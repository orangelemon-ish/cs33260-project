#!/usr/bin/env python3
"""Ratings checks (W1-10, W1-25, W1-28, W1-17 preview). Counts only, no text. Writes ratings_checks.md.

Heavy joins run on a deterministic 1% sample of NOTES (all ratings of the sampled notes), so they are
fast and memory-safe. Sections G, H, I scan the full ratings table but read only a few columns.

Usage: python 08_ratings_checks.py --parquet data/parquet --out ratings_checks.md
       (--memory-limit 3GB --threads 2 by default; --sample-mod 100 means 1% of notes)
Needs ratings/ (folder of parts) and noteStatusHistory.parquet; notes.parquet is used for section I.
"""
import argparse, os
import duckdb

def md_table(cols, rows):
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join("" if v is None else (f"{v:,}" if isinstance(v, int) else str(v)) for v in r) + " |")
    return "\n".join(out)

HOUR = 3600000.0
WIN_START = 1734048000000   # 2024-12-13 00:00 UTC (W1-33)
WIN_END   = 1788739200000   # 2026-09-07 00:00 UTC, exclusive (W1-30)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", default="data/parquet")
    ap.add_argument("--out", default="ratings_checks.md")
    ap.add_argument("--memory-limit", default="3GB")
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--sample-mod", type=int, default=100)
    a = ap.parse_args()
    con = duckdb.connect()
    con.execute(f"SET memory_limit='{a.memory_limit}'")
    con.execute(f"SET threads={a.threads}")
    con.execute("SET preserve_insertion_order=false")
    con.execute(f"SET temp_directory='{os.path.join(a.parquet, '.checks_tmp')}'")
    P = lambda n: os.path.join(a.parquet, n)
    con.execute(f"CREATE VIEW r AS SELECT * FROM read_parquet('{P('ratings')}/*.parquet', union_by_name=true)")
    con.execute(f"CREATE VIEW sh AS SELECT * FROM read_parquet('{P('noteStatusHistory.parquet')}')")
    M = a.sample_mod
    con.execute(f"""CREATE TABLE rs AS SELECT noteId, raterParticipantId, TRY_CAST(createdAtMillis AS BIGINT) AS rt
                    FROM r WHERE hash(noteId) % {M} = 0""")
    con.execute(f"""CREATE TABLE shs AS SELECT noteId, TRY_CAST(createdAtMillis AS BIGINT) AS created,
        NULLIF(GREATEST(TRY_CAST(timestampMillisOfStatusLock AS BIGINT),0),0) AS lock_ts,
        NULLIF(GREATEST(TRY_CAST(timestampMillisOfFirstNonNMRStatus AS BIGINT),0),0) AS first_ts,
        firstNonNMRStatus, currentStatus, lockedStatus
        FROM sh WHERE hash(noteId) % {M} = 0""")
    L = ["# Ratings checks", "", f"Sample: notes with hash(noteId) % {M} = 0 (all their ratings). Full-table sections are marked.", ""]

    r = con.execute("""SELECT (SELECT count(*) FROM rs), (SELECT count(DISTINCT noteId) FROM rs), (SELECT count(*) FROM shs)""").fetchall()
    L += ["## A. Sample size", md_table(["ratings", "notes with ratings", "notes in status history"], r), ""]

    r = con.execute("""SELECT count(*), count(*) - count(DISTINCT (noteId, raterParticipantId)) FROM rs""").fetchall()
    L += ["## B. Duplicate (noteId, rater) pairs in the sample (W1-10)", md_table(["ratings", "extra rows from duplicate pairs"], r), ""]

    r = con.execute(f"""SELECT count(*), count(*) FILTER (WHERE rs.rt < shs.created),
          round(quantile_cont((rs.rt - shs.created)/{HOUR}, 0.01),2), round(quantile_cont((rs.rt - shs.created)/{HOUR}, 0.5),2),
          round(quantile_cont((rs.rt - shs.created)/{HOUR}, 0.99),2),
          round(100.0*count(*) FILTER (WHERE (rs.rt - shs.created)/{HOUR} > 48)/count(*),1)
          FROM rs JOIN shs USING(noteId)""").fetchall()
    L += ["## C. Rating time vs. note creation time (W1-25: is `createdAtMillis` in ratings the RATING time? expect about 0 ratings before the note)",
          md_table(["ratings joined", "rating BEFORE note creation", "p1 (hours after note)", "p50", "p99", "% later than 48h"], r), ""]

    r = con.execute("""SELECT count(*), count(*) FILTER (WHERE rs.rt > shs.lock_ts), round(100.0*count(*) FILTER (WHERE rs.rt > shs.lock_ts)/count(*),2)
                       FROM rs JOIN shs USING(noteId) WHERE shs.lock_ts IS NOT NULL""").fetchall()
    L += ["## D. Ratings made AFTER the note's lock time (notes with a lock)", md_table(["ratings on locked notes", "after lock", "%"], r), ""]

    # E. ratings up to lock per note in the main window, by final status
    r = con.execute(f"""
      WITH cnt AS (SELECT shs.noteId, shs.created, coalesce(shs.lockedStatus, shs.currentStatus) AS final,
                          count(rs.rt) FILTER (WHERE shs.lock_ts IS NULL OR rs.rt <= shs.lock_ts) AS n
                   FROM shs LEFT JOIN rs USING(noteId)
                   WHERE shs.created >= {WIN_START} AND shs.created < {WIN_END} GROUP BY 1,2,3)
      SELECT final, CASE WHEN n = 0 THEN '0' WHEN n < 5 THEN '1-4' WHEN n < 10 THEN '5-9' ELSE '10+' END AS bucket, count(*)
      FROM cnt GROUP BY 1,2 ORDER BY 1,2""").fetchall()
    L += ["## E. Main window (created 2024-12-13 to 2026-09-06): ratings received up to lock time, by final status (sample). NMR with 5+ ratings = Unresolved candidates; NMR with fewer = Under-rated (W1-17, W1-28)",
          md_table(["final status", "ratings up to lock", "notes"], r), ""]

    r = con.execute("""
      WITH cnt AS (SELECT shs.noteId, count(rs.rt) FILTER (WHERE rs.rt <= shs.first_ts) AS n
                   FROM shs LEFT JOIN rs USING(noteId) WHERE shs.first_ts IS NOT NULL GROUP BY 1)
      SELECT count(*), count(*) FILTER (WHERE n < 5), round(100.0*count(*) FILTER (WHERE n < 5)/count(*),2) FROM cnt""").fetchall()
    L += ["## F. Validation of the threshold: notes that ever left Needs More Ratings, with fewer than 5 ratings made by that time (expect near 0%; if not, our counting rule needs revisiting)",
          md_table(["notes that got a first status", "with < 5 ratings by then", "%"], r), ""]

    # Full-table sections
    r = con.execute("""SELECT strftime(epoch_ms(TRY_CAST(createdAtMillis AS BIGINT)), '%Y-%m') m, count(*),
                       count(*) FILTER (WHERE ratingSourceBucketed = 'POPULATION_SAMPLED'),
                       round(100.0*count(*) FILTER (WHERE ratingSourceBucketed = 'POPULATION_SAMPLED')/count(*),2)
                       FROM r WHERE TRY_CAST(createdAtMillis AS BIGINT) >= 1756684800000 GROUP BY 1 ORDER BY 1""").fetchall()
    L += ["## G. FULL TABLE: ratings per month from 2025-09 and the population-sampled share (W1-25)",
          md_table(["month", "ratings", "population-sampled", "%"], r), ""]

    r = con.execute("""SELECT CAST(year(epoch_ms(TRY_CAST(createdAtMillis AS BIGINT))) AS VARCHAR), count(*),
                       count(*) FILTER (WHERE helpfulnessLevel IS NULL) FROM r GROUP BY 1 ORDER BY 1""").fetchall()
    L += ["## H. FULL TABLE: ratings per year and how many have no `helpfulnessLevel` (older ratings used the deprecated binary flags)",
          md_table(["year", "ratings", "no helpfulnessLevel"], r), ""]

    con.execute("CREATE TABLE rated AS SELECT DISTINCT noteId FROM r")
    r = con.execute("""SELECT CAST(year(epoch_ms(TRY_CAST(sh.createdAtMillis AS BIGINT))) AS VARCHAR) y, count(*),
                       count(*) FILTER (WHERE rated.noteId IS NULL),
                       round(100.0*count(*) FILTER (WHERE rated.noteId IS NULL)/count(*),2)
                       FROM sh LEFT JOIN rated USING(noteId) GROUP BY 1 ORDER BY 1""").fetchall()
    L += ["## I. FULL TABLE: notes in status history with NO ratings at all, by creation year (these count as Under-rated with 0 ratings)",
          md_table(["year", "notes", "with no ratings", "%"], r), ""]
    open(a.out, "w").write("\n".join(L))
    print("wrote", a.out)

if __name__ == "__main__":
    main()