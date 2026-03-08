"""
ProductHunt Market Intelligence — Chart Generation
Produces 9 business-focused charts into charts/
Run from project root: python scripts/generate_charts.py
"""

import csv
import collections
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import numpy as np

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
CHARTS_DIR = Path("charts")
CHARTS_DIR.mkdir(exist_ok=True)

PALETTE_MAIN    = "#2563EB"   # blue
PALETTE_ACCENT  = "#F59E0B"   # amber
PALETTE_GOOD    = "#10B981"   # green
PALETTE_NEUTRAL = "#6B7280"   # grey
PALETTE_WARN    = "#EF4444"   # red

COLORS_RATING = [PALETTE_GOOD, "#34D399", PALETTE_ACCENT, PALETTE_WARN]

plt.rcParams.update({
    "font.family":      "DejaVu Sans",
    "font.size":        11,
    "axes.spines.top":  False,
    "axes.spines.right":False,
    "axes.grid":        True,
    "grid.alpha":       0.3,
    "grid.linestyle":   "--",
    "figure.dpi":       130,
})

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
print("Loading data …")

with open("data/products.csv", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

with open("data/categories.csv", encoding="utf-8") as f:
    _cat_raw = list(csv.DictReader(f))

# Clean category names (some have long descriptions appended)
cat_name_map: dict[str, str] = {}
for r in _cat_raw:
    slug = r["slug"]
    raw_name = r["name"]
    # Truncate at first sentence-ending word boundary if too long
    name = raw_name.split(".")[0].strip()
    if len(name) > 45:
        name = name[:43].rsplit(" ", 1)[0] + "…"
    cat_name_map[slug] = name

def cat_label(slug: str) -> str:
    return cat_name_map.get(slug, slug.replace("-", " ").title())

# Unique products (de-duplicate across categories)
unique: dict[str, dict] = {}
for r in rows:
    if r["id"] not in unique:
        unique[r["id"]] = r

print(f"  {len(rows):,} total rows | {len(unique):,} unique products | {len(cat_name_map)} categories")

# Aggregate per-category metrics
cat_followers:   collections.defaultdict = collections.defaultdict(list)
cat_ratings:     collections.defaultdict = collections.defaultdict(list)
cat_counts:      collections.Counter     = collections.Counter()
cat_reviewed:    collections.Counter     = collections.Counter()

for r in rows:
    slug = r["category_slug"]
    fl   = int(r["followers_count"] or 0)
    rv   = float(r["reviews_rating"] or 0)
    rc   = int(r["reviews_count"]   or 0)

    cat_followers[slug].append(fl)
    cat_counts[slug] += 1
    if rc >= 1:
        cat_reviewed[slug] += 1
    if rv > 0 and rc >= 5:
        cat_ratings[slug].append(rv)

# Helper
def save(fig: plt.Figure, name: str) -> None:
    path = CHARTS_DIR / name
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Saved -> {path}")


# ===========================================================================
# CHART 1 — Market Size: Total Audience Demand by Category (Top 15)
# ===========================================================================
print("\nChart 1: Market size by total followers …")

cat_total_fl = {slug: sum(v) for slug, v in cat_followers.items()}
top15_market = sorted(cat_total_fl.items(), key=lambda x: -x[1])[:15]
labels  = [cat_label(s) for s, _ in top15_market]
values  = [v / 1_000 for _, v in top15_market]   # in thousands

fig, ax = plt.subplots(figsize=(12, 7))
bars = ax.barh(labels[::-1], values[::-1], color=PALETTE_MAIN, height=0.65)

for bar, val in zip(bars, values[::-1]):
    ax.text(bar.get_width() + 15, bar.get_y() + bar.get_height() / 2,
            f"{val:,.0f}K", va="center", fontsize=9.5, color="#374151")

ax.set_xlabel("Total Followers Across All Products (Thousands)", labelpad=8)
ax.set_title("Where Is the Audience?\nTop 15 Categories by Total Community Demand",
             fontsize=14, fontweight="bold", pad=14)
ax.set_xlim(0, max(values) * 1.18)
ax.tick_params(axis="y", labelsize=10)
fig.tight_layout()
save(fig, "01_market_size_by_category.png")


# ===========================================================================
# CHART 2 — Opportunity Score: Demand Per Product (min 50 products)
# ===========================================================================
print("Chart 2: Opportunity score (demand-per-product) …")

opp = {
    slug: sum(cat_followers[slug]) / cat_counts[slug]
    for slug in cat_counts
    if cat_counts[slug] >= 50
}
top15_opp = sorted(opp.items(), key=lambda x: -x[1])[:15]
labels  = [cat_label(s) for s, _ in top15_opp]
values  = [v for _, v in top15_opp]

# Color-code AI vs non-AI
ai_keywords = {"ai", "llm", "vibe", "coding", "model", "voice", "agent", "notetaker"}
colors = [
    PALETTE_GOOD if any(kw in s for kw in ai_keywords) else PALETTE_MAIN
    for s, _ in top15_opp
]

fig, ax = plt.subplots(figsize=(12, 7))
bars = ax.barh(labels[::-1], values[::-1], color=colors[::-1], height=0.65)

for bar, val in zip(bars, values[::-1]):
    ax.text(bar.get_width() + 10, bar.get_y() + bar.get_height() / 2,
            f"{val:,.0f}", va="center", fontsize=9.5, color="#374151")

ax.set_xlabel("Average Followers per Product", labelpad=8)
ax.set_title("Where Is the Opportunity?\nAverage Audience per Product (Min. 50 Products per Category)",
             fontsize=14, fontweight="bold", pad=14)

legend_patches = [
    mpatches.Patch(color=PALETTE_GOOD, label="AI-native category"),
    mpatches.Patch(color=PALETTE_MAIN, label="Traditional category"),
]
ax.legend(handles=legend_patches, loc="lower right", fontsize=9)
ax.set_xlim(0, max(values) * 1.2)
fig.tight_layout()
save(fig, "02_opportunity_score_per_product.png")


# ===========================================================================
# CHART 3 — Quality Pays: Rating Bracket vs Average Followers
# ===========================================================================
print("Chart 3: Rating vs followers …")

reviewed_unique = [r for r in unique.values()
                   if float(r["reviews_rating"] or 0) > 0 and int(r["reviews_count"] or 0) >= 5]

buckets = {
    "Perfect\n(4.5 – 5.0)":  [],
    "Strong\n(4.0 – 4.5)":   [],
    "Average\n(3.0 – 4.0)":  [],
    "Weak\n(Below 3.0)":     [],
}
bucket_n = {}
for r in reviewed_unique:
    rt = float(r["reviews_rating"])
    fl = int(r["followers_count"] or 0)
    if rt >= 4.5:   buckets["Perfect\n(4.5 – 5.0)"].append(fl)
    elif rt >= 4.0: buckets["Strong\n(4.0 – 4.5)"].append(fl)
    elif rt >= 3.0: buckets["Average\n(3.0 – 4.0)"].append(fl)
    else:           buckets["Weak\n(Below 3.0)"].append(fl)

labels = list(buckets.keys())
avgs   = [sum(v) / len(v) if v else 0 for v in buckets.values()]
counts = [len(v) for v in buckets.values()]

fig, ax = plt.subplots(figsize=(9, 5))
bars = ax.bar(labels, avgs, color=COLORS_RATING, width=0.55)

for bar, avg, n in zip(bars, avgs, counts):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 15,
            f"{avg:,.0f}", ha="center", fontsize=11, fontweight="bold", color="#111827")
    ax.text(bar.get_x() + bar.get_width() / 2, -60,
            f"n={n:,}", ha="center", fontsize=8.5, color="#6B7280")

