#!/usr/bin/env python3
"""RQ1 sample recount and first descriptive numbers (decisions W1-9, W1-10). Counts only, no text.

Usage: python 12_rq1_sample.py --parquet data/parquet --out data/derived/rq1_sample.md
Needs requests.parquet, notes.parquet, userEnrollment.parquet.

Definitions
  t0      = first eligibility time of a post = the earliest valid (> 0) of the four eligibility columns (about the XL time = first request)
  sample  = posts with t0 from 2026-08-13 00:00 UTC to 2026-10-12 23:59 UTC
  level   = highest feed reached: 'Small / in-app' (Small or in-app time valid), else 'Large', else 'XL only'
  first note = earliest note in the notes table for the post (deleted notes are not in that table)
RQ1a: among posts with no note before t0, share with a first note within 6, 24, 72 hours of t0, by level.
RQ1b: among in-app-eligible posts with no note before the in-app time, same shares, and AI vs. other first notes.
"""
import argparse, os
import duckdb

def md_table(cols, rows):
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join("" if v is None else (f"{v:,}" if isinstance(v, int) else str(v)) for v in r) + " |")
    return "\n".join(out)

H = 3600000
START, END = 1786579200000, 1791849600000   # 2026-08-13 00:00 UTC, 2026-10-13 00:00 UTC (exclusive)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", default="data/parquet")
    ap.add_argument("--out", default="data/derived/rq1_sample.md")
    ap.add_argument("--memory-limit", default="3GB")
    ap.add_argument("--threads", type=int, default=2)
    a = ap.parse_args()
    con = duckdb.connect()
    con.execute(f"SET memory_limit='{a.memory_limit}'"); con.execute(f"SET threads={a.threads}")
    P = lambda n: os.path.join(a.parquet, n)
    con.execute(f"""CREATE TABLE posts AS
      WITH r AS (SELECT tweetId,
          NULLIF(GREATEST(TRY_CAST(apiXlFeedEligibleAtMillis AS BIGINT), 0), 0) AS xl,
          NULLIF(GREATEST(TRY_CAST(apiLargeFeedEligibleAtMillis AS BIGINT), 0), 0) AS lg,
          NULLIF(GREATEST(TRY_CAST(apiSmallFeedEligibleAtMillis AS BIGINT), 0), 0) AS sm,
          NULLIF(GREATEST(TRY_CAST(noteRequestFeedEligibleAtMillis AS BIGINT), 0), 0) AS ia
        FROM read_parquet('{P('requests.parquet')}'))
      SELECT tweetId, xl, lg, sm, ia, LEAST(xl, lg, sm, ia) AS t0,
             CASE WHEN ia IS NOT NULL OR sm IS NOT NULL THEN 'Small / in-app' WHEN lg IS NOT NULL THEN 'Large' ELSE 'XL only' END AS level
      FROM r WHERE LEAST(xl, lg, sm, ia) >= {START} AND LEAST(xl, lg, sm, ia) < {END}""")
    con.execute(f"""CREATE TABLE fn AS
      SELECT n.tweetId, min(TRY_CAST(n.createdAtMillis AS BIGINT)) AS first_note,
             arg_min(n.noteAuthorParticipantId, TRY_CAST(n.createdAtMillis AS BIGINT)) AS first_author
      FROM read_parquet('{P('notes.parquet')}') n GROUP BY 1""")
    con.execute(f"""CREATE TABLE ue AS SELECT participantId, enrollmentState FROM read_parquet('{P('userEnrollment.parquet')}')""")
    con.execute("""CREATE TABLE s AS
      SELECT p.*, fn.first_note, (ue.enrollmentState = 'apiEarnedIn') AS first_is_ai
      FROM posts p LEFT JOIN fn USING (tweetId) LEFT JOIN ue ON fn.first_author = ue.participantId""")

    L = ["# RQ1 sample", "", "Window: first eligible 2026-08-13 to 2026-10-12. Counts only.", ""]
    r = con.execute("""SELECT level, count(*), count(*) FILTER (WHERE first_note IS NOT NULL) FROM s GROUP BY 1
                       ORDER BY CASE level WHEN 'XL only' THEN 1 WHEN 'Large' THEN 2 ELSE 3 END""").fetchall()
    tot = (sum(x[1] for x in r), sum(x[2] for x in r))
    r = [(a_, b, c, f"{100*c/b:.1f}%") for a_, b, c in r] + [("All", tot[0], tot[1], f"{100*tot[1]/max(tot[0],1):.1f}%")]
    L += ["## A. Sample by highest feed reached", md_table(["level", "posts", "with any note", "%"], r), ""]

    def rq(label, tcol, where_level):
        rows = con.execute(f"""
          WITH g AS (SELECT level, {tcol} AS t, first_note, first_is_ai FROM s WHERE {where_level})
          SELECT level, count(*) AS posts,
                 count(*) FILTER (WHERE first_note < t) AS noted_before,
                 count(*) FILTER (WHERE first_note IS NULL OR first_note >= t) AS at_risk,
                 count(*) FILTER (WHERE first_note >= t AND first_note < t + 6*{H}) AS w6,
                 count(*) FILTER (WHERE first_note >= t AND first_note < t + 24*{H}) AS w24,
                 count(*) FILTER (WHERE first_note >= t AND first_note < t + 72*{H}) AS w72,
                 round(quantile_cont((first_note - t)/{H}.0, 0.5) FILTER (WHERE first_note >= t), 1) AS median_hours,
                 count(*) FILTER (WHERE first_note >= t AND first_note < t + 24*{H} AND first_is_ai) AS w24_ai
          FROM g GROUP BY 1 ORDER BY CASE level WHEN 'XL only' THEN 1 WHEN 'Large' THEN 2 ELSE 3 END""").fetchall()
        out = []
        for lv, posts, nb, ar, w6, w24, w72, med, ai in rows:
            pc = lambda x: f"{100*x/ar:.1f}%" if ar else ""
            out.append((lv, posts, nb, ar, pc(w6), pc(w24), pc(w72), med, f"{100*ai/w24:.1f}%" if w24 else ""))
        return ["## " + label,
                md_table(["level", "posts", "noted before t", "at risk at t", "first note within 6h", "within 24h", "within 72h", "median hours (noted)", "AI share of 24h first notes"], out), ""]

    L += rq("B. RQ1a: clock t = first eligibility (about the first request), all levels", "t0", "true")
    L += rq("C. RQ1b: clock t = in-app eligibility, in-app group only", "COALESCE(ia, sm)", "(ia IS NOT NULL OR sm IS NOT NULL)")
    open(a.out, "w").write("\n".join(L))
    print("wrote", a.out)

if __name__ == "__main__":
    main()