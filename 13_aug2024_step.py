#!/usr/bin/env python3
"""Diagnose the Aug 2024 step (Under-rated 23% -> 18%, Unresolved 56% -> 61%). Counts only, no text.

Usage: python 13_aug2024_step.py --derived data/derived --parquet data/parquet --out data/derived/aug2024_step.md
Needs fates.parquet and the ratings folder.

Three explanations are checked:
  1. Coverage: notes with no rating at all vanish around Aug 2024 (the share with 0 ratings drops).
  2. Counting artifact: late locks in Jul to Sep 2024 let notes collect ratings for longer, so we also count ratings in a fixed
     first 14 days (n_14d), which does not depend on the lock time.
  3. Volume: fewer notes per month would give each note more ratings (ratings per note by month).
"""
import argparse, os
import duckdb

def md_table(cols, rows):
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join("" if v is None else (f"{v:,}" if isinstance(v, int) else str(v)) for v in r) + " |")
    return "\n".join(out)

D = 86400000
H = 3600000
START, END = 1717200000000, 1730419200000          # created 2024-06-01 .. 2024-11-01 (exclusive)
DAY_START, DAY_END = 1721260800000, 1725148800000  # daily table: 2024-07-18 .. 2024-09-01 (exclusive)
Y0, Y1 = 1704067200000, 1735689600000              # 2024-01-01 .. 2025-01-01
MISLEADING = "MISINFORMED_OR_POTENTIALLY_MISLEADING"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--derived", default="data/derived")
    ap.add_argument("--parquet", default="data/parquet")
    ap.add_argument("--out", default="data/derived/aug2024_step.md")
    ap.add_argument("--memory-limit", default="3GB")
    ap.add_argument("--threads", type=int, default=2)
    a = ap.parse_args()
    con = duckdb.connect()
    con.execute(f"SET memory_limit='{a.memory_limit}'"); con.execute(f"SET threads={a.threads}")
    con.execute("SET preserve_insertion_order=false")
    F = os.path.join(a.derived, "fates.parquet")
    R = os.path.join(a.parquet, "ratings", "*.parquet")
    con.execute(f"""CREATE TABLE n AS
      SELECT noteId, created, n_upto_lock, (NOT deleted_like AND classification = '{MISLEADING}') AS main,
             (lock_ms - created) / {D}.0 AS lock_days
      FROM read_parquet('{F}') WHERE created >= {START} AND created < {END}""")
    print("scanning ratings (a few minutes)...", flush=True)
    con.execute(f"""CREATE TABLE rc AS
      SELECT r.noteId, min(TRY_CAST(r.createdAtMillis AS BIGINT)) AS first_rating,
             count(*) FILTER (WHERE TRY_CAST(r.createdAtMillis AS BIGINT) <= n.created + 14*{D}) AS n_14d
      FROM (SELECT noteId, createdAtMillis FROM read_parquet('{R}', union_by_name=true)) r
      JOIN n USING (noteId) GROUP BY r.noteId""")
    con.execute("""CREATE TABLE m AS SELECT n.*, COALESCE(rc.n_14d, 0) AS n_14d,
                          (rc.first_rating - n.created) / 3600000.0 AS hours_to_first
                   FROM n LEFT JOIN rc USING (noteId)""")
    cols = """count(*) AS notes,
              round(100.0*count(*) FILTER (WHERE n_upto_lock = 0)/count(*), 1) AS zero_pct,
              round(100.0*count(*) FILTER (WHERE n_upto_lock < 5)/count(*), 1) AS under5_lock_pct,
              round(100.0*count(*) FILTER (WHERE n_14d < 5)/count(*), 1) AS under5_14d_pct,
              round(median(n_upto_lock), 0) AS med_ratings_lock,
              round(median(n_14d), 0) AS med_ratings_14d,
              round(median(hours_to_first), 1) AS med_hours_first,
              round(100.0*count(*) FILTER (WHERE lock_days > 15)/count(*), 1) AS late_lock_pct"""
    hdr = ["notes", "0 ratings %", "<5 ratings (to lock) %", "<5 ratings (first 14 days) %", "median ratings (to lock)",
           "median ratings (14 days)", "median hours to first rating", "late lock %"]
    L = ["# Aug 2024 step diagnostics", "", "Main population (in notes table, misleading class) unless stated.", ""]
    rows = con.execute(f"SELECT strftime(epoch_ms(created), '%Y-%m-%d') d, {cols} FROM m WHERE main AND created >= {DAY_START} AND created < {DAY_END} GROUP BY 1 ORDER BY 1").fetchall()
    L += ["## A. By creation day, 2024-07-18 to 2024-08-31", md_table(["day"] + hdr, rows), ""]
    rows = con.execute(f"SELECT strftime(epoch_ms(created), '%Y-%m') mth, {cols} FROM m WHERE main GROUP BY 1 ORDER BY 1").fetchall()
    L += ["## B. By creation month, 2024-06 to 2024-10", md_table(["month"] + hdr, rows), ""]
    rows = con.execute(f"""
      SELECT mth, notes, ratings, round(ratings*1.0/notes, 1) FROM (
        SELECT strftime(epoch_ms(created), '%Y-%m') mth, count(*) AS notes FROM read_parquet('{F}')
        WHERE created >= {Y0} AND created < {Y1} GROUP BY 1) a
      JOIN (SELECT strftime(epoch_ms(TRY_CAST(createdAtMillis AS BIGINT)), '%Y-%m') mth2, count(*) AS ratings
            FROM read_parquet('{R}', union_by_name=true)
            WHERE TRY_CAST(createdAtMillis AS BIGINT) >= {Y0} AND TRY_CAST(createdAtMillis AS BIGINT) < {Y1} GROUP BY 1) b ON a.mth = b.mth2
      ORDER BY 1""").fetchall()
    L += ["## C. 2024 by month, all status-history notes: notes created, ratings made (by rating time), ratings per new note",
          md_table(["month", "notes created", "ratings made", "ratings per new note"], rows), ""]
    open(a.out, "w").write("\n".join(L))
    print("wrote", a.out)

if __name__ == "__main__":
    main()