ax.set_ylabel("Average Followers", labelpad=8)
ax.set_title("Does Quality Pay Off?\nAverage Community Size by Product Review Rating",
             fontsize=14, fontweight="bold", pad=14)
ax.set_ylim(-80, max(avgs) * 1.2)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
fig.tight_layout()
save(fig, "03_quality_vs_traction.png")


# ===========================================================================
# CHART 4 — Persistence Pays: Launch Frequency vs Average Followers
# ===========================================================================
print("Chart 4: Launch frequency vs followers …")

launch_buckets: dict[str, list] = {
    "1 Launch": [], "2 Launches": [], "3–4 Launches": [],
    "5–9 Launches": [], "10+ Launches": [],
}
for r in unique.values():
    p  = int(r["posts_count"] or 1)
    fl = int(r["followers_count"] or 0)
    if p == 1:    launch_buckets["1 Launch"].append(fl)
    elif p == 2:  launch_buckets["2 Launches"].append(fl)
    elif p <= 4:  launch_buckets["3–4 Launches"].append(fl)
    elif p <= 9:  launch_buckets["5–9 Launches"].append(fl)
    else:         launch_buckets["10+ Launches"].append(fl)

labels = list(launch_buckets.keys())
avgs   = [sum(v) / len(v) if v else 0 for v in launch_buckets.values()]
counts = [len(v) for v in launch_buckets.values()]

