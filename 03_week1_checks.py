#!/usr/bin/env python3
"""Week-1 data checks on notes + noteStatusHistory (no ratings needed).
Writes week1_checks.md (counts only, no note text).

Usage: python 03_week1_checks.py --parquet data/parquet --out week1_checks.md
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
    ap.add_argument("--out", default="week1_checks.md")
    a = ap.parse_args()
    con = duckdb.connect()
    P = lambda n: os.path.join(a.parquet, n + ".parquet")
    con.execute(f"CREATE VIEW notes AS SELECT * FROM read_parquet('{P('notes')}')")
    con.execute(f"CREATE VIEW sh AS SELECT * FROM read_parquet('{P('noteStatusHistory')}')")
    # typed helper view: millisecond columns as BIGINT, values <= 0 treated as missing
    con.execute("""
      CREATE VIEW shx AS SELECT noteId,
        TRY_CAST(createdAtMillis AS BIGINT) AS created,
        NULLIF(GREATEST(TRY_CAST(timestampMillisOfStatusLock AS BIGINT), 0), 0) AS lock_ts,
        NULLIF(GREATEST(TRY_CAST(timestampMillisOfFirstNonNMRStatus AS BIGINT), 0), 0) AS first_nonnmr_ts,
        firstNonNMRStatus, mostRecentNonNMRStatus, currentStatus, lockedStatus
      FROM sh""")
    cutoff = con.execute("SELECT max(TRY_CAST(timestampMillisOfCurrentStatus AS BIGINT)) FROM sh").fetchone()[0]
    L = ["# Week 1 checks", "",
         f"Snapshot cutoff (max timestampMillisOfCurrentStatus): {con.execute(f'SELECT CAST(epoch_ms({cutoff}) AS VARCHAR)').fetchone()[0]} UTC", ""]

    L += ["## 1. Table overlap (deleted notes live only in noteStatusHistory)", md_table(
        ["in both", "only in notes", "only in noteStatusHistory"],
        con.execute("""SELECT (SELECT count(*) FROM notes n JOIN sh s USING(noteId)),
                              (SELECT count(*) FROM notes n ANTI JOIN sh s USING(noteId)),
                              (SELECT count(*) FROM sh s ANTI JOIN notes n USING(noteId))""").fetchall()), ""]

    L += ["## 2. Sentinel timestamps (values <= 0) per millis column in noteStatusHistory"]
    cols = [r[0] for r in con.execute("DESCRIBE SELECT * FROM sh").fetchall() if "millis" in r[0].lower() or "minute" in r[0].lower()]
    rows = []
    for c in cols:
        rows.append((c, con.execute(f"""SELECT count(*) FROM sh WHERE TRY_CAST("{c}" AS BIGINT) <= 0""").fetchone()[0]))
    L += [md_table(["column", "rows with value <= 0"], rows), ""]

    L += ["## 3. Lock lag in days (timestampMillisOfStatusLock - createdAtMillis), notes with a lock",
          md_table(["n", "p10", "p50", "p90", "p99"], con.execute("""
            SELECT count(*), round(quantile_cont((lock_ts-created)/86400000.0,0.1),1),
                   round(quantile_cont((lock_ts-created)/86400000.0,0.5),1),
                   round(quantile_cont((lock_ts-created)/86400000.0,0.9),1),
                   round(quantile_cont((lock_ts-created)/86400000.0,0.99),1)
            FROM shx WHERE lock_ts IS NOT NULL AND created IS NOT NULL""").fetchall()), ""]

    L += ["## 4. currentStatus vs lockedStatus (all notes)",
          md_table(["currentStatus", "lockedStatus", "n"], con.execute("""
            SELECT currentStatus, lockedStatus, count(*) FROM sh GROUP BY 1,2 ORDER BY 3 DESC""").fetchall()), ""]

    L += ["## 5. firstNonNMRStatus vs mostRecentNonNMRStatus vs currentStatus (published-then-removed candidates)",
          md_table(["first", "most recent", "current", "n"], con.execute("""
            SELECT firstNonNMRStatus, mostRecentNonNMRStatus, currentStatus, count(*) FROM sh GROUP BY 1,2,3 ORDER BY 4 DESC""").fetchall()), ""]

    L += ["## 6. Notes created per year x currentStatus",
          md_table(["year", "currentStatus", "n"], con.execute("""
            SELECT year(epoch_ms(created)), currentStatus, count(*) FROM shx WHERE created IS NOT NULL GROUP BY 1,2 ORDER BY 1,2""").fetchall()), ""]

    L += ["## 7. Posts: notes per tweetId (notes table)",
          md_table(["posts", "mean notes/post", "max notes/post", "posts with >1 note"], con.execute("""
            SELECT count(*), round(avg(c),2), max(c), sum(CASE WHEN c>1 THEN 1 ELSE 0 END)
            FROM (SELECT tweetId, count(*) c FROM notes GROUP BY 1)""").fetchall()), ""]

    L += ["## 8. classification x currentStatus (notes in both tables)",
          md_table(["classification", "currentStatus", "n"], con.execute("""
            SELECT n.classification, s.currentStatus, count(*) FROM notes n JOIN sh s USING(noteId) GROUP BY 1,2 ORDER BY 3 DESC""").fetchall()), ""]
    open(a.out, "w").write("\n".join(L))
    print("wrote", a.out)

if __name__ == "__main__":
    main()