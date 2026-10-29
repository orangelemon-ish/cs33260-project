#!/usr/bin/env python3
"""Deleted-like notes (in noteStatusHistory but not in notes.parquet) by month and author type (W1-36).
Counts only, no text. Writes deleted_checks.md.
Usage: python 09_deleted_checks.py --parquet data/parquet --out deleted_checks.md
Needs notes.parquet, noteStatusHistory.parquet, ratings/ (folder); userEnrollment.parquet if present.
"""
import argparse, os
import duckdb

def md_table(cols, rows):
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join("" if v is None else (f"{v:,}" if isinstance(v, int) else str(v)) for v in r) + " |")
    return "\n".join(out)

WIN_START = 1734048000000   # 2024-12-13 (W1-33)
WIN_END   = 1788739200000   # 2026-09-07 exclusive (W1-30)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", default="data/parquet")
    ap.add_argument("--out", default="deleted_checks.md")
    ap.add_argument("--memory-limit", default="3GB")
    ap.add_argument("--threads", type=int, default=2)
    a = ap.parse_args()
    con = duckdb.connect()
    con.execute(f"SET memory_limit='{a.memory_limit}'")
    con.execute(f"SET threads={a.threads}")
    con.execute("SET preserve_insertion_order=false")
    con.execute(f"SET temp_directory='{os.path.join(a.parquet, '.checks_tmp')}'")
    P = lambda n: os.path.join(a.parquet, n)
    con.execute(f"CREATE VIEW notes AS SELECT noteId FROM read_parquet('{P('notes.parquet')}')")
    con.execute("CREATE TABLE rated AS SELECT DISTINCT noteId FROM read_parquet('%s/*.parquet', union_by_name=true)" % P('ratings'))
    has_ue = os.path.exists(P('userEnrollment.parquet'))
    ue_join = ""
    author_expr = "'unknown'"
    if has_ue:
        con.execute(f"CREATE VIEW ue AS SELECT participantId, enrollmentState FROM read_parquet('{P('userEnrollment.parquet')}')")
        ue_join = "LEFT JOIN ue ON s.noteAuthorParticipantId = ue.participantId"
        author_expr = "CASE WHEN ue.enrollmentState = 'apiEarnedIn' THEN 'AI (apiEarnedIn)' ELSE 'other' END"
    con.execute(f"""CREATE TABLE sx AS
        SELECT s.noteId, TRY_CAST(s.createdAtMillis AS BIGINT) AS created,
               coalesce(NULLIF(s.lockedStatus,''), s.currentStatus) AS final,
               (n.noteId IS NULL) AS deleted_like, (r.noteId IS NOT NULL) AS has_rating,
               {author_expr} AS author_type
        FROM read_parquet('{P('noteStatusHistory.parquet')}') s
        LEFT JOIN notes n ON s.noteId = n.noteId
        LEFT JOIN rated r ON s.noteId = r.noteId
        {ue_join}""")
    L = ["# Deleted-like note checks", "",
         "'Deleted-like' = in noteStatusHistory but not in notes.parquet. Month = creation month.", ""]

    r = con.execute("""SELECT strftime(epoch_ms(created), '%Y-%m') m, count(*), count(*) FILTER (WHERE deleted_like),
                       round(100.0*count(*) FILTER (WHERE deleted_like)/count(*),2),
                       round(100.0*count(*) FILTER (WHERE deleted_like AND has_rating)/nullif(count(*) FILTER (WHERE deleted_like),0),1)
                       FROM sx WHERE created >= 1704067200000 GROUP BY 1 ORDER BY 1""").fetchall()
    L += ["## A. Deleted-like share by creation month (2024 onward) and the share of those with at least one rating",
          md_table(["month", "notes", "deleted-like", "% deleted-like", "% of deleted-like with a rating"], r), ""]

    r = con.execute("""SELECT strftime(epoch_ms(created), '%Y-%m') m, author_type, count(*), count(*) FILTER (WHERE deleted_like),
                       round(100.0*count(*) FILTER (WHERE deleted_like)/count(*),2)
                       FROM sx WHERE created >= 1756684800000 GROUP BY 1,2 ORDER BY 1,2""").fetchall()
    L += ["## B. From Sep 2025: deleted-like share by creation month and author type (AI = current apiEarnedIn state)",
          md_table(["month", "author type", "notes", "deleted-like", "% deleted-like"], r), ""]

    r = con.execute(f"""SELECT deleted_like, final, count(*) FROM sx
                       WHERE created >= {WIN_START} AND created < {WIN_END} GROUP BY 1,2 ORDER BY 1,3 DESC""").fetchall()
    L += ["## C. Main window (created 2024-12-13 to 2026-09-06): final status for deleted-like (true) vs. notes present in notes.parquet (false)",
          md_table(["deleted-like", "final status", "notes"], [(str(a_), b, c) for a_, b, c in r]), ""]
    open(a.out, "w").write("\n".join(L))
    print("wrote", a.out)

if __name__ == "__main__":
    main()