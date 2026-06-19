"""
fix_dataset_and_retrain.py
==========================
Chạy script này để:
1. Xác nhận dataset đã loại bỏ hoàn toàn public-adapted sources
2. Tạo lại dataset_clean.csv từ merged Vietnamese-only dataset
3. Dùng lại split train/valid/test đã chia theo base_case_id
4. Retrain model v2 với dataset sạch
5. So sánh metrics trước/sau

Cách chạy:
    cd ScamDetector-main/backend
    python scripts/fix_dataset_and_retrain.py

Yêu cầu:
    pip install scikit-learn pandas joblib
"""

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.pipeline import FeatureUnion, Pipeline

BASE_DIR = Path(__file__).resolve().parents[1]
DATASET_DIR = BASE_DIR / "datasets" / "processed"
ARTIFACT_DIR = BASE_DIR / "ml_artifacts"
REPORT_DIR = BASE_DIR / "reports"
TEST_SUITE_DIR = BASE_DIR / "datasets" / "test_suites"

FULL_DATASET_PATH = DATASET_DIR / "scam_dataset_full.csv"
CLEAN_DATASET_PATH = DATASET_DIR / "scam_dataset_clean.csv"
CLEAN_TRAIN_PATH = DATASET_DIR / "train_clean.csv"
CLEAN_VALID_PATH = DATASET_DIR / "valid_clean.csv"
CLEAN_TEST_PATH = DATASET_DIR / "test_clean.csv"
TRAIN_PATH = DATASET_DIR / "train.csv"
VALID_PATH = DATASET_DIR / "valid.csv"
TEST_PATH = DATASET_DIR / "test.csv"

# Các source bị loại (dịch từ tiếng Anh)
REMOVED_SOURCES = [
    "meaning_preserving_adapted_from_mendeley_sms_phishing",
    "meaning_preserving_adapted_from_reportsmishing_imc25",
    "meaning_preserving_adapted_from_uci_sms_spam_collection",
]

ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ─── 1. LỌC DATASET ────────────────────────────────────────────────────────────

def filter_dataset():
    df = pd.read_csv(FULL_DATASET_PATH)

    print("=" * 60)
    print("STEP 1: LỌC DATASET")
    print("=" * 60)
    print(f"\nTổng mẫu ban đầu: {len(df)}")
    print("\nPhân bổ theo source (ban đầu):")
    print(df["source"].value_counts().to_string())

    removed = df[df["source"].isin(REMOVED_SOURCES)]
    clean_df = df[~df["source"].isin(REMOVED_SOURCES)].copy()

    print(f"\n>>> Public-adapted còn trong merged dataset: {len(removed)} mẫu")
    for src in REMOVED_SOURCES:
        count = len(removed[removed["source"] == src])
        print(f"    - {src}: {count} mẫu")

    if len(removed) > 0:
        raise ValueError(
            "Merged dataset vẫn còn public-adapted rows. "
            "Chạy scripts/merge_datasets.py sau khi bỏ public_adapted_vi.csv khỏi DATASET_FILES."
        )

    print(f"\nSố mẫu còn lại: {len(clean_df)}")
    print("\nPhân bổ label sau khi lọc:")
    print(clean_df["label"].value_counts().to_string())

    clean_df.to_csv(CLEAN_DATASET_PATH, index=False, encoding="utf-8-sig")
    print(f"\n✅ Đã lưu: {CLEAN_DATASET_PATH}")

    return clean_df


# ─── 2. LOAD CLEAN SPLITS ─────────────────────────────────────────────────────

