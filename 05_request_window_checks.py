#!/usr/bin/env python3
"""Follow-up checks on the request file: when does the usable data actually start, are
tweetIds clean, and how many posts are 'at risk' for an event study?
Writes request_window_checks.md (counts only, no text).

Usage: python 05_request_window_checks.py --parquet data/parquet --out request_window_checks.md
Needs requests.parquet and notes.parquet.
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
    ap.add_argument("--out", default="request_window_checks.md")
    a = ap.parse_args()
    con = duckdb.connect()
    P = lambda n: os.path.join(a.parquet, n + ".parquet")
    con.execute(f"CREATE VIEW r AS SELECT * FROM read_parquet('{P('requests')}')")
    con.execute(f"CREATE VIEW notes AS SELECT * FROM read_parquet('{P('notes')}')")
    E = "noteRequestFeedEligibleAtMillis"
    SNOW = "((TRY_CAST(tweetId AS BIGINT) >> 22) + 1288834974657)"
    con.execute("""CREATE VIEW fn AS SELECT tweetId, min(TRY_CAST(createdAtMillis AS BIGINT)) AS first_note, count(*) AS n_notes
                   FROM notes GROUP BY 1""")
    L = ["# Request window checks", ""]

    # A. notes per month
    rows = con.execute("""SELECT strftime(epoch_ms(TRY_CAST(createdAtMillis AS BIGINT)), '%Y-%m') m, count(*)
                          FROM notes WHERE TRY_CAST(createdAtMillis AS BIGINT) >= 1735689600000 GROUP BY 1 ORDER BY 1""").fetchall()
    L += ["## A. Notes created per month (notes table, 2025 onward). A jump in Aug 2026 would suggest a platform change", md_table(["month", "notes"], rows), ""]

    # B. request-file posts by decoded creation month
    rows = con.execute(f"""SELECT CASE WHEN {SNOW} < 1735689600000 THEN 'before 2025' ELSE strftime(epoch_ms({SNOW}), '%Y-%m') END m, count(*)
                           FROM r WHERE TRY_CAST(tweetId AS BIGINT) > 0 GROUP BY 1 ORDER BY 1""").fetchall()
    L += ["## B. Request-file posts by decoded post-creation month (tests whether the file is a rolling window of recent posts)", md_table(["post month", "posts"], rows), ""]

    # C. in-app feed: share noted, by eligibility month
    rows = con.execute(f"""
      SELECT strftime(epoch_ms(TRY_CAST(r.{E} AS BIGINT)), '%Y-%m') m, count(*),
             count(fn.tweetId) FILTER (WHERE true),
             count(*) FILTER (WHERE fn.first_note < TRY_CAST(r.{E} AS BIGINT))
      FROM r LEFT JOIN fn USING(tweetId) WHERE TRY_CAST(r.{E} AS BIGINT) > 0 GROUP BY 1 ORDER BY 1""").fetchall()
    L += ["## C. In-app feed eligible posts by eligibility month: how many have any note, and how many had a note BEFORE eligibility",
          md_table(["eligibility month", "posts", "with >= 1 note", "note before eligibility"], rows), ""]

    # D. tweetId quality
    rows = []
    for name, tbl in (("request file", "r"), ("notes", "notes")):
        t, bad_cast, nonpos, old = con.execute(f"""
          SELECT count(*), count(*) FILTER (WHERE TRY_CAST(tweetId AS BIGINT) IS NULL),
                 count(*) FILTER (WHERE TRY_CAST(tweetId AS BIGINT) <= 0),
                 count(*) FILTER (WHERE TRY_CAST(tweetId AS BIGINT) > 0 AND {SNOW} < 1420070400000)
          FROM {tbl}""").fetchone()
        rows.append((name, t, bad_cast, nonpos, old))
    L += ["## D. tweetId quality (decoded creation before 2015 means pre-snowflake or invalid ID; the decode formula does not apply to them)",
          md_table(["table", "rows", "not numeric", "<= 0", "decoded before 2015"], rows), ""]

    # E. at-risk counts for an event study (in-app feed)
    rows = con.execute(f"""
      WITH j AS (SELECT TRY_CAST(r.{E} AS BIGINT) AS e, fn.first_note AS f
                 FROM r LEFT JOIN fn USING(tweetId) WHERE TRY_CAST(r.{E} AS BIGINT) > 0)
      SELECT CASE WHEN e >= 1785542400000 THEN 'eligible Aug 2026 or later' ELSE 'eligible before Aug 2026' END grp,
             count(*),
             count(*) FILTER (WHERE f < e) AS noted_before,
             count(*) FILTER (WHERE f IS NULL OR f >= e) AS at_risk,
             count(*) FILTER (WHERE f >= e) AS at_risk_noted_later,
             count(*) FILTER (WHERE f IS NULL) AS at_risk_never_noted
      FROM j GROUP BY 1 ORDER BY 1""").fetchall()
    L += ["## E. Event-study sample: posts with valid in-app eligibility",
          md_table(["group", "posts", "note before eligibility", "at risk at eligibility", "of those, noted later", "of those, no note in notes table"], rows),
          "", "(Posts with no note may have had notes that were later deleted; deleted notes are not in the notes table.)", ""]
    open(a.out, "w").write("\n".join(L))
    print("wrote", a.out)

if __name__ == "__main__":
    main()