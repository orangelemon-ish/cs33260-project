#!/usr/bin/env python3
"""Monthly fate shares (RQ2a/b) with 95% Wilson intervals and rule-change dates marked.

Usage:  python 11_monthly_fates.py --derived data/derived
Reads <derived>/fates.parquet. Writes into the same folder:
  monthly_fates_main.csv, monthly_fates_s2.csv, monthly_fates_main.png, monthly_fates_lines.png, monthly_summary.md
Main population = in notes table, misleading class. S2 = every status-history note (deleted included, no class filter).
Series = extended window (created 2023-02-01 to 15 days before the data cutoff). The last two bars are
2026-09-01..06 (end of the main trend, W1-30) and 2026-09-07..10-11 (later cohort, scored partly under the 2026-09-21 rule).
Needs: duckdb, matplotlib.
"""
import argparse, csv, datetime as dt, math, os
import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

FATES = ["Published", "Published-then-removed", "Rated not helpful", "Near miss", "Unresolved", "Under-rated"]
COLORS = ["#2a9d8f", "#8ab17d", "#e76f51", "#e9c46a", "#7f8fa9", "#264653"]
MISLEADING = "MISINFORMED_OR_POTENTIALLY_MISLEADING"
CHANGES = [  # (date, short label)  scoring-rule or system changes (decisions.md, section D)
    ("2024-07-25", "subset scoring"), ("2024-08-12", "30-min stability hold"), ("2024-10-07", "flip-flop fix"),
    ("2024-12-12", "Expansion lock"), ("2025-03-27", "5+5 rater rule"), ("2025-04-08", "net helpful"),
    ("2025-05-28", "engagement intercept"), ("2025-06-30", "independence intercept"),
    ("2025-11-10", "new Gaussian model"), ("2026-06-30", "group models"), ("2026-07-28", "Gaussian to Core"),
    ("2026-08-03", "Gaussian Expansion"), ("2026-09-21", "Not Helpful 3+3 rule")]
AI_LAUNCH = ("2025-09-02", "AI writers start")
SEP1, SEP7 = 1788220800000, 1788739200000   # 2026-09-01, 2026-09-07 00:00 UTC

def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))

def fetch(con, where):
    q = f"""
      SELECT CASE WHEN created < {SEP1} THEN strftime(epoch_ms(created), '%Y-%m')
                  WHEN created < {SEP7} THEN '2026-09-a' ELSE '2026-09-b' END AS pk, fate, count(*)
      FROM read_parquet('{{f}}') WHERE in_extended AND {where} GROUP BY 1, 2"""
    return con.execute(q.replace("{f}", FATES_FILE)).fetchall()

def table(rows):
    keys = sorted({r[0] for r in rows})
    counts = {k: {f: 0 for f in FATES} for k in keys}
    for pk, f, n in rows:
        counts[pk][f] = n
    out = []
    for k in keys:
        tot = sum(counts[k].values())
        rec = {"period": k, "notes": tot}
        for f in FATES:
            lo, hi = wilson(counts[k][f], tot)
            rec[f] = counts[k][f]; rec[f + " %"] = round(100 * counts[k][f] / tot, 2) if tot else 0
            rec[f + " lo"] = round(100 * lo, 2); rec[f + " hi"] = round(100 * hi, 2)
        out.append(rec)
    return out

def label(k):
    return {"2026-09-a": "2026-09 (1-6)", "2026-09-b": "09-07 to 10-11 (later)"}.get(k, k)

def xpos(date, keys):
    d = dt.date.fromisoformat(date)
    m = d.strftime("%Y-%m")
    if d >= dt.date(2026, 9, 7):
        return keys.index("2026-09-b") if "2026-09-b" in keys else None
    if d >= dt.date(2026, 9, 1):
        return keys.index("2026-09-a") if "2026-09-a" in keys else None
    if m not in keys:
        return None
    nxt = (d.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
    dim = (nxt - d.replace(day=1)).days
    return keys.index(m) + (d.day - 1) / dim

def write_csv(path, rec):
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rec[0].keys()))
        w.writeheader(); w.writerows(rec)