def load_clean_splits():
    print("\n" + "=" * 60)
    print("STEP 2: LOAD TRAIN / VALID / TEST CLEAN SPLITS")
    print("=" * 60)

    train_df = pd.read_csv(TRAIN_PATH)
    valid_df = pd.read_csv(VALID_PATH)
    test_df = pd.read_csv(TEST_PATH)

    for name, df in [("train", train_df), ("valid", valid_df), ("test", test_df)]:
        leaked = df[df["source"].isin(REMOVED_SOURCES)]
        if len(leaked) > 0:
            raise ValueError(f"{name}.csv còn {len(leaked)} public-adapted rows")

    train_like_base_cases = set(pd.concat([train_df, valid_df])["base_case_id"].astype(str))
    test_base_cases = set(test_df["base_case_id"].astype(str))
    overlap = train_like_base_cases & test_base_cases
    if overlap:
        raise ValueError(f"Clean test split leaks {len(overlap)} base_case_id values from train/valid")

    print(f"\nTrain: {len(train_df)} mẫu")
    print(train_df["label"].value_counts().to_string())
    print(f"\nValid: {len(valid_df)} mẫu")
    print(valid_df["label"].value_counts().to_string())
    print(f"\nTest:  {len(test_df)} mẫu")
    print(test_df["label"].value_counts().to_string())

    train_df.to_csv(CLEAN_TRAIN_PATH, index=False, encoding="utf-8-sig")
    valid_df.to_csv(CLEAN_VALID_PATH, index=False, encoding="utf-8-sig")
    test_df.to_csv(CLEAN_TEST_PATH, index=False, encoding="utf-8-sig")

    print(f"\n✅ Đã lưu bản sao train/valid/test clean")

    return train_df, valid_df, test_df


# ─── 3. BUILD MODEL ────────────────────────────────────────────────────────────

def build_model():
    word_vectorizer = TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 2),
        min_df=1,
        max_features=25000,
        lowercase=True,
    )
    char_vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=1,
        max_features=35000,
        lowercase=True,
    )
    features = FeatureUnion([
        ("word_tfidf", word_vectorizer),
        ("char_tfidf", char_vectorizer),
    ])
    classifier = LogisticRegression(
        max_iter=3000,
        class_weight="balanced",
        solver="liblinear",
        random_state=42,
    )
    return Pipeline([("features", features), ("classifier", classifier)])


# ─── 4. RETRAIN + EVALUATE ─────────────────────────────────────────────────────

