#!/usr/bin/env python3
"""Memory-safe conversion of the Community Notes ratings zips to Parquet, ONE PART AT A TIME.

Why: the all-at-once converter extracts every part first (tens of GB of disk) and lets DuckDB
use most of your RAM, which can freeze or crash a machine. This script
  * extracts a single zip, converts it, deletes the extracted TSV, then moves on;
  * caps DuckDB memory and threads;
  * writes each part to <out>/ratings/ratings-0000N.parquet (via a .tmp file, so a crash never
    leaves a half-written file that looks finished);
  * skips parts that are already done, so you can stop and rerun it at any time.

Usage:
    python 01b_ratings_to_parquet.py --raw data/raw/2026-10-28 --out data/parquet
Optional: --memory-limit 3GB --threads 1   (use these if your machine is small)

Read the result later with:  read_parquet('data/parquet/ratings/*.parquet', union_by_name=true)
"""
import argparse, os, shutil, sys, tempfile, time, zipfile
import duckdb

def find_parts(raw):
    hits = []
    for root, _, files in os.walk(raw):
        for f in files:
            if f.startswith("ratings-") and f.endswith((".zip", ".tsv")):
                hits.append(os.path.join(root, f))
    return sorted(hits)

def count_data_lines(path):
    n, last = 0, b"\n"
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(16 * 1024 * 1024)
            if not chunk:
                break
            n += chunk.count(b"\n")
            last = chunk[-1:]
    if last != b"\n":
        n += 1
    return n - 1  # minus header

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", default="data/parquet")
    ap.add_argument("--memory-limit", default="4GB")
    ap.add_argument("--threads", type=int, default=2)
    a = ap.parse_args()

    parts = find_parts(a.raw)
    if not parts:
        sys.exit(f"No ratings-* files found under {a.raw}")
    out_dir = os.path.join(a.out, "ratings")
    os.makedirs(out_dir, exist_ok=True)
    scratch_root = os.path.join(a.out, ".ratings_scratch")
    os.makedirs(scratch_root, exist_ok=True)

    con = duckdb.connect()
    con.execute(f"SET memory_limit='{a.memory_limit}'")
    con.execute(f"SET threads={a.threads}")
    con.execute("SET preserve_insertion_order=false")
    con.execute(f"SET temp_directory='{os.path.join(scratch_root, 'duckdb_tmp')}'")

    total_rows = 0
    for p in parts:
        stem = os.path.splitext(os.path.basename(p))[0]
        final = os.path.join(out_dir, stem + ".parquet")
        if os.path.exists(final) and os.path.getsize(final) > 0:
            rows = con.execute(f"SELECT count(*) FROM read_parquet('{final}')").fetchone()[0]
            total_rows += rows
            print(f"[{stem}] already done ({rows:,} rows), skipping", flush=True)
            continue
        t0 = time.time()
        work = tempfile.mkdtemp(dir=scratch_root)
        try:
            if p.endswith(".zip"):
                with zipfile.ZipFile(p) as z:
                    members = [m for m in z.namelist() if not m.endswith("/")]
                    assert len(members) == 1, f"{p} has {len(members)} files"
                    tsv = z.extract(members[0], work)
            else:
                tsv = p
            tmp_out = final + ".tmp"
            if os.path.exists(tmp_out):
                os.remove(tmp_out)
            q = tsv.replace("'", "''")
            con.execute(f"""
                COPY (SELECT * FROM read_csv('{q}', delim='\t', header=true, all_varchar=true,
                      quote='', escape='', null_padding=true))
                TO '{tmp_out}' (FORMAT PARQUET, COMPRESSION ZSTD)""")
            rows = con.execute(f"SELECT count(*) FROM read_parquet('{tmp_out}')").fetchone()[0]
            lines = count_data_lines(tsv)
            flag = "OK" if rows == lines else "MISMATCH (embedded line breaks?)"
            os.replace(tmp_out, final)
            total_rows += rows
            print(f"[{stem}] {rows:,} rows vs {lines:,} data lines  {flag}  ({time.time()-t0:.0f}s)", flush=True)
        finally:
            shutil.rmtree(work, ignore_errors=True)
    shutil.rmtree(os.path.join(scratch_root, "duckdb_tmp"), ignore_errors=True)
    print(f"Done. {len(parts)} part(s), {total_rows:,} rows total -> {out_dir}")

if __name__ == "__main__":
    main()