def main():
    global FATES_FILE
    ap = argparse.ArgumentParser()
    ap.add_argument("--derived", default="data/derived")
    a = ap.parse_args()
    FATES_FILE = os.path.join(a.derived, "fates.parquet")
    con = duckdb.connect()
    main_rec = table(fetch(con, f"NOT deleted_like AND classification = '{MISLEADING}'"))
    s2_rec = table(fetch(con, "true"))
    write_csv(os.path.join(a.derived, "monthly_fates_main.csv"), main_rec)
    write_csv(os.path.join(a.derived, "monthly_fates_s2.csv"), s2_rec)
    keys = [r["period"] for r in main_rec]
    x = list(range(len(keys)))

    # Figure 1: stacked shares (main population)
    fig, ax = plt.subplots(figsize=(14, 6))
    bottom = [0.0] * len(keys)
    for f, c in zip(FATES, COLORS):
        vals = [r[f + " %"] for r in main_rec]
        bars = ax.bar(x, vals, bottom=bottom, color=c, label=f, width=0.85)
        for i, k in enumerate(keys):
            if k in ("2026-09-a", "2026-09-b"):
                bars[i].set_hatch("//"); bars[i].set_edgecolor("white")
        bottom = [b + v for b, v in zip(bottom, vals)]
    if "2024-12" in keys:
        ax.axvspan(-0.5, keys.index("2024-12") - 0.5, color="grey", alpha=0.12, zorder=0)
        ax.text(keys.index("2024-12") / 2, 103, "extended series (before main window)", ha="center", fontsize=9, color="grey")
    for i, (d, lab) in enumerate(CHANGES, 1):
        p = xpos(d, keys)
        if p is not None:
            ax.axvline(p, color="black", ls="--", lw=0.8)
            ax.text(p, 101 + (i % 3) * 2.2, str(i), ha="center", fontsize=8)
    p = xpos(AI_LAUNCH[0], keys)
    if p is not None:
        ax.axvline(p, color="purple", ls=":", lw=1.2); ax.text(p, 108, "AI", ha="center", fontsize=8, color="purple")
    ax.set_xticks(x); ax.set_xticklabels([label(k) for k in keys], rotation=90, fontsize=7)
    ax.set_ylim(0, 112); ax.set_ylabel("share of notes created that month (%)")
    ax.set_title("Note fates by creation month (main population: in notes table, misleading class)")
    ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0), fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(a.derived, "monthly_fates_main.png"), dpi=150); plt.close(fig)

    # Figure 2: lines with 95% CI (main) and S2 dotted
    fig, ax = plt.subplots(figsize=(14, 5))
    s2 = {r["period"]: r for r in s2_rec}
    for f, c in [("Published", COLORS[0]), ("Unresolved", COLORS[4]), ("Under-rated", COLORS[5])]:
        ax.plot(x, [r[f + " %"] for r in main_rec], color=c, lw=2, label=f + " (main)")
        ax.fill_between(x, [r[f + " lo"] for r in main_rec], [r[f + " hi"] for r in main_rec], color=c, alpha=0.25)
        ax.plot(x, [s2[k][f + " %"] for k in keys], color=c, lw=1.5, ls=":", label=f + " (S2: incl. deleted, all classes)")
    for d, lab in CHANGES:
        p = xpos(d, keys)
        if p is not None:
            ax.axvline(p, color="black", ls="--", lw=0.6)
    p = xpos(AI_LAUNCH[0], keys)
    if p is not None:
        ax.axvline(p, color="purple", ls=":", lw=1.2)
    ax.set_xticks(x); ax.set_xticklabels([label(k) for k in keys], rotation=90, fontsize=7)
    ax.set_ylabel("share (%)"); ax.set_title("Published, Unresolved and Under-rated shares by creation month (95% Wilson intervals, main population)")
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout(); fig.savefig(os.path.join(a.derived, "monthly_fates_lines.png"), dpi=150); plt.close(fig)

    # summary (counts only)
    def pct(r, f): return f"{r[f + ' %']:.1f}"
    L = ["# Monthly fate summary", "", "Main population, shares in %. Intervals are narrow because n is large; they ignore non-sampling issues.", ""]
    by_year = {}
    for r in main_rec:
        y = r["period"][:4]
        d = by_year.setdefault(y, {f: 0 for f in FATES} | {"n": 0})
        d["n"] += r["notes"]
        for f in FATES: d[f] += r[f]
    L += ["## By creation year (extended series; 2026 includes the last two bars)",
          "| year | notes | " + " | ".join(FATES) + " |", "|" + "---|" * (len(FATES) + 2)]
    for y, d in sorted(by_year.items()):
        L.append(f"| {y} | {d['n']:,} | " + " | ".join(f"{100*d[f]/d['n']:.1f}" for f in FATES) + " |")
    L += ["", "## Last 10 periods", "| period | notes | " + " | ".join(FATES) + " |", "|" + "---|" * (len(FATES) + 2)]
    for r in main_rec[-10:]:
        L.append(f"| {r['period']} | {r['notes']:,} | " + " | ".join(pct(r, f) for f in FATES) + " |")
    L += ["", "## Marker key (dashed lines in the figures)"] + [f"{i}. {d}: {lab}" for i, (d, lab) in enumerate(CHANGES, 1)]
    L += [f"AI: {AI_LAUNCH[0]} {AI_LAUNCH[1]}"]
    open(os.path.join(a.derived, "monthly_summary.md"), "w").write("\n".join(L))
    print("wrote CSVs, two PNGs and monthly_summary.md in", a.derived)

if __name__ == "__main__":
    main()