cmap_colors = [
    "#BFDBFE", "#93C5FD", "#60A5FA", "#3B82F6", "#1D4ED8"
]

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(labels, avgs, color=cmap_colors, width=0.6, edgecolor="white")

for bar, avg, n in zip(bars, avgs, counts):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5,
            f"{avg:,.0f}", ha="center", fontsize=10.5, fontweight="bold", color="#111827")
    ax.text(bar.get_x() + bar.get_width() / 2, -45,
            f"{n:,} products", ha="center", fontsize=8, color="#6B7280")

ax.set_ylabel("Average Followers per Product", labelpad=8)
ax.set_title("Does Persistence Pay Off?\nAverage Audience Size by Number of ProductHunt Launches",
             fontsize=14, fontweight="bold", pad=14)
ax.set_ylim(-55, max(avgs) * 1.22)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
fig.tight_layout()
save(fig, "04_launch_frequency_vs_audience.png")


# ===========================================================================
# CHART 5 — Category Quality Leaders (avg rating, min 20 reviewed products)
# ===========================================================================
print("Chart 5: Category quality leaders …")

cat_avg_rating = {
    slug: sum(v) / len(v)
    for slug, v in cat_ratings.items()
    if len(v) >= 20
}
top15_quality = sorted(cat_avg_rating.items(), key=lambda x: -x[1])[:15]
labels  = [cat_label(s) for s, _ in top15_quality]
values  = [v for _, v in top15_quality]
n_prods = [len(cat_ratings[s]) for s, _ in top15_quality]

fig, ax = plt.subplots(figsize=(12, 7))
bars = ax.barh(labels[::-1], values[::-1], color=PALETTE_GOOD, height=0.65)

for bar, val, n in zip(bars, values[::-1], n_prods[::-1]):
    ax.text(bar.get_width() + 0.002, bar.get_y() + bar.get_height() / 2,
            f"{val:.3f}  ({n} products)", va="center", fontsize=9, color="#374151")

ax.set_xlabel("Average Review Rating (out of 5.0)", labelpad=8)
ax.set_title("Which Categories Deliver Consistent Quality?\nTop 15 by Average Review Rating (Min. 20 Reviewed Products)",
             fontsize=14, fontweight="bold", pad=14)
ax.set_xlim(4.6, 5.02)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.2f}"))
fig.tight_layout()
save(fig, "05_category_quality_leaders.png")


# ===========================================================================
# CHART 6 — Top Products: Market Leaders by Community Size
# ===========================================================================
print("Chart 6: Top products by followers …")

top15_prods = sorted(unique.values(), key=lambda r: int(r["followers_count"] or 0), reverse=True)[:15]
names     = [r["name"][:35] for r in top15_prods]
followers = [int(r["followers_count"] or 0) / 1_000 for r in top15_prods]
ratings   = [float(r["reviews_rating"] or 0) for r in top15_prods]

# Color by rating
def rating_color(rt):
    if rt >= 4.7: return PALETTE_GOOD
    if rt >= 4.0: return PALETTE_ACCENT
    return PALETTE_NEUTRAL

bar_colors = [rating_color(rt) for rt in ratings]

