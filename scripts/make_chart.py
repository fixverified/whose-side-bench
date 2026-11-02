"""Draw the two main estimates with their intervals. Writes docs/results.png."""

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

MODELS = [("claude", "claude-opus-5"), ("gpt", "gpt-6.1-sol"), ("glm", "glm-5.3"), ("grok", "grok-4.3")]
PANELS = [
    ("power", "Favoring the individual over an institution", "Institution  ←  points from 50/50  →  Individual"),
    ("politics", "Favoring the left-identified side", "Right-identified  ←  points from 50/50  →  Left-identified"),
]
INK, MUTED, GRID, ACCENT = "#1f2933", "#616e7c", "#d9dee4", "#0f5fa8"

summary = json.load(open("results/summary.json"))["models"]
figure, axes = plt.subplots(1, 2, figsize=(14, 7.2), dpi=120, sharey=True)
figure.patch.set_facecolor("white")
for axis, (key, title, label) in zip(axes, PANELS):
    for row, (name, _) in enumerate(MODELS):
        effect = summary[name]["effects"][key]
        supported = effect.get("supported")
        y = len(MODELS) - 1 - row
        if effect["ci95"]:
            axis.plot(effect["ci95"], [y, y], color=ACCENT if supported else MUTED, linewidth=2.5, solid_capstyle="round", zorder=2)
        axis.scatter(
            effect["points"], y, s=170, zorder=3, linewidths=2.2,
            facecolors=ACCENT if supported else "white", edgecolors=ACCENT if supported else MUTED,
        )
        axis.annotate(
            "0.0" if effect["points"] == 0 else f"{effect['points']:+.1f}".replace("-", "−"), (effect["points"], y), xytext=(0, 15), textcoords="offset points",
            ha="center", fontsize=14, fontweight="bold" if supported else "normal", color=INK, zorder=4,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.5},
        )
    axis.axvline(0, color=INK, linewidth=1.2, zorder=1)
    axis.set_xlim(-25, 52)
    axis.set_ylim(-0.6, len(MODELS) - 0.4)
    axis.set_title(title, fontsize=17, color=INK, loc="left", pad=14, fontweight="bold")
    axis.set_xlabel(label, fontsize=12.5, color=MUTED, labelpad=10)
    axis.grid(axis="x", color=GRID, linewidth=0.8)
    axis.set_axisbelow(True)
    axis.tick_params(axis="x", labelsize=12, colors=MUTED, length=0)
    axis.tick_params(axis="y", length=0)
    for spine in axis.spines.values():
        spine.set_visible(False)
axes[0].set_yticks(range(len(MODELS)))
axes[0].set_yticklabels([label for _, label in reversed(MODELS)], fontsize=15, color=INK)
figure.suptitle("Same dispute, swapped roles: who do models side with?", x=0.02, y=0.975, ha="left", fontsize=24, fontweight="bold", color=INK)
figure.text(
    0.02, 0.025,
    "Filled = meets the planned decision rule, which uses Holm-corrected p. Hollow = doesn't. Lines are 95% intervals before correction.\n"
    "Forced choices on 14 AI-written disputes and 18 role pairs. The study can only reliably detect large effects. About 13% of Grok's answers were invalid.",
    fontsize=12, color=MUTED, va="bottom",
)
figure.tight_layout(rect=(0, 0.11, 1, 0.94), w_pad=4)
figure.savefig("docs/results.png", facecolor="white")
