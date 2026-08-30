"""Deterministic headless chart rendering using Matplotlib & Seaborn."""

import base64
import io
from pathlib import Path
from typing import List, Optional, Tuple, Union
import matplotlib
matplotlib.use("Agg")  # Enforce headless rendering
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

from .chart_model import ChartSeriesSpec, ChartTypeEnum

SHEETSLY_PALETTE = [
    "#4f46e5",  # Indigo 600
    "#10b981",  # Emerald 500
    "#f59e0b",  # Amber 500
    "#0ea5e9",  # Sky 500
    "#8b5cf6",  # Violet 500
    "#f43f5e",  # Rose 500
    "#14b8a6",  # Teal 500
    "#64748b",  # Slate 500
]


class ChartRenderer:
    """Renders high-quality static chart artifacts deterministically."""

    @classmethod
    def render_to_file(
        cls,
        chart_type: ChartTypeEnum,
        title: str,
        x_categories: List[str],
        series: List[ChartSeriesSpec],
        x_axis_label: Optional[str],
        y_axis_label: Optional[str],
        output_file_path: Path,
        include_base64: bool = False,
    ) -> Optional[str]:
        """
        Renders chart to PNG file on disk and optionally returns base64 string.
        """
        output_file_path.parent.mkdir(parents=True, exist_ok=True)

        fig, ax = plt.subplots(figsize=(9, 5.5), dpi=150)
        fig.patch.set_facecolor("#ffffff")
        ax.set_facecolor("#ffffff")

        # Apply grid
        ax.grid(True, linestyle="--", linewidth=0.6, color="#e2e8f0", alpha=0.8, zorder=0)
        ax.set_axisbelow(True)

        # -------------------------------------------------------------
        # 1. BAR & COLUMN CHART
        # -------------------------------------------------------------
        if chart_type in {ChartTypeEnum.BAR, ChartTypeEnum.COLUMN}:
            x_indices = np.arange(len(x_categories))
            num_series = len(series)
            bar_width = 0.8 / max(num_series, 1)

            for idx, s in enumerate(series):
                offset = (idx - (num_series - 1) / 2) * bar_width
                color = s.color or SHEETSLY_PALETTE[idx % len(SHEETSLY_PALETTE)]
                clean_vals = [float(v) if v is not None else 0.0 for v in s.values]
                bars = ax.bar(
                    x_indices + offset,
                    clean_vals,
                    width=bar_width * 0.9,
                    label=s.name if num_series > 1 else None,
                    color=color,
                    zorder=3,
                )

            ax.set_xticks(x_indices)
            ax.set_xticklabels(x_categories)

        # -------------------------------------------------------------
        # 2. LINE CHART
        # -------------------------------------------------------------
        elif chart_type == ChartTypeEnum.LINE:
            x_indices = np.arange(len(x_categories))
            for idx, s in enumerate(series):
                color = s.color or SHEETSLY_PALETTE[idx % len(SHEETSLY_PALETTE)]
                clean_vals = [float(v) if v is not None else np.nan for v in s.values]
                ax.plot(
                    x_indices,
                    clean_vals,
                    marker="o",
                    markersize=6,
                    linewidth=2.4,
                    label=s.name if len(series) > 1 else None,
                    color=color,
                    zorder=4,
                )

            ax.set_xticks(x_indices)
            ax.set_xticklabels(x_categories)

        # -------------------------------------------------------------
        # 3. AREA CHART
        # -------------------------------------------------------------
        elif chart_type == ChartTypeEnum.AREA:
            x_indices = np.arange(len(x_categories))
            for idx, s in enumerate(series):
                color = s.color or SHEETSLY_PALETTE[idx % len(SHEETSLY_PALETTE)]
                clean_vals = [float(v) if v is not None else 0.0 for v in s.values]
                ax.plot(x_indices, clean_vals, linewidth=2.0, color=color, zorder=4)
                ax.fill_between(x_indices, 0, clean_vals, color=color, alpha=0.3, label=s.name if len(series) > 1 else None, zorder=3)

            ax.set_xticks(x_indices)
            ax.set_xticklabels(x_categories)

        # -------------------------------------------------------------
        # 4. PIE / DONUT CHART
        # -------------------------------------------------------------
        elif chart_type == ChartTypeEnum.PIE:
            ax.axis("off")  # Disable Cartesian axis for Pie
            s = series[0]
            clean_vals = [float(v) if v is not None else 0.0 for v in s.values]
            total_sum = sum(clean_vals)
            if total_sum <= 0:
                clean_vals = [1.0] * max(len(clean_vals), 1)
                total_sum = float(len(clean_vals))

            colors = [SHEETSLY_PALETTE[i % len(SHEETSLY_PALETTE)] for i in range(len(x_categories))]

            def dynamic_autopct(pct):
                # Hide percentage if slice is too small (< 3.5%) to prevent overflow/clipping
                if pct < 3.5:
                    return ""
                return f"{pct:.1f}%"

            use_legend = len(x_categories) > 4 or any(len(str(c)) > 10 for c in x_categories)

            wedges, texts, autotexts = ax.pie(
                clean_vals,
                labels=None if use_legend else x_categories,
                labeldistance=1.05,
                autopct=dynamic_autopct,
                pctdistance=0.75,
                startangle=140,
                colors=colors,
                wedgeprops=dict(width=0.48, edgecolor="white", linewidth=2),
                textprops=dict(color="#1e293b", fontsize=9, fontweight="medium"),
            )
            for autotext in autotexts:
                autotext.set_color("#ffffff")
                autotext.set_fontweight("bold")
                autotext.set_fontsize(9)

            if use_legend:
                legend_labels = [
                    f"{cat} ({(val / total_sum * 100):.1f}%)" if val > 0 else str(cat)
                    for cat, val in zip(x_categories, clean_vals)
                ]
                ax.legend(
                    wedges,
                    legend_labels,
                    title=x_axis_label or "Categories",
                    loc="center left",
                    bbox_to_anchor=(0.95, 0.5),
                    frameon=True,
                    facecolor="#f8fafc",
                    edgecolor="#e2e8f0",
                    fontsize=8.5,
                    title_fontsize=9,
                )

        # -------------------------------------------------------------
        # 5. SCATTER CHART
        # -------------------------------------------------------------
        elif chart_type == ChartTypeEnum.SCATTER:
            s = series[0]
            try:
                x_nums = [float(x) for x in x_categories]
            except (ValueError, TypeError):
                x_nums = list(range(len(x_categories)))
            y_nums = [float(v) if v is not None else 0.0 for v in s.values]
            color = SHEETSLY_PALETTE[0]

            ax.scatter(x_nums, y_nums, color=color, s=70, alpha=0.85, edgecolors="#ffffff", linewidth=1.5, zorder=4)

        # -------------------------------------------------------------
        # 6. HISTOGRAM
        # -------------------------------------------------------------
        elif chart_type == ChartTypeEnum.HISTOGRAM:
            s = series[0]
            clean_vals = [float(v) for v in s.values if v is not None]
            color = SHEETSLY_PALETTE[0]

            ax.hist(
                clean_vals,
                bins="auto",
                color=color,
                edgecolor="white",
                linewidth=1.2,
                alpha=0.85,
                zorder=3,
            )

        # -------------------------------------------------------------
        # General Styling & Labeling
        # -------------------------------------------------------------
        if chart_type != ChartTypeEnum.PIE:
            if x_axis_label:
                ax.set_xlabel(x_axis_label, fontsize=10, fontweight="bold", color="#475569", labelpad=8)
            if y_axis_label:
                ax.set_ylabel(y_axis_label, fontsize=10, fontweight="bold", color="#475569", labelpad=8)

            # Format Y tick numbers with commas
            ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))

            # Tick formatting
            ax.tick_params(colors="#64748b", labelsize=9)
            for spine in ax.spines.values():
                spine.set_color("#cbd5e1")
                spine.set_linewidth(0.8)

            # Rotate X labels if long or numerous
            if len(x_categories) > 5 or any(len(str(c)) > 8 for c in x_categories):
                plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment="right")

            # Legend if multiple series
            if len(series) > 1:
                ax.legend(frameon=True, facecolor="#f8fafc", edgecolor="#e2e8f0", fontsize=9)

        # Title
        ax.set_title(title, fontsize=13, fontweight="bold", color="#0f172a", pad=14)

        plt.tight_layout()

        # Save to file
        plt.savefig(output_file_path, format="png", bbox_inches="tight")

        base64_str = None
        if include_base64:
            buf = io.BytesIO()
            plt.savefig(buf, format="png", bbox_inches="tight")
            buf.seek(0)
            base64_str = base64.b64encode(buf.read()).decode("utf-8")

        plt.close(fig)
        return base64_str
