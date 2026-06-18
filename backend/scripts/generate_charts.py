"""
generate_charts.py
==================
Chạy script này để sinh toàn bộ biểu đồ và file kết quả phục vụ báo cáo.

Output (trong thư mục reports/charts/):
    - label_distribution.png         : Phân bổ nhãn SAFE/SUSPICIOUS/SCAM
    - source_distribution.png        : Phân bổ nguồn dữ liệu
    - confusion_matrix.png           : Confusion matrix heatmap
    - metrics_by_class.png           : Precision / Recall / F1 theo từng lớp
    - fairness_heatmap.png           : Tỷ lệ SCAM detection theo vùng miền × noise
    - robustness_bar.png             : Accuracy theo loại noise
    - report_summary.csv             : Bảng tổng hợp metrics

Cách chạy:
    cd ScamDetector-main/backend
    python scripts/generate_charts.py

Yêu cầu:
    pip install matplotlib seaborn scikit-learn pandas joblib
"""

import json
import warnings
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score

warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).resolve().parents[1]
DATASET_DIR = BASE_DIR / "datasets" / "processed"
ARTIFACT_DIR = BASE_DIR / "ml_artifacts"
REPORT_DIR = BASE_DIR / "reports"
CHART_DIR = REPORT_DIR / "charts"
CHART_DIR.mkdir(parents=True, exist_ok=True)

# Style
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.labelsize": 12,
    "figure.dpi": 150,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.2,
})
COLORS = {"SCAM": "#D32F2F", "SAFE": "#388E3C", "SUSPICIOUS": "#F57C00"}
PALETTE = [COLORS["SCAM"], COLORS["SAFE"], COLORS["SUSPICIOUS"]]


# ─── LOAD ──────────────────────────────────────────────────────────────────────

def load_data():
    full_df = pd.read_csv(DATASET_DIR / "scam_dataset_full.csv")
    test_df = pd.read_csv(DATASET_DIR / "test.csv")

    with open(ARTIFACT_DIR / "metrics_v1.json", "r", encoding="utf-8") as f:
        metrics = json.load(f)

    model = joblib.load(ARTIFACT_DIR / "scam_detector_pipeline_v1.joblib")

    # Fairness + robustness test suites
    fairness_path = BASE_DIR / "datasets" / "test_suites" / "fairness_test.csv"
    robustness_path = BASE_DIR / "datasets" / "test_suites" / "robustness_test.csv"

    fairness_df = pd.read_csv(fairness_path) if fairness_path.exists() else None
    robustness_df = pd.read_csv(robustness_path) if robustness_path.exists() else None

    return full_df, test_df, metrics, model, fairness_df, robustness_df


# ─── 1. LABEL DISTRIBUTION ────────────────────────────────────────────────────

