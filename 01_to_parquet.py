#!/usr/bin/env python3
"""Convert a downloaded Community Notes snapshot (zipped or plain TSVs) to Parquet.

Usage:
    python 01_to_parquet.py --raw data/raw/2026-10-27 --out data/parquet

It finds files by name prefix anywhere under --raw, so it does not depend on the
exact folder layout of the downloader. Every column is read as text (all_varchar)
so IDs and millisecond timestamps are never silently mangled; cast later in SQL.

Prints, per dataset: files found, rows in Parquet, and data lines in the source
files. A mismatch means some text field contains a line break; tell your teammates.
"""
import argparse, glob, os, sys, tempfile, zipfile
import duckdb

# dataset name -> filename prefixes to look for
PREFIXES = {
    "notes": ["notes-"],
    "ratings": ["ratings-"],
    "noteStatusHistory": ["noteStatusHistory-"],
    "userEnrollment": ["userEnrollment-"],
    "requests": ["batSignals-", "noteRequests-", "requests-"],  # name unconfirmed; see --requests-glob
}

def find_files(raw, prefixes):
    hits = []
    for root, _, files in os.walk(raw):
        for f in files:
            if any(f.startswith(p) for p in prefixes) and f.endswith((".zip", ".tsv")):
                hits.append(os.path.join(root, f))
    return sorted(hits)

def count_data_lines(paths):
    n = 0
    for p in paths:
        with open(p, "rb") as fh:
            n += sum(1 for _ in fh) - 1  # minus header
    return n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, help="snapshot folder, e.g. data/raw/2026-10-27")
    ap.add_argument("--out", default="data/parquet")
    ap.add_argument("--requests-glob", default=None,
                    help="explicit path/glob to the note-request file(s) if the name differs")
    ap.add_argument("--only", nargs="*", help="subset of datasets to convert")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    con = duckdb.connect()
    con.execute("PRAGMA temp_directory='%s'" % os.path.join(args.out, ".duckdb_tmp"))

    for name, prefixes in PREFIXES.items():
        if args.only and name not in args.only:
            continue
        if name == "requests" and args.requests_glob:
            found = sorted(glob.glob(args.requests_glob))
        else:
            found = find_files(args.raw, prefixes)
        if not found:
            print(f"[{name}] NO FILES FOUND (prefixes {prefixes}) -- skipping")
            continue
        with tempfile.TemporaryDirectory(dir=args.out) as tmp:
            tsvs = []
            for p in found:
                if p.endswith(".zip"):
                    with zipfile.ZipFile(p) as z:
                        z.extractall(tmp)
                        tsvs += [os.path.join(tmp, m) for m in z.namelist() if not m.endswith("/")]
                else:
                    tsvs.append(p)
            tsvs = sorted(tsvs)
            out = os.path.join(args.out, f"{name}.parquet")
            files_sql = "[" + ",".join("'%s'" % t.replace("'", "''") for t in tsvs) + "]"
            con.execute(f"""
                COPY (SELECT * FROM read_csv({files_sql}, delim='\t', header=true,
                      all_varchar=true, quote='', escape='', null_padding=true,
                      union_by_name=true))
                TO '{out}' (FORMAT PARQUET, COMPRESSION ZSTD)""")
            rows = con.execute(f"SELECT count(*) FROM read_parquet('{out}')").fetchone()[0]
            lines = count_data_lines(tsvs)
            flag = "OK" if rows == lines else "MISMATCH (check for embedded newlines)"
            print(f"[{name}] {len(found)} source file(s) -> {out}: {rows:,} rows vs {lines:,} data lines  {flag}")

if __name__ == "__main__":
    sys.exit(main())