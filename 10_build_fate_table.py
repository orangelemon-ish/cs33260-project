#!/usr/bin/env python3
"""Build the note-level fate table (decisions W1-3 to W1-8). One row per note in noteStatusHistory.

Usage (quick check on a 1% sample of notes, same sample as ratings_checks.md):
    python 10_build_fate_table.py --parquet data/parquet --out-dir data/derived --sample-mod 100
Full run:
    python 10_build_fate_table.py --parquet data/parquet --out-dir data/derived

Writes <out-dir>/fates.parquet (or fates_sample100.parquet) and fates_summary.md (counts only).
Fate precedence: Published > Published-then-removed > Rated not helpful > Near miss > Unresolved > Under-rated.
"""
import argparse, os
import duckdb

def md_table(cols, rows):
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join("" if v is None else (f"{v:,}" if isinstance(v, int) else str(v)) for v in r) + " |")
    return "\n".join(out)

DAY = 86400000
WIN_START = 1734048000000      # 2024-12-13 00:00 UTC (main window start)
WIN_END   = 1788739200000      # 2026-09-07 00:00 UTC, exclusive (main window ends 2026-09-06)
EXT_START = 1675209600000      # 2023-02-01 (extended series start)
NEAR_MISS_START = 1722470400000  # 2024-08-01
MISLEADING = "MISINFORMED_OR_POTENTIALLY_MISLEADING"
FATES = ["Published", "Published-then-removed", "Rated not helpful", "Near miss", "Unresolved", "Under-rated"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", default="data/parquet")
    ap.add_argument("--out-dir", default="data/derived")
    ap.add_argument("--sample-mod", type=int, default=1, help="1 = all notes; 100 = 1%% of notes")
    ap.add_argument("--memory-limit", default="3GB")
    ap.add_argument("--threads", type=int, default=2)
    a = ap.parse_args()
    M = a.sample_mod
    os.makedirs(a.out_dir, exist_ok=True)
    con = duckdb.connect()
    con.execute(f"SET memory_limit='{a.memory_limit}'")
    con.execute(f"SET threads={a.threads}")
    con.execute("SET preserve_insertion_order=false")
    con.execute(f"SET temp_directory='{os.path.join(a.out_dir, '.tmp_duckdb')}'")
    P = lambda n: os.path.join(a.parquet, n)
    samp = f"WHERE hash(noteId) % {M} = 0" if M > 1 else ""

    con.execute(f"""CREATE TABLE sh AS SELECT noteId, noteAuthorParticipantId AS author,
        TRY_CAST(createdAtMillis AS BIGINT) AS created,
        NULLIF(GREATEST(TRY_CAST(timestampMillisOfStatusLock AS BIGINT), 0), 0) AS lock_ms,
        NULLIF(firstNonNMRStatus, '') AS first_status, NULLIF(mostRecentNonNMRStatus, '') AS recent_status,
        NULLIF(lockedStatus, '') AS locked_status, currentStatus,
        COALESCE(TRY_CAST(timestampMillisOfFirstNmrDueToMinStableCrhTime AS BIGINT) > 0, false) AS stable_hold,
        TRY_CAST(timestampMillisOfCurrentStatus AS BIGINT) AS cur_ms
        FROM read_parquet('{P('noteStatusHistory.parquet')}') {samp}""")
    cutoff = con.execute("SELECT max(cur_ms) FROM (SELECT cur_ms FROM sh)").fetchone()[0]
    if M > 1:   # the cutoff must come from the full file, not the sample
        cutoff = con.execute(f"SELECT max(TRY_CAST(timestampMillisOfCurrentStatus AS BIGINT)) FROM read_parquet('{P('noteStatusHistory.parquet')}')").fetchone()[0]
    cut15 = int(cutoff - 15 * DAY)

    con.execute(f"""CREATE TABLE nt AS SELECT noteId, classification, isMediaNote, isCollaborativeNote
                    FROM read_parquet('{P('notes.parquet')}')""")
    con.execute(f"""CREATE TABLE ue AS SELECT participantId, enrollmentState FROM read_parquet('{P('userEnrollment.parquet')}')""")
    con.execute("CREATE TABLE lockinfo AS SELECT noteId, lock_ms FROM sh")
    print("counting ratings up to lock time (the long step)...", flush=True)
    rsamp = f"WHERE hash(noteId) % {M} = 0" if M > 1 else ""
    con.execute(f"""CREATE TABLE rc AS
        SELECT r.noteId, count(*) AS n_total,
               count(*) FILTER (WHERE l.lock_ms IS NULL OR TRY_CAST(r.createdAtMillis AS BIGINT) <= l.lock_ms) AS n_upto_lock
        FROM (SELECT noteId, createdAtMillis FROM read_parquet('{P('ratings')}/*.parquet', union_by_name=true) {rsamp}) r
        JOIN lockinfo l USING (noteId) GROUP BY r.noteId""")

    con.execute(f"""CREATE TABLE fates AS
        WITH base AS (
          SELECT sh.noteId, sh.author, sh.created, strftime(epoch_ms(sh.created), '%Y-%m') AS created_month,
                 (nt.noteId IS NULL) AS deleted_like, nt.classification, nt.isMediaNote, nt.isCollaborativeNote,
                 CASE WHEN ue.enrollmentState = 'apiEarnedIn' THEN 'AI' ELSE 'other' END AS author_type,
                 sh.lock_ms, (sh.lock_ms IS NOT NULL) AS locked,
                 COALESCE(sh.locked_status, sh.currentStatus) AS final_status,
                 COALESCE(sh.first_status = 'CURRENTLY_RATED_HELPFUL' OR sh.recent_status = 'CURRENTLY_RATED_HELPFUL', false) AS ever_helpful,
                 COALESCE(sh.first_status = 'CURRENTLY_RATED_NOT_HELPFUL' OR sh.recent_status = 'CURRENTLY_RATED_NOT_HELPFUL', false) AS ever_not_helpful,
                 sh.stable_hold,
                 COALESCE(rc.n_total, 0) AS n_total, COALESCE(rc.n_upto_lock, 0) AS n_upto_lock
          FROM sh LEFT JOIN nt USING (noteId) LEFT JOIN rc USING (noteId) LEFT JOIN ue ON sh.author = ue.participantId)
        SELECT *,
          CASE WHEN n_upto_lock = 0 THEN '0' WHEN n_upto_lock < 5 THEN '1-4' WHEN n_upto_lock < 10 THEN '5-9' ELSE '10+' END AS ratings_bucket,
          CASE WHEN final_status = 'CURRENTLY_RATED_HELPFUL' THEN 'Published'
               WHEN ever_helpful THEN 'Published-then-removed'
               WHEN final_status = 'CURRENTLY_RATED_NOT_HELPFUL' OR ever_not_helpful THEN 'Rated not helpful'
               WHEN stable_hold AND created >= {NEAR_MISS_START} THEN 'Near miss'
               WHEN n_upto_lock >= 5 THEN 'Unresolved'
               ELSE 'Under-rated' END AS fate,
          (created >= {WIN_START} AND created < {WIN_END}) AS in_main_window,
          (created >= {EXT_START} AND created <= {cut15}) AS in_extended
        FROM base""")
    name = "fates.parquet" if M == 1 else f"fates_sample{M}.parquet"
    con.execute(f"COPY fates TO '{os.path.join(a.out_dir, name)}' (FORMAT PARQUET, COMPRESSION ZSTD)")

    main_pop = f"in_main_window AND NOT deleted_like AND classification = '{MISLEADING}'"
    L = ["# Fate table summary", "", f"Output: {name} (sample-mod {M}). Counts only.", ""]
    tot = con.execute("SELECT count(*), count(*) FILTER (WHERE in_main_window), count(*) FILTER (WHERE in_extended), "
                      "count(*) FILTER (WHERE deleted_like), count(*) FILTER (WHERE author_type = 'AI') FROM fates").fetchall()
    L += ["## A. Table size", md_table(["notes", "in main window", "in extended window", "deleted-like", "AI authors"], tot), ""]
    rows = []
    for f in FATES:
        n1, n2 = con.execute(f"SELECT count(*) FILTER (WHERE {main_pop} AND fate = '{f}'), count(*) FILTER (WHERE in_main_window AND fate = '{f}') FROM fates").fetchone()
        rows.append((f, n1, n2))
    t1 = sum(r[1] for r in rows) or 1
    t2 = sum(r[2] for r in rows) or 1
    rows = [(f, n1, f"{100*n1/t1:.1f}%", n2, f"{100*n2/t2:.1f}%") for f, n1, n2 in rows]
    rows.append(("Total", t1, "100%", t2, "100%"))
    L += ["## B. Fates in the main window",
          "Main population = in notes table, misleading class. S2 = every status-history note in the window (deleted included, no class filter).",
          md_table(["fate", "main population", "%", "S2", "%"], rows), ""]
    r = con.execute("SELECT final_status, ratings_bucket, count(*) FROM fates WHERE in_main_window GROUP BY 1, 2 ORDER BY 1, 2").fetchall()
    L += ["## C. S2 in the main window: final status by ratings up to lock (used to check against the 1% sample)",
          md_table(["final status", "ratings up to lock", "notes"], r), ""]
    if M == 1:
        ns = con.execute(f"SELECT count(*) FROM nt ANTI JOIN (SELECT noteId FROM sh) s USING (noteId)").fetchone()[0]
        L += ["## D. Notes in the notes table with no status-history row (never scored)", md_table(["notes"], [(ns,)]), ""]
    else:
        L += ["## D. Check against ratings_checks.md (sample-mod 100)",
              "Section C should read: Helpful 10+ = 1,415; Not Helpful 1-4 = 1, 5-9 = 93, 10+ = 585; NMR 0 = 22, 1-4 = 3,495, 5-9 = 2,168, 10+ = 8,474 (16,253 notes).", ""]
    open(os.path.join(a.out_dir, "fates_summary.md" if M == 1 else f"fates_summary_sample{M}.md"), "w").write("\n".join(L))
    print("done:", name)

if __name__ == "__main__":
    main()