#!/usr/bin/env python3
"""Checks on the note-request file (post-level feed-eligibility table).
Writes requests_checks.md (counts only, no text).

Usage: python 04_requests_checks.py --parquet data/parquet --out requests_checks.md
Needs requests.parquet and notes.parquet (not ratings).
"""
import argparse, os
import duckdb

def md_table(cols, rows):
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join("" if v is None else (f"{v:,}" if isinstance(v, int) else str(v)) for v in r) + " |")
    return "\n".join(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", default="data/parquet")
    ap.add_argument("--out", default="requests_checks.md")
    a = ap.parse_args()
    con = duckdb.connect()
    P = lambda n: os.path.join(a.parquet, n + ".parquet")
    con.execute(f"CREATE VIEW r AS SELECT * FROM read_parquet('{P('requests')}')")
    con.execute(f"CREATE VIEW notes AS SELECT * FROM read_parquet('{P('notes')}')")
    cols = [c[0] for c in con.execute("DESCRIBE SELECT * FROM r").fetchall()]
    elig = [c for c in cols if c.endswith("EligibleAtMillis")]
    L = ["# Request file checks", "", f"Columns: {', '.join(cols)}", ""]

    # 1. valid vs sentinel
    rows = []
    for c in elig:
        t, bad, good, lo, hi = con.execute(f"""
          SELECT count(*), count(*) FILTER (WHERE TRY_CAST("{c}" AS BIGINT) <= 0),
                 count(*) FILTER (WHERE TRY_CAST("{c}" AS BIGINT) > 0),
                 CAST(epoch_ms(min(TRY_CAST("{c}" AS BIGINT)) FILTER (WHERE TRY_CAST("{c}" AS BIGINT) > 0)) AS VARCHAR),
                 CAST(epoch_ms(max(TRY_CAST("{c}" AS BIGINT)) FILTER (WHERE TRY_CAST("{c}" AS BIGINT) > 0)) AS VARCHAR)
          FROM r""").fetchone()
        rows.append((c, t, bad, good, lo, hi))
    L += ["## 1. Eligibility timestamps: rows with value <= 0 (missing) vs valid, and valid date range",
          md_table(["column", "rows", "<= 0", "valid", "earliest valid", "latest valid"], rows), ""]

    # 2. monthly counts for each eligibility column
    for c in elig:
        m = con.execute(f"""SELECT strftime(epoch_ms(TRY_CAST("{c}" AS BIGINT)), '%Y-%m'), count(*)
                            FROM r WHERE TRY_CAST("{c}" AS BIGINT) > 0 GROUP BY 1 ORDER BY 1""").fetchall()
        L += [f"## 2. Posts per month by `{c}`", md_table(["month", "posts"], m), ""]

    # 3. overlap with notes
    con.execute("""CREATE VIEW fn AS SELECT tweetId, min(TRY_CAST(createdAtMillis AS BIGINT)) AS first_note, count(*) AS n_notes
                   FROM notes GROUP BY 1""")
    L += ["## 3. Overlap with notes (by tweetId)",
          md_table(["request-file posts", "of those with >= 1 note", "posts with notes (all)", "of those in request file"],
                   con.execute("""SELECT (SELECT count(*) FROM r),
                                         (SELECT count(*) FROM r JOIN fn USING(tweetId)),
                                         (SELECT count(*) FROM fn),
                                         (SELECT count(*) FROM fn JOIN r USING(tweetId))""").fetchall()), ""]

    # 4. timing of first note relative to eligibility
    for c in elig:
        res = con.execute(f"""
          WITH j AS (SELECT TRY_CAST(r."{c}" AS BIGINT) AS e, fn.first_note AS f
                     FROM r JOIN fn USING(tweetId) WHERE TRY_CAST(r."{c}" AS BIGINT) > 0)
          SELECT count(*),
                 count(*) FILTER (WHERE f < e),
                 round(quantile_cont((f-e)/86400000.0, 0.1),2), round(quantile_cont((f-e)/86400000.0, 0.25),2),
                 round(quantile_cont((f-e)/86400000.0, 0.5),2), round(quantile_cont((f-e)/86400000.0, 0.75),2),
                 round(quantile_cont((f-e)/86400000.0, 0.9),2)
          FROM j""").fetchall()
        L += [f"## 4. Days from `{c}` to first note (negative = note came first)",
              md_table(["posts with valid time and a note", "first note BEFORE eligibility", "p10", "p25", "p50", "p75", "p90"], res), ""]

    # 5. non-empty text columns (counts only)
    txt = [c for c in cols if c not in elig and c != "tweetId"]
    rows = [(c, con.execute(f"""SELECT count(*) FILTER (WHERE "{c}" IS NOT NULL AND "{c}" <> '') FROM r""").fetchone()[0]) for c in txt]
    L += ["## 5. Non-empty counts in other columns", md_table(["column", "non-empty rows"], rows), ""]

    # 6-9. Post creation time decoded from tweetId (snowflake ID: ms since 2010-11-04 01:42:54.657 UTC, shifted left 22 bits)
    SNOW = "((CAST(tweetId AS BIGINT) >> 22) + 1288834974657)"
    lo, hi = con.execute(f"SELECT CAST(epoch_ms(min({SNOW})) AS VARCHAR), CAST(epoch_ms(max({SNOW})) AS VARCHAR) FROM r").fetchone()
    lo2, hi2 = con.execute(f"SELECT CAST(epoch_ms(min({SNOW})) AS VARCHAR), CAST(epoch_ms(max({SNOW})) AS VARCHAR) FROM fn").fetchone()
    L += ["## 6. Post creation time decoded from tweetId (sanity check; validate by hand on a few posts, see decisions W1-23)",
          md_table(["table", "earliest decoded", "latest decoded"], [("request file", lo, hi), ("posts with notes", lo2, hi2)]), ""]
    c = "noteRequestFeedEligibleAtMillis"
    if c in cols:
        H = f"((TRY_CAST({c} AS BIGINT) - {SNOW}) / 3600000.0)"
        row = con.execute(f"""SELECT count(*), round(quantile_cont({H},0.01),2), round(quantile_cont({H},0.1),2),
                                     round(quantile_cont({H},0.5),2), round(quantile_cont({H},0.9),2), round(quantile_cont({H},0.99),2),
                                     round(100.0*count(*) FILTER (WHERE {H} > 24)/count(*),1),
                                     round(100.0*count(*) FILTER (WHERE {H} > 48)/count(*),1),
                                     round(100.0*count(*) FILTER (WHERE {H} > 168)/count(*),1)
                              FROM r WHERE TRY_CAST({c} AS BIGINT) > 0""").fetchall()
        L += [f"## 7. Hours from post creation to `{c}` (docs say eligibility may be capped within N hours of post creation; a hard cap would show up here)",
              md_table(["posts", "p1", "p10", "p50", "p90", "p99", "% > 24h", "% > 48h", "% > 168h"], row), ""]
        G = f"((fn.first_note - {SNOW}) / 3600000.0)"
        row = con.execute(f"""SELECT count(*), round(quantile_cont({G},0.1),2), round(quantile_cont({G},0.5),2), round(quantile_cont({G},0.9),2)
                              FROM fn JOIN r USING(tweetId) WHERE TRY_CAST(r.{c} AS BIGINT) > 0""").fetchall()
        row_all = con.execute(f"""SELECT count(*), round(quantile_cont({G},0.1),2), round(quantile_cont({G},0.5),2), round(quantile_cont({G},0.9),2)
                                  FROM fn""").fetchall()
        L += ["## 8. Hours from post creation to first note",
              md_table(["group", "posts", "p10", "p50", "p90"],
                       [("in request feed (valid eligibility)",) + row[0], ("all posts with notes",) + row_all[0]]), ""]
        row = con.execute(f"""
          WITH j AS (SELECT (fn.first_note - TRY_CAST(r.{c} AS BIGINT)) / 3600000.0 AS d
                     FROM fn JOIN r USING(tweetId) WHERE TRY_CAST(r.{c} AS BIGINT) > 0)
          SELECT count(*), count(*) FILTER (WHERE d < 0), count(*) FILTER (WHERE d >= 0 AND d < 6),
                 count(*) FILTER (WHERE d >= 6 AND d < 24), count(*) FILTER (WHERE d >= 24 AND d < 72),
                 count(*) FILTER (WHERE d >= 72) FROM j""").fetchall()
        L += ["## 9. First note relative to feed eligibility (posts with a note)",
              md_table(["posts", "before eligibility", "0-6h after", "6-24h after", "24-72h after", ">72h after"], row), ""]
    open(a.out, "w").write("\n".join(L))
    print("wrote", a.out)

if __name__ == "__main__":
    main()