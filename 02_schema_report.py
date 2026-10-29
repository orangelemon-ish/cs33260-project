#!/usr/bin/env python3
"""Write schema_report.md describing every Parquet table (columns, row counts,
date ranges of timestamp columns, distinct counts of ID columns).

A table is either a single file (notes.parquet) or a folder of parts (ratings/*.parquet).
Tables with more than 20 million rows use APPROXIMATE distinct counts to save memory.

Usage:  python 02_schema_report.py --parquet data/parquet --out schema_report.md
        (add --only ratings to describe just one table; --memory-limit 4GB --threads 2 by default)

The report contains NO note text and no sample rows, so it is safe to paste into
chat or commit to git.
"""
import argparse, glob, os
import duckdb

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", default="data/parquet")
    ap.add_argument("--out", default="schema_report.md")
    ap.add_argument("--only", nargs="*", help="table names to describe (default: all)")
    ap.add_argument("--memory-limit", default="4GB")
    ap.add_argument("--threads", type=int, default=2)
    args = ap.parse_args()
    con = duckdb.connect()
    con.execute(f"SET memory_limit='{args.memory_limit}'")
    con.execute(f"SET threads={args.threads}")
    con.execute("SET preserve_insertion_order=false")

    tables = {}
    for path in sorted(glob.glob(os.path.join(args.parquet, "*.parquet"))):
        tables[os.path.basename(path)[:-8]] = f"read_parquet('{path}')"
    for d in sorted(glob.glob(os.path.join(args.parquet, "*"))):
        if os.path.isdir(d) and glob.glob(os.path.join(d, "*.parquet")):
            tables[os.path.basename(d)] = f"read_parquet('{os.path.join(d, '*.parquet')}', union_by_name=true)"

    lines = ["# Schema report", ""]
    for name, src in tables.items():
        if args.only and name not in args.only:
            continue
        cols = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM {src}").fetchall()]
        n = con.execute(f"SELECT count(*) FROM {src}").fetchone()[0]
        big = n > 20_000_000
        lines += [f"## {name}", f"- rows: {n:,}", f"- columns ({len(cols)}): " + ", ".join(cols)]
        lang = [c for c in cols if "lang" in c.lower()]
        lines.append(f"- language-like columns: {lang if lang else 'NONE'}")
        for c in cols:
            low = c.lower()
            if "millis" in low:
                q = f"""SELECT CAST(epoch_ms(min(TRY_CAST(NULLIF("{c}",'') AS BIGINT))) AS VARCHAR),
                               CAST(epoch_ms(max(TRY_CAST(NULLIF("{c}",'') AS BIGINT))) AS VARCHAR),
                               count(NULLIF("{c}",''))
                        FROM {src}"""
                lo, hi, nn = con.execute(q).fetchone()
                lines.append(f"- `{c}`: {lo} to {hi} ({nn:,} non-empty)")
            elif low.endswith("id") or "participant" in low:
                q = f"""SELECT approx_count_distinct("{c}") FROM {src}""" if big else f"""SELECT count(DISTINCT "{c}") FROM {src}"""
                d = con.execute(q).fetchone()[0]
                lines.append(f"- `{c}`: {d:,} distinct" + (" (approx)" if big else ""))
            elif c.lower() in ("currentstatus", "firststatus", "firstnonnmrstatus", "lockedstatus",
                               "helpfulnesslevel", "classification", "ratingsourcebucketed", "enrollmentstate"):
                vals = con.execute(f"""SELECT "{c}", count(*) FROM {src}
                                       GROUP BY 1 ORDER BY 2 DESC LIMIT 12""").fetchall()
                lines.append(f"- `{c}` values: " + ", ".join(f"{v!r}={k:,}" for v, k in vals))
        lines.append("")
    with open(args.out, "w") as f:
        f.write("\n".join(lines))
    print(f"wrote {args.out}")

if __name__ == "__main__":
    main()