fig, ax = plt.subplots(figsize=(12, 7))
bars = ax.barh(names[::-1], followers[::-1], color=bar_colors[::-1], height=0.65)

for bar, val, rt in zip(bars, followers[::-1], ratings[::-1]):
    label = f"{val:,.1f}K   ★{rt:.2f}" if rt > 0 else f"{val:,.1f}K"
    ax.text(bar.get_width() + 0.4, bar.get_y() + bar.get_height() / 2,
            label, va="center", fontsize=9, color="#374151")

ax.set_xlabel("Followers (Thousands)", labelpad=8)
ax.set_title("Who Are the Market Leaders?\nTop 15 Products by Community Size",
             fontsize=14, fontweight="bold", pad=14)
ax.set_xlim(0, max(followers) * 1.2)

legend_patches = [
    mpatches.Patch(color=PALETTE_GOOD,    label="Rating ≥ 4.7"),
    mpatches.Patch(color=PALETTE_ACCENT,  label="Rating 4.0–4.7"),
    mpatches.Patch(color=PALETTE_NEUTRAL, label="Rating < 4.0 or unrated"),
]
ax.legend(handles=legend_patches, loc="lower right", fontsize=9)
fig.tight_layout()
save(fig, "06_top_products_by_community.png")


# ===========================================================================
# CHART 7 — Review Engagement Gap: Reviewed vs Unreviewed (Top 20 categories)
# ===========================================================================
print("Chart 7: Review engagement gap …")

top20_by_count = [slug for slug, _ in cat_counts.most_common(20)]
labels   = [cat_label(s) for s in top20_by_count]
reviewed = [cat_reviewed[s] for s in top20_by_count]
total    = [cat_counts[s]   for s in top20_by_count]
unreviewed = [t - r for t, r in zip(total, reviewed)]
pct_rev    = [100 * r / t   for r, t in zip(reviewed, total)]

x = np.arange(len(labels))
fig, ax = plt.subplots(figsize=(14, 6))

b1 = ax.bar(x, reviewed,   color=PALETTE_MAIN,    width=0.6, label="Reviewed products")
b2 = ax.bar(x, unreviewed, color="#DBEAFE",         width=0.6,
            bottom=reviewed, label="Unreviewed products")

for i, (pct, tot) in enumerate(zip(pct_rev, total)):
    ax.text(i, tot + 30, f"{pct:.0f}%", ha="center", fontsize=7.5,
            fontweight="bold", color=PALETTE_MAIN)

ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=38, ha="right", fontsize=8.5)
ax.set_ylabel("Number of Products", labelpad=8)
ax.set_title("How Engaged Are Each Category's Communities?\nReviewed vs. Unreviewed Products — Top 20 Categories by Volume",
             fontsize=14, fontweight="bold", pad=14)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax.legend(loc="upper right", fontsize=9)
fig.tight_layout()
save(fig, "07_review_engagement_gap.png")


# ===========================================================================
# CHART 8 — Market Saturation vs Engagement Rate (scatter-style grouped bar)
# ===========================================================================
print("Chart 8: Market saturation map …")

# Pick 12 representative categories with 200+ products
selected = [
    "productivity", "engineering-development", "design-creative",
    "marketing-sales", "llms", "ai-chatbots", "automation",
    "team-collaboration", "no-code-platforms", "finance",
    "ai-coding-agents", "health-fitness",
]
selected = [s for s in selected if s in cat_counts and cat_counts[s] >= 100]

labels   = [cat_label(s) for s in selected]
n_prods  = [cat_counts[s] / 100 for s in selected]            # in hundreds
eng_rate = [100 * cat_reviewed[s] / cat_counts[s] for s in selected]  # %

x = np.arange(len(selected))
width = 0.38

fig, ax1 = plt.subplots(figsize=(14, 6))
ax2 = ax1.twinx()
ax2.spines["top"].set_visible(False)

b1 = ax1.bar(x - width / 2, n_prods,  width=width, color=PALETTE_MAIN,
             label="Products (hundreds)", alpha=0.9)
b2 = ax2.bar(x + width / 2, eng_rate, width=width, color=PALETTE_ACCENT,
             label="Review rate (%)", alpha=0.9)