def plot_label_distribution(full_df):
    counts = full_df["label"].value_counts().reindex(["SCAM", "SAFE", "SUSPICIOUS"])
    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(counts.index, counts.values,
                  color=[COLORS[l] for l in counts.index],
                  edgecolor="white", linewidth=0.8, width=0.5)

    for bar, val in zip(bars, counts.values):
        pct = val / counts.sum() * 100
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 12,
                f"{val}\n({pct:.1f}%)", ha="center", va="bottom", fontsize=11, fontweight="bold")

    ax.set_title("Phân bổ nhãn trong Dataset (n=1,623)")
    ax.set_ylabel("Số mẫu")
    ax.set_ylim(0, max(counts.values) * 1.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig(CHART_DIR / "label_distribution.png")
    plt.close()
    print("✅ label_distribution.png")


# ─── 2. SOURCE DISTRIBUTION ────────────────────────────────────────────────────

def plot_source_distribution(full_df):
    source_map = {
        "vietnamese_synthetic": "Vietnamese\nSynthetic",
        "self_created_long_context_based_on_public_warning_taxonomy": "Long-context\nSynthetic",
        "self_created_long_context_hard_negative": "Hard\nNegative",
        "meaning_preserving_adapted_from_mendeley_sms_phishing": "Mendeley\n(adapted)",
        "meaning_preserving_adapted_from_reportsmishing_imc25": "ReportSmishing\n(adapted)",
        "meaning_preserving_adapted_from_uci_sms_spam_collection": "UCI SMS\n(adapted)",
    }
    counts = full_df["source"].value_counts()
    labels = [source_map.get(s, s) for s in counts.index]
    adapted_sources = [s for s in counts.index if "adapted" in s]
    bar_colors = ["#D32F2F" if s in adapted_sources else "#1565C0" for s in counts.index]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(labels, counts.values, color=bar_colors, edgecolor="white", linewidth=0.8)

    for bar, val in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5,
                str(val), ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.set_title("Phân bổ nguồn dữ liệu\n(Đỏ = nguồn public-adapted cần loại bỏ)")
    ax.set_ylabel("Số mẫu")
    ax.set_ylim(0, max(counts.values) * 1.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    patch_vi = mpatches.Patch(color="#1565C0", label="Nguồn tiếng Việt (giữ lại)")
    patch_en = mpatches.Patch(color="#D32F2F", label="Public-adapted từ tiếng Anh (loại bỏ)")
    ax.legend(handles=[patch_vi, patch_en], loc="upper right")

    plt.tight_layout()
    plt.savefig(CHART_DIR / "source_distribution.png")
    plt.close()
    print("✅ source_distribution.png")


# ─── 3. CONFUSION MATRIX ──────────────────────────────────────────────────────

def plot_confusion_matrix(metrics):
    cm = np.array(metrics["test_metrics"]["confusion_matrix"])
    labels = metrics["test_metrics"]["labels"]

    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=labels, yticklabels=labels,
                linewidths=0.5, linecolor="white", ax=ax, cbar_kws={"shrink": 0.8},
                annot_kws={"size": 14, "weight": "bold"})

    ax.set_title(f"Confusion Matrix – Test Set\n(Accuracy: {metrics['test_metrics']['accuracy']:.4f})")
    ax.set_ylabel("Nhãn thực tế")
    ax.set_xlabel("Nhãn dự đoán")
    ax.tick_params(axis="both", labelsize=11)
    plt.tight_layout()
    plt.savefig(CHART_DIR / "confusion_matrix.png")
    plt.close()
    print("✅ confusion_matrix.png")


# ─── 4. METRICS BY CLASS ──────────────────────────────────────────────────────

def plot_metrics_by_class(metrics):
    labels = ["SAFE", "SUSPICIOUS", "SCAM"]
    cr = metrics["test_metrics"]["classification_report"]

    precision = [cr[l]["precision"] for l in labels]
    recall    = [cr[l]["recall"]    for l in labels]
    f1        = [cr[l]["f1-score"]  for l in labels]

    x = np.arange(len(labels))
    width = 0.25

    fig, ax = plt.subplots(figsize=(8, 5))
    b1 = ax.bar(x - width, precision, width, label="Precision", color="#1565C0", edgecolor="white")
    b2 = ax.bar(x,          recall,   width, label="Recall",    color="#2E7D32", edgecolor="white")
    b3 = ax.bar(x + width,  f1,       width, label="F1-score",  color="#E65100", edgecolor="white")

    for bars in [b1, b2, b3]:
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                    f"{bar.get_height():.2f}", ha="center", va="bottom", fontsize=9)

    ax.set_title("Precision / Recall / F1 theo từng lớp")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=12)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("Score")
    ax.legend()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.axhline(y=0.95, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)
    ax.text(2.6, 0.955, "0.95", color="gray", fontsize=9)
    plt.tight_layout()
    plt.savefig(CHART_DIR / "metrics_by_class.png")
    plt.close()
    print("✅ metrics_by_class.png")


# ─── 5. FAIRNESS HEATMAP ──────────────────────────────────────────────────────

def plot_fairness_heatmap(model, fairness_df):
    if fairness_df is None:
        print("⚠️  Không tìm thấy fairness_test.csv, bỏ qua biểu đồ fairness.")
        return

    required = {"text", "label", "region_variant", "noise_type"}
    if not required.issubset(fairness_df.columns):
        print(f"⚠️  fairness_test.csv thiếu cột: {required - set(fairness_df.columns)}, bỏ qua.")
        return

    fairness_df = fairness_df.dropna(subset=["text", "label", "region_variant", "noise_type"])
    fairness_df["predicted"] = model.predict(fairness_df["text"].astype(str))
    fairness_df["correct"] = (fairness_df["predicted"] == fairness_df["label"]).astype(int)

    # Pivot: region × noise accuracy
    pivot = fairness_df.groupby(["region_variant", "noise_type"])["correct"].mean().unstack(fill_value=np.nan)

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.heatmap(pivot, annot=True, fmt=".2f", cmap="YlGn", ax=ax,
                linewidths=0.5, linecolor="white", vmin=0.7, vmax=1.0,
                cbar_kws={"label": "Accuracy", "shrink": 0.8},
                annot_kws={"size": 11})
    ax.set_title("Fairness – Accuracy theo Vùng miền × Loại nhiễu")
    ax.set_xlabel("Loại nhiễu (noise_type)")
    ax.set_ylabel("Vùng miền (region_variant)")
    plt.tight_layout()
    plt.savefig(CHART_DIR / "fairness_heatmap.png")
    plt.close()
    print("✅ fairness_heatmap.png")


