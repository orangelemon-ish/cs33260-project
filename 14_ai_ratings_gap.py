#!/usr/bin/env python3
"""Why do AI notes get fewer ratings than human notes? Descriptive checks with the data we have. Counts only.

Usage: python 14_ai_ratings_gap.py --derived data/derived --parquet data/parquet --out data/derived/ai_ratings_gap.md
Needs fates.parquet, notes.parquet, requests.parquet, the ratings folder; statsmodels for the regression (skipped if missing).

Population: main population (in notes table, misleading class) created 2026-05-01 to 2026-09-06, after the AI surge.
We do NOT have post views, followers or engagement, so we test what we can observe:
  - how early the note comes after the post (latency, from the tweetId)
  - competition: first note on the post vs. a later note, and notes per post
  - media notes
  - how ratings arrive: speed, and the share that come from notification-driven (population-sampled) ratings
  - the post's request signal (highest feed reached), for notes created 2026-08-13 to 09-06
A Poisson regression then shows how much of the AI gap these observed factors explain.
"""
import argparse, math, os
import duckdb

def md_table(cols, rows):
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join("" if v is None else (f"{v:,}" if isinstance(v, int) else str(v)) for v in r) + " |")
    return "\n".join(out)

H = 3600000
START, END, LV_START = 1777593600000, 1788739200000, 1786579200000
MISLEADING = "MISINFORMED_OR_POTENTIALLY_MISLEADING"
BUCKETS = ("CASE WHEN latency_h < 0.25 THEN '1: under 15 min' WHEN latency_h < 1 THEN '2: 15-60 min' "
           "WHEN latency_h < 6 THEN '3: 1-6 h' WHEN latency_h < 24 THEN '4: 6-24 h' ELSE '5: over 24 h' END")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--derived", default="data/derived")
    ap.add_argument("--parquet", default="data/parquet")
    ap.add_argument("--out", default="data/derived/ai_ratings_gap.md")
    ap.add_argument("--memory-limit", default="3GB")
    ap.add_argument("--threads", type=int, default=2)
    a = ap.parse_args()
    con = duckdb.connect()
    con.execute(f"SET memory_limit='{a.memory_limit}'"); con.execute(f"SET threads={a.threads}")
    con.execute("SET preserve_insertion_order=false")
    F = os.path.join(a.derived, "fates.parquet")
    P = lambda n: os.path.join(a.parquet, n)

    con.execute(f"""CREATE TABLE nn AS
      SELECT noteId, tweetId, COALESCE(TRY_CAST(isMediaNote AS INTEGER), 0) AS media,
             row_number() OVER (PARTITION BY tweetId ORDER BY TRY_CAST(createdAtMillis AS BIGINT), noteId) AS rnk,
             count(*) OVER (PARTITION BY tweetId) AS n_on_post
      FROM read_parquet('{P('notes.parquet')}')""")
    con.execute(f"""CREATE TABLE w AS
      SELECT f.noteId, f.author_type, f.created, f.n_upto_lock, f.lock_ms, nn.tweetId, nn.media, nn.rnk, nn.n_on_post,
             (f.created - ((TRY_CAST(nn.tweetId AS BIGINT) >> 22) + 1288834974657)) / {H}.0 AS latency_h
      FROM read_parquet('{F}') f JOIN nn USING (noteId)
      WHERE NOT f.deleted_like AND f.classification = '{MISLEADING}' AND f.created >= {START} AND f.created < {END}
        AND TRY_CAST(nn.tweetId AS BIGINT) > 0
        AND ((TRY_CAST(nn.tweetId AS BIGINT) >> 22) + 1288834974657) >= 1420070400000""")
    con.execute("DELETE FROM w WHERE latency_h < 0")
    print("scanning ratings (a few minutes)...", flush=True)
    con.execute(f"""CREATE TABLE rr AS
      SELECT w.noteId, (min(r.rt) - any_value(w.created)) / {H}.0 AS first_h,
             count(*) FILTER (WHERE (w.lock_ms IS NULL OR r.rt <= w.lock_ms) AND r.rt <= w.created + 24*{H}) AS n_24h,
             count(*) FILTER (WHERE (w.lock_ms IS NULL OR r.rt <= w.lock_ms) AND r.src = 'POPULATION_SAMPLED') AS n_pop
      FROM (SELECT noteId, TRY_CAST(createdAtMillis AS BIGINT) AS rt, ratingSourceBucketed AS src
            FROM read_parquet('{P('ratings')}/*.parquet', union_by_name=true)) r
      JOIN w USING (noteId) GROUP BY w.noteId""")
    con.execute(f"""CREATE TABLE req AS
      WITH q AS (SELECT tweetId, TRY_CAST(apiXlFeedEligibleAtMillis AS BIGINT) AS xl, TRY_CAST(apiLargeFeedEligibleAtMillis AS BIGINT) AS lg,
                        TRY_CAST(apiSmallFeedEligibleAtMillis AS BIGINT) AS sm, TRY_CAST(noteRequestFeedEligibleAtMillis AS BIGINT) AS ia
                 FROM read_parquet('{P('requests.parquet')}'))
      SELECT tweetId, CASE WHEN ia > 0 OR sm > 0 THEN 'Small / in-app' WHEN lg > 0 THEN 'Large' ELSE 'XL only' END AS level FROM q""")
    con.execute(f"""CREATE TABLE d AS
      SELECT w.*, {BUCKETS} AS bucket, COALESCE(rr.n_24h, 0) AS n_24h, COALESCE(rr.n_pop, 0) AS n_pop, rr.first_h,
             COALESCE(req.level, 'no request in file') AS level
      FROM w LEFT JOIN rr USING (noteId) LEFT JOIN req USING (tweetId)""")

    L = ["# Why do AI notes get fewer ratings?", "",
         "Main population created 2026-05-01 to 2026-09-06. 'Ratings' = ratings up to lock time. 'AI' = apiEarnedIn author. Counts only.", ""]
    stat = ("count(*) AS notes, round(avg(n_upto_lock), 1) AS mean_ratings, round(median(n_upto_lock), 0) AS median_ratings, "
            "round(100.0*count(*) FILTER (WHERE n_upto_lock < 5)/count(*), 1) AS under5, "
            "round(100.0*count(*) FILTER (WHERE n_upto_lock >= 10)/count(*), 1) AS ten_plus")
    sh = ["notes", "mean ratings", "median ratings", "% under 5", "% 10 or more"]
    r = con.execute(f"SELECT author_type, {stat} FROM d GROUP BY 1 ORDER BY 1").fetchall()
    L += ["## 1. The gap", md_table(["author"] + sh, r), ""]
    r = con.execute(f"SELECT bucket, author_type, {stat} FROM d GROUP BY 1, 2 ORDER BY 1, 2").fetchall()
    L += ["## 2. By how early the note comes after the post", md_table(["latency", "author"] + sh, r), ""]
    r = con.execute(f"SELECT CASE WHEN rnk = 1 THEN 'first note on post' ELSE 'later note' END AS pos, author_type, {stat} FROM d GROUP BY 1, 2 ORDER BY 1, 2").fetchall()
    L += ["## 3. First note on the post vs. a later note", md_table(["position", "author"] + sh, r), ""]
    r = con.execute(f"SELECT CASE WHEN media = 1 THEN 'media note' ELSE 'regular note' END, author_type, {stat} FROM d GROUP BY 1, 2 ORDER BY 1, 2").fetchall()
    L += ["## 4. Media notes", md_table(["type", "author"] + sh, r), ""]
    r = con.execute(f"""SELECT author_type, round(median(first_h), 2) AS med_first_h,
          round(100.0*sum(n_24h)/nullif(sum(n_upto_lock), 0), 1) AS pct_in_24h,
          round(100.0*sum(n_pop)/nullif(sum(n_upto_lock), 0), 1) AS pct_population_sampled,
          round(avg(n_pop), 2) AS mean_pop_ratings_per_note
          FROM d GROUP BY 1 ORDER BY 1""").fetchall()
    L += ["## 5. How ratings arrive", md_table(["author", "median hours to first rating", "% of ratings within 24h", "% from population-sampled (notification) ratings", "mean population-sampled ratings per note"], r), ""]
    r = con.execute(f"""SELECT level, author_type, {stat} FROM d WHERE created >= {LV_START} GROUP BY 1, 2
                        ORDER BY CASE level WHEN 'no request in file' THEN 0 WHEN 'XL only' THEN 1 WHEN 'Large' THEN 2 ELSE 3 END, 2""").fetchall()
    L += ["## 6. By the post's request signal (notes created 2026-08-13 to 09-06; highest feed the post reached)", md_table(["level", "author"] + sh, r), ""]
    r = con.execute(f"""SELECT level, round(100.0*count(*) FILTER (WHERE author_type = 'AI')/count(*), 1) AS ai_share, count(*)
                        FROM d WHERE created >= {LV_START} GROUP BY 1 ORDER BY 1""").fetchall()
    L += ["## 7. AI share of notes by request signal (same notes)", md_table(["level", "AI share of notes %", "notes"], r), ""]

    try:
        import numpy as np, statsmodels.api as sm
        rows = con.execute("""SELECT n_upto_lock, (author_type = 'AI')::INT, bucket, (rnk = 1)::INT, (n_on_post > 1)::INT, media,
                                     strftime(epoch_ms(created), '%Y-%m') FROM d""").fetchall()
        y = np.array([r[0] for r in rows], dtype=float)
        def design(use):
            cols = [np.ones(len(rows)), np.array([r[1] for r in rows], dtype=float)]
            names = ["const", "AI"]
            if "lat" in use:
                for b in sorted({r[2] for r in rows})[1:]:
                    cols.append(np.array([1.0 if r[2] == b else 0.0 for r in rows])); names.append("latency " + b)
            if "oth" in use:
                for nm, k in (("first note", 3), ("other notes on post", 4), ("media note", 5)):
                    cols.append(np.array([r[k] for r in rows], dtype=float)); names.append(nm)
                for mth in sorted({r[6] for r in rows})[1:]:
                    cols.append(np.array([1.0 if r[6] == mth else 0.0 for r in rows])); names.append("month " + mth)
            keep = [0] + [k for k in range(1, len(cols)) if cols[k].std() > 0]   # drop constant columns (would make the matrix singular)
            return np.column_stack([cols[k] for k in keep]), [names[k] for k in keep]
        out = []
        for label, use in (("AI only (unadjusted)", set()), ("+ latency", {"lat"}), ("+ latency, first note, other notes, media, month", {"lat", "oth"})):
            try:
                X, names = design(use)
                fit = sm.GLM(y, X, family=sm.families.Poisson()).fit(cov_type="HC1")
                b, se = fit.params[1], fit.bse[1]
                out.append((label, f"{math.exp(b):.2f}", f"{math.exp(b-1.96*se):.2f} to {math.exp(b+1.96*se):.2f}"))
            except Exception as e:   # keep the rest of the report if one model fails
                out.append((label, "failed", str(e)[:60]))
        L += ["## 8. Poisson regression: ratings per note, AI vs. other (rate ratio; 1.00 = no gap)",
              md_table(["model", "AI rate ratio", "95% CI"], out), "",
              "A ratio of 0.60 means AI notes get 40% fewer ratings. If it moves toward 1.00 as factors are added, those factors explain part of the gap. Unobserved post visibility (views, followers) is not in the data."]
    except ImportError:
        L += ["## 8. Regression skipped (statsmodels not installed)", ""]
    open(a.out, "w").write("\n".join(L))
    print("wrote", a.out)

if __name__ == "__main__":
    main()