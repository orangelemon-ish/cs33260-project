#!/usr/bin/env python3
"""Lock-rule and tweetId-decode checks (tasks 3 and 4). Counts only, no text.
Writes lock_checks.md.  Usage: python 06_lock_checks.py --parquet data/parquet --out lock_checks.md
Needs notes.parquet and noteStatusHistory.parquet.
"""
import argparse, os
import duckdb

def md_table(cols, rows):
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join("" if v is None else (f"{v:,}" if isinstance(v, int) else str(v)) for v in r) + " |")
    return "\n".join(out)

DAY = 86400000.0
LOCK_START = 1675209600000   # 2023-02-01 00:00 UTC (after the Jan 2023 lock policy and retro-lock)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", default="data/parquet")
    ap.add_argument("--out", default="lock_checks.md")
    a = ap.parse_args()
    con = duckdb.connect()
    P = lambda n: os.path.join(a.parquet, n + ".parquet")
    con.execute(f"CREATE VIEW notes AS SELECT * FROM read_parquet('{P('notes')}')")
    con.execute(f"CREATE VIEW sh AS SELECT * FROM read_parquet('{P('noteStatusHistory')}')")
    con.execute("""CREATE VIEW s AS SELECT noteId,
        TRY_CAST(createdAtMillis AS BIGINT) AS created,
        NULLIF(GREATEST(TRY_CAST(timestampMillisOfStatusLock AS BIGINT),0),0) AS lock_ts,
        NULLIF(GREATEST(TRY_CAST(timestampMillisOfRetroLock AS BIGINT),0),0) AS retro_ts,
        TRY_CAST(timestampMillisOfCurrentStatus AS BIGINT) AS cur_ts,
        currentStatus, lockedStatus FROM sh""")
    cutoff = con.execute("SELECT max(cur_ts) FROM s").fetchone()[0]
    cut15 = cutoff - 15 * DAY
    L = ["# Lock checks", "",
         f"Data cutoff (max timestampMillisOfCurrentStatus): {con.execute(f'SELECT CAST(epoch_ms({cutoff}) AS VARCHAR)').fetchone()[0]} UTC", ""]

    # 1. Task 3: notes created on/after 2023-02-01 and at least 15 days before the cutoff
    base = f"created >= {LOCK_START} AND created <= {int(cut15)}"
    r = con.execute(f"""SELECT count(*), count(lock_ts), round(100.0*count(lock_ts)/count(*),3),
        count(*) FILTER (WHERE lock_ts IS NOT NULL AND (lock_ts-created)/{DAY} BETWEEN 13.5 AND 14.5),
        round(quantile_cont((lock_ts-created)/{DAY},0.01),2), round(quantile_cont((lock_ts-created)/{DAY},0.5),2),
        round(quantile_cont((lock_ts-created)/{DAY},0.99),2)
        FROM s WHERE {base}""").fetchall()
    L += ["## 1. Notes created 2023-02-01 or later and at least 15 days before the cutoff",
          md_table(["notes", "locked", "% locked", "locked within 13.5-14.5 days", "lag p1 (days)", "lag p50", "lag p99"], r), ""]

    # 2. agreement between lockedStatus and currentStatus
    r = con.execute(f"""SELECT lockedStatus, currentStatus, count(*) FROM s WHERE {base} AND lock_ts IS NOT NULL
                        GROUP BY 1,2 ORDER BY 3 DESC""").fetchall()
    L += ["## 2. lockedStatus vs currentStatus (same population, locked notes only)", md_table(["lockedStatus", "currentStatus", "n"], r), ""]

    # 3. notes in the population that are NOT locked
    r = con.execute(f"""SELECT currentStatus, count(*) FROM s WHERE {base} AND lock_ts IS NULL GROUP BY 1 ORDER BY 2 DESC""").fetchall()
    L += ["## 3. Same population but NOT locked (should be rare if the two-week rule is universal)", md_table(["currentStatus", "n"], r), ""]

    # 4. pre-policy notes
    r = con.execute(f"""SELECT count(*), count(retro_ts), count(lock_ts) FROM s WHERE created < {LOCK_START}""").fetchall()
    L += ["## 4. Notes created before 2023-02-01 (retro-lock era)", md_table(["notes", "with retro lock", "with any lock"], r), ""]

    # 5. fate at lock by year (locked status), population from 2023-02-01
    r = con.execute(f"""SELECT year(epoch_ms(created)), lockedStatus, count(*) FROM s
                        WHERE {base} AND lock_ts IS NOT NULL GROUP BY 1,2 ORDER BY 1,2""").fetchall()
    r = [(str(y), st, n) for y, st, n in r]
    L += ["## 5. Locked status by creation year (population for the RQ2 trend)", md_table(["year", "lockedStatus", "n"], r), ""]

    # 6. Task 4: decoded post time must not be later than the note's creation time
    SNOW = "((TRY_CAST(tweetId AS BIGINT) >> 22) + 1288834974657)"
    r = con.execute(f"""SELECT count(*), count(*) FILTER (WHERE {SNOW} > TRY_CAST(createdAtMillis AS BIGINT)),
        round(100.0*count(*) FILTER (WHERE {SNOW} > TRY_CAST(createdAtMillis AS BIGINT))/count(*),4),
        round(quantile_cont((TRY_CAST(createdAtMillis AS BIGINT)-{SNOW})/3600000.0,0.5),2)
        FROM notes WHERE TRY_CAST(tweetId AS BIGINT) > 0 AND {SNOW} >= 1420070400000""").fetchall()
    L += ["## 6. tweetId decode sanity: notes whose decoded post time is LATER than the note's own creation time (a correct decode should give about 0%; media notes may add a few)",
          md_table(["notes (valid IDs)", "decoded post later than note", "%", "median hours from post to note"], r), ""]
    open(a.out, "w").write("\n".join(L))
    print("wrote", a.out)

if __name__ == "__main__":
    main()