# ─── 6. ROBUSTNESS BAR ────────────────────────────────────────────────────────

def plot_robustness_bar(model, robustness_df):
    if robustness_df is None:
        print("⚠️  Không tìm thấy robustness_test.csv, bỏ qua biểu đồ robustness.")
        return

    required = {"text", "label", "noise_type"}
    if not required.issubset(robustness_df.columns):
        print(f"⚠️  robustness_test.csv thiếu cột: {required - set(robustness_df.columns)}, bỏ qua.")
        return

    robustness_df = robustness_df.dropna(subset=["text", "label", "noise_type"])
    robustness_df["predicted"] = model.predict(robustness_df["text"].astype(str))
    robustness_df["correct"] = (robustness_df["predicted"] == robustness_df["label"]).astype(int)

    acc_by_noise = robustness_df.groupby("noise_type")["correct"].mean().sort_values(ascending=False)

    colors = ["#D32F2F" if v < 0.85 else "#388E3C" for v in acc_by_noise.values]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(acc_by_noise.index, acc_by_noise.values, color=colors, edgecolor="white", width=0.5)

    for bar, val in zip(bars, acc_by_noise.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                f"{val:.2f}", ha="center", va="bottom", fontsize=11, fontweight="bold")

    ax.set_title("Robustness – Accuracy theo loại nhiễu ngôn ngữ")
    ax.set_ylabel("Accuracy")
    ax.set_ylim(0, 1.12)
    ax.axhline(y=0.85, color="gray", linestyle="--", linewidth=1, alpha=0.7)
    ax.text(len(acc_by_noise) - 0.5, 0.855, "Ngưỡng 85%", color="gray", fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig(CHART_DIR / "robustness_bar.png")
    plt.close()
    print("✅ robustness_bar.png")


# ─── 7. SUMMARY CSV ───────────────────────────────────────────────────────────

def save_summary_csv(metrics):
    cr = metrics["test_metrics"]["classification_report"]
    labels = ["SAFE", "SUSPICIOUS", "SCAM"]

    rows = []
    for label in labels:
        rows.append({
            "Class": label,
            "Precision": round(cr[label]["precision"], 4),
            "Recall": round(cr[label]["recall"], 4),
            "F1-score": round(cr[label]["f1-score"], 4),
            "Support": int(cr[label]["support"]),
        })
    rows.append({
        "Class": "Accuracy",
        "Precision": "",
        "Recall": "",
        "F1-score": round(metrics["test_metrics"]["accuracy"], 4),
        "Support": int(cr["macro avg"]["support"]),
    })

    summary_df = pd.DataFrame(rows)
    out_path = REPORT_DIR / "report_summary.csv"
    summary_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"✅ report_summary.csv\n")
    print(summary_df.to_string(index=False))


# ─── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("Đang tải dữ liệu và model...\n")
    full_df, test_df, metrics, model, fairness_df, robustness_df = load_data()

    print(f"Dataset: {len(full_df)} mẫu | Test set: {len(test_df)} mẫu\n")
    print("Đang sinh biểu đồ...")
    print("-" * 40)

    plot_label_distribution(full_df)
    plot_source_distribution(full_df)
    plot_confusion_matrix(metrics)
    plot_metrics_by_class(metrics)
    plot_fairness_heatmap(model, fairness_df)
    plot_robustness_bar(model, robustness_df)
    save_summary_csv(metrics)

    print("\n" + "=" * 50)
    print(f"XONG — Tất cả output trong: {REPORT_DIR}")
    print(f"Biểu đồ: {CHART_DIR}")
    print("=" * 50)


if __name__ == "__main__":
    main()