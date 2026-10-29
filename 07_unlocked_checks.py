#!/usr/bin/env python3
"""Who are the notes older than 15 days that are NOT locked, and how many notes have AI-writer authors?
Counts only, no text. Writes unlocked_checks.md.
Usage: python 07_unlocked_checks.py --parquet data/parquet --out unlocked_checks.md
Needs noteStatusHistory.parquet and notes.parquet; userEnrollment.parquet is used if present.
"""
import argparse, os
import duckdb

def md_table(cols, rows):
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join("" if v is None else (f"{v:,}" if isinstance(v, int) else str(v)) for v in r) + " |")
    return "\n".join(out)

DAY = 86400000.0
START = 1675209600000  # 2023-02-01

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", default="data/parquet")
    ap.add_argument("--out", default="unlocked_checks.md")
    a = ap.parse_args()
    con = duckdb.connect()
    P = lambda n: os.path.join(a.parquet, n + ".parquet")
    con.execute(f"CREATE VIEW notes AS SELECT * FROM read_parquet('{P('notes')}')")
    con.execute("""CREATE VIEW s AS SELECT noteId, noteAuthorParticipantId AS author,
        TRY_CAST(createdAtMillis AS BIGINT) AS created,
        NULLIF(GREATEST(TRY_CAST(timestampMillisOfStatusLock AS BIGINT),0),0) AS lock_ts,
        TRY_CAST(timestampMillisOfCurrentStatus AS BIGINT) AS cur_ts, currentStatus, lockedStatus
        FROM read_parquet('%s')""" % P('noteStatusHistory'))
    cutoff = con.execute("SELECT max(cur_ts) FROM s").fetchone()[0]
    cut15 = int(cutoff - 15 * DAY)
    con.execute(f"CREATE VIEW pop AS SELECT * FROM s WHERE created >= {START} AND created <= {cut15}")
    L = ["# Unlocked-note checks", "", "Population: notes in noteStatusHistory created 2023-02-01 or later and at least 15 days before the data cutoff.", ""]

    r = con.execute("""SELECT strftime(epoch_ms(created), '%Y-%m') m, count(*), count(*) FILTER (WHERE lock_ts IS NULL),
                       round(100.0*count(*) FILTER (WHERE lock_ts IS NULL)/count(*),2) FROM pop GROUP BY 1 ORDER BY 1""").fetchall()
    L += ["## A. Unlocked share by creation month", md_table(["month", "notes", "unlocked", "% unlocked"], r), ""]

    r = con.execute("""SELECT CASE WHEN n.noteId IS NULL THEN 'not in notes table (likely deleted)' ELSE 'in notes table' END g,
                       count(*), count(*) FILTER (WHERE p.lock_ts IS NULL),
                       round(100.0*count(*) FILTER (WHERE p.lock_ts IS NULL)/count(*),2)
                       FROM pop p LEFT JOIN notes n USING(noteId) GROUP BY 1 ORDER BY 1""").fetchall()
    L += ["## B. Unlocked share: surviving vs. not in notes table", md_table(["group", "notes", "unlocked", "% unlocked"], r), ""]

    r = con.execute("""SELECT n.classification, n.isMediaNote, n.isCollaborativeNote, count(*), count(*) FILTER (WHERE p.lock_ts IS NULL),
                       round(100.0*count(*) FILTER (WHERE p.lock_ts IS NULL)/count(*),2)
                       FROM pop p JOIN notes n USING(noteId) GROUP BY 1,2,3 ORDER BY 4 DESC LIMIT 20""").fetchall()
    L += ["## C. Unlocked share by classification, media flag, collaborative flag (surviving notes)",
          md_table(["classification", "isMediaNote", "isCollaborativeNote", "notes", "unlocked", "% unlocked"], r), ""]

    r = con.execute(f"""SELECT CASE WHEN lock_ts IS NULL THEN 'unlocked' ELSE 'locked' END g, count(*),
                        round(quantile_cont(({cutoff}-cur_ts)/{DAY},0.1),1), round(quantile_cont(({cutoff}-cur_ts)/{DAY},0.5),1),
                        round(quantile_cont(({cutoff}-cur_ts)/{DAY},0.9),1)
                        FROM pop GROUP BY 1 ORDER BY 1""").fetchall()
    L += ["## D. Days between a note's last rescoring (timestampMillisOfCurrentStatus) and the data cutoff (unlocked notes still being rescored would show small values)",
          md_table(["group", "notes", "p10", "p50", "p90"], r), ""]

    r = con.execute(f"""SELECT strftime(epoch_ms(created), '%Y-%m') m, count(*) FROM pop
                        WHERE lock_ts IS NOT NULL AND (lock_ts - created)/{DAY} > 15 GROUP BY 1 ORDER BY 1""").fetchall()
    L += ["## E. Late locks (more than 15 days after creation) by creation month", md_table(["month", "late-locked notes"], r), ""]

    if os.path.exists(P('userEnrollment')):
        con.execute(f"CREATE VIEW ue AS SELECT participantId, enrollmentState FROM read_parquet('{P('userEnrollment')}')")
        r = con.execute("""SELECT coalesce(u.enrollmentState, 'not in userEnrollment') st, count(*),
                           count(*) FILTER (WHERE p.lock_ts IS NULL), round(100.0*count(*) FILTER (WHERE p.lock_ts IS NULL)/count(*),2)
                           FROM pop p LEFT JOIN ue u ON p.author = u.participantId GROUP BY 1 ORDER BY 2 DESC""").fetchall()
        L += ["## F. Notes by author enrollment state (current state; `apiEarnedIn` = AI Note Writer API authors)",
              md_table(["author state", "notes", "unlocked", "% unlocked"], r), ""]
        r = con.execute("""SELECT strftime(epoch_ms(created), '%Y-%m') m, count(*), count(*) FILTER (WHERE u.enrollmentState = 'apiEarnedIn')
                           FROM s LEFT JOIN ue u ON s.author = u.participantId WHERE created >= 1735689600000 GROUP BY 1 ORDER BY 1""").fetchall()
        L += ["## G. Notes per month (2025 onward, all notes in status history) and how many have `apiEarnedIn` authors",
              md_table(["month", "notes", "by apiEarnedIn authors"], r), ""]
    else:
        L += ["(userEnrollment.parquet not found; sections F and G skipped)", ""]
    open(a.out, "w").write("\n".join(L))
    print("wrote", a.out)

if __name__ == "__main__":
    main()