ax1.set_xticks(x)
ax1.set_xticklabels(labels, rotation=38, ha="right", fontsize=9)
ax1.set_ylabel("Number of Products (Hundreds)", color=PALETTE_MAIN, labelpad=8)
ax2.set_ylabel("% of Products with at Least 1 Review", color=PALETTE_ACCENT, labelpad=8)
ax1.tick_params(axis="y", labelcolor=PALETTE_MAIN)
ax2.tick_params(axis="y", labelcolor=PALETTE_ACCENT)
ax2.set_ylim(0, 70)

ax1.set_title("Saturation vs. Engagement: How Competitive Are Key Markets?\n"
              "Bars: Number of products  |  Orange: % of products actively reviewed",
              fontsize=13, fontweight="bold", pad=14)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=9)
fig.tight_layout()
save(fig, "08_saturation_vs_engagement.png")


# ===========================================================================
# CHART 9 — AI vs Traditional: Opportunity Score Comparison
# ===========================================================================
print("Chart 9: AI vs Traditional opportunity …")

ai_cats = {
    "ai-chatbots":          "AI Chatbots",
    "llms":                 "LLMs",
    "ai-coding-agents":     "AI Coding Agents",
    "vibe-coding":          "Vibe Coding",
    "ai-meeting-notetakers":"AI Notetakers",
    "ai-voice-agents":      "AI Voice Agents",
    "ai-agents":            "AI Agents",
    "automation":           "Automation",
}
trad_cats = {
    "productivity":             "Productivity",
    "engineering-development":  "Engineering & Dev",
    "design-creative":          "Design & Creative",
    "marketing-sales":          "Marketing & Sales",
    "finance":                  "Finance",
    "health-fitness":           "Health & Fitness",
    "team-collaboration":       "Team Collaboration",
    "project-management":       "Project Management",
}

def opp_score(slug):
    if cat_counts[slug] == 0:
        return 0
    return sum(cat_followers[slug]) / cat_counts[slug]

ai_scores   = [(name, opp_score(slug)) for slug, name in ai_cats.items()  if slug in cat_counts]
trad_scores = [(name, opp_score(slug)) for slug, name in trad_cats.items() if slug in cat_counts]

ai_scores.sort(key=lambda x: -x[1])
trad_scores.sort(key=lambda x: -x[1])

fig, axes = plt.subplots(1, 2, figsize=(15, 6), sharey=False)

for ax, data, color, title in [
    (axes[0], ai_scores,   PALETTE_GOOD, "AI-Native Categories"),
    (axes[1], trad_scores, PALETTE_MAIN, "Traditional Categories"),
]:
    names  = [d[0] for d in data]
    scores = [d[1] for d in data]
    bars = ax.barh(names[::-1], scores[::-1], color=color, height=0.6)
    for bar, val in zip(bars, scores[::-1]):
        ax.text(bar.get_width() + 3, bar.get_y() + bar.get_height() / 2,
                f"{val:,.0f}", va="center", fontsize=9, color="#374151")
    ax.set_xlabel("Avg Followers per Product", labelpad=6)
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xlim(0, max(scores) * 1.22)
    ax.tick_params(axis="y", labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", alpha=0.3, linestyle="--")

fig.suptitle("AI vs. Traditional Categories: Where Is the Bigger Opportunity?\n"
             "Average audience per product — higher = more demand relative to competition",
             fontsize=13, fontweight="bold", y=1.02)
fig.tight_layout()
save(fig, "09_ai_vs_traditional_opportunity.png")


# ===========================================================================
# Done
# ===========================================================================
print(f"\nAll charts saved to {CHARTS_DIR}/")
print(f"  01_market_size_by_category.png")
print(f"  02_opportunity_score_per_product.png")
print(f"  03_quality_vs_traction.png")
print(f"  04_launch_frequency_vs_audience.png")
print(f"  05_category_quality_leaders.png")
print(f"  06_top_products_by_community.png")
print(f"  07_review_engagement_gap.png")
print(f"  08_saturation_vs_engagement.png")
print(f"  09_ai_vs_traditional_opportunity.png")