def retrain_and_evaluate(train_df, valid_df, test_df):
    print("\n" + "=" * 60)
    print("STEP 3: RETRAIN MODEL")
    print("=" * 60)

    train_full = pd.concat([train_df, valid_df], ignore_index=True)
    X_train, y_train = train_full["text"].astype(str), train_full["label"].astype(str)
    X_test, y_test = test_df["text"].astype(str), test_df["label"].astype(str)

    print(f"\nTraining với {len(train_full)} mẫu...")
    model = build_model()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    labels = ["SAFE", "SUSPICIOUS", "SCAM"]

    print("\n========== TEST RESULT (CLEAN DATASET) ==========")
    print(f"Accuracy: {round(accuracy, 4)}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, labels=labels, zero_division=0))
    print("Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    print(labels)
    print(cm)

    responsible_ai_metrics = evaluate_responsible_ai_suites(model, train_df, valid_df)

    # Save model + metrics
    model_path = ARTIFACT_DIR / "scam_detector_pipeline_v2_clean.joblib"
    joblib.dump(model, model_path)

    report_dict = classification_report(y_test, y_pred, labels=labels, output_dict=True, zero_division=0)
    metrics = {
        "model_name": "TF-IDF word+char ngram + LogisticRegression (Clean Dataset)",
        "dataset": {
            "total_after_filter": len(train_df) + len(valid_df) + len(test_df),
            "public_adapted_rows_in_training_dataset": 0,
            "train_rows": len(train_df),
            "valid_rows": len(valid_df),
            "test_rows": len(test_df),
        },
        "removed_sources": REMOVED_SOURCES,
        "test_metrics": {
            "accuracy": accuracy,
            "labels": labels,
            "classification_report": report_dict,
            "confusion_matrix": cm.tolist(),
        },
        "responsible_ai_test_suites": responsible_ai_metrics,
        "notes": [
            "Dataset cleaned at merge step: public-adapted English-derived sources are excluded entirely.",
            "Splits are grouped by base_case_id to avoid train/test leakage across variants.",
            "Robustness suite is generated from held-out test rows with new adversarial obfuscation transforms.",
            "SCAM recall is the primary metric — zero miss rate for HIGH risk scams.",
        ],
    }

    metrics_path = ARTIFACT_DIR / "metrics_v2_clean.json"
    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Model saved: {model_path}")
    print(f"✅ Metrics saved: {metrics_path}")

    return model, metrics


def evaluate_responsible_ai_suites(model, train_df, valid_df):
    train_like_base_cases = set(pd.concat([train_df, valid_df])["base_case_id"].astype(str))
    suite_specs = {
        "fairness": TEST_SUITE_DIR / "fairness_test.csv",
        "robustness": TEST_SUITE_DIR / "robustness_test.csv",
    }
    results = {}

    for suite_name, suite_path in suite_specs.items():
        if not suite_path.exists():
            continue

        suite_df = pd.read_csv(suite_path)
        overlap = len(set(suite_df["base_case_id"].astype(str)) & train_like_base_cases)
        y_true = suite_df["label"].astype(str)
        y_pred = model.predict(suite_df["text"].astype(str))
        suite_accuracy = accuracy_score(y_true, y_pred)

        by_noise = {}
        if "noise_type" in suite_df.columns:
            for noise_type, group in suite_df.groupby("noise_type"):
                group_pred = model.predict(group["text"].astype(str))
                by_noise[str(noise_type)] = accuracy_score(group["label"].astype(str), group_pred)

        by_region = {}
        if "region_variant" in suite_df.columns:
            for region, group in suite_df.groupby("region_variant"):
                group_pred = model.predict(group["text"].astype(str))
                by_region[str(region)] = accuracy_score(group["label"].astype(str), group_pred)

        results[suite_name] = {
            "rows": len(suite_df),
            "base_case_overlap_with_train_valid": overlap,
            "accuracy": suite_accuracy,
            "accuracy_by_noise_type": by_noise,
            "accuracy_by_region_variant": by_region,
        }

    return results


# ─── 5. COMPARE V1 vs V2 ───────────────────────────────────────────────────────

def compare_versions():
    print("\n" + "=" * 60)
    print("STEP 4: SO SÁNH V1 (cũ) vs V2 (clean)")
    print("=" * 60)

    v1_path = ARTIFACT_DIR / "metrics_v1.json"
    v2_path = ARTIFACT_DIR / "metrics_v2_clean.json"

    if not v1_path.exists():
        print("⚠️  Không tìm thấy metrics_v1.json để so sánh.")
        return

    with v1_path.open("r", encoding="utf-8") as f:
        v1 = json.load(f)
    with v2_path.open("r", encoding="utf-8") as f:
        v2 = json.load(f)

    v1_acc = v1["test_metrics"]["accuracy"]
    v2_acc = v2["test_metrics"]["accuracy"]

    v1_scam = v1["test_metrics"]["classification_report"].get("SCAM", {})
    v2_scam = v2["test_metrics"]["classification_report"].get("SCAM", {})

    print(f"\n{'Metric':<25} {'V1 (w/ adapted)':<20} {'V2 (clean only)':<20}")
    print("-" * 65)
    print(f"{'Accuracy':<25} {v1_acc:.4f}               {v2_acc:.4f}")
    print(f"{'SCAM Precision':<25} {v1_scam.get('precision', 0):.4f}               {v2_scam.get('precision', 0):.4f}")
    print(f"{'SCAM Recall':<25} {v1_scam.get('recall', 0):.4f}               {v2_scam.get('recall', 0):.4f}")
    print(f"{'SCAM F1':<25} {v1_scam.get('f1-score', 0):.4f}               {v2_scam.get('f1-score', 0):.4f}")
    print(f"{'Training samples':<25} {v1['dataset']['train_full_rows']}                  {v2['dataset']['train_rows'] + v2['dataset']['valid_rows']}")

    delta = v2_acc - v1_acc
    sign = "+" if delta >= 0 else ""
    print(f"\nAccuracy delta: {sign}{delta:.4f}")
    print("\nLưu ý: Giảm nhẹ accuracy trên test set (nếu có) là bình thường khi loại bỏ")
    print("dữ liệu adapted — model bây giờ chỉ học từ ngữ cảnh tiếng Việt thực.")


# ─── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    filter_dataset()
    train_df, valid_df, test_df = load_clean_splits()
    retrain_and_evaluate(train_df, valid_df, test_df)
    compare_versions()

    print("\n" + "=" * 60)
    print("HOÀN TẤT — Các file được tạo:")
    print(f"  Dataset sạch : datasets/processed/scam_dataset_clean.csv")
    print(f"  Train/Valid/Test: datasets/processed/train_clean.csv ...")
    print(f"  Model mới    : ml_artifacts/scam_detector_pipeline_v2_clean.joblib")
    print(f"  Metrics mới  : ml_artifacts/metrics_v2_clean.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
