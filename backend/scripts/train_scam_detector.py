import json
from pathlib import Path

import joblib
import pandas as pd

from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)


BASE_DIR = Path(__file__).resolve().parents[1]

DATASET_DIR = BASE_DIR / "datasets" / "processed"
ARTIFACT_DIR = BASE_DIR / "ml_artifacts"
REPORT_DIR = BASE_DIR / "reports"

TRAIN_PATH = DATASET_DIR / "train.csv"
VALID_PATH = DATASET_DIR / "valid.csv"
TEST_PATH = DATASET_DIR / "test.csv"

ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def load_dataset():
    train_df = pd.read_csv(TRAIN_PATH)
    valid_df = pd.read_csv(VALID_PATH)
    test_df = pd.read_csv(TEST_PATH)

    required_cols = ["text", "label"]

    for name, df in [
        ("train", train_df),
        ("valid", valid_df),
        ("test", test_df),
    ]:
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing column '{col}' in {name}.csv")

    train_df = train_df.dropna(subset=["text", "label"])
    valid_df = valid_df.dropna(subset=["text", "label"])
    test_df = test_df.dropna(subset=["text", "label"])

    train_df["text"] = train_df["text"].astype(str)
    valid_df["text"] = valid_df["text"].astype(str)
    test_df["text"] = test_df["text"].astype(str)

    train_df["label"] = train_df["label"].astype(str).str.upper().str.strip()
    valid_df["label"] = valid_df["label"].astype(str).str.upper().str.strip()
    test_df["label"] = test_df["label"].astype(str).str.upper().str.strip()

    allowed_labels = ["SAFE", "SUSPICIOUS", "SCAM"]

    train_df = train_df[train_df["label"].isin(allowed_labels)]
    valid_df = valid_df[valid_df["label"].isin(allowed_labels)]
    test_df = test_df[test_df["label"].isin(allowed_labels)]

    return train_df, valid_df, test_df


def build_model():
    word_vectorizer = TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 2),
        min_df=1,
        max_features=25000,
        lowercase=True,
    )

    # Char n-gram giúp bắt lỗi không dấu, sai chính tả, viết tắt, né keyword.
    char_vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=1,
        max_features=35000,
        lowercase=True,
    )

    features = FeatureUnion(
        [
            ("word_tfidf", word_vectorizer),
            ("char_tfidf", char_vectorizer),
        ]
    )

    classifier = LogisticRegression(
        max_iter=3000,
        class_weight="balanced",
        solver="liblinear",
        random_state=42,
    )

    pipeline = Pipeline(
        [
            ("features", features),
            ("classifier", classifier),
        ]
    )

    return pipeline


def evaluate_model(model, X, y, split_name):
    y_pred = model.predict(X)

    accuracy = accuracy_score(y, y_pred)

    labels = ["SAFE", "SUSPICIOUS", "SCAM"]

    report_dict = classification_report(
        y,
        y_pred,
        labels=labels,
        output_dict=True,
        zero_division=0,
    )

    report_text = classification_report(
        y,
        y_pred,
        labels=labels,
        zero_division=0,
    )

    cm = confusion_matrix(y, y_pred, labels=labels)

    print(f"\n========== {split_name.upper()} RESULT ==========")
    print("Accuracy:", round(accuracy, 4))
    print("\nClassification report:")
    print(report_text)

    print("Confusion matrix labels:")
    print(labels)
    print(cm)

    return {
        "split": split_name,
        "accuracy": accuracy,
        "labels": labels,
        "classification_report": report_dict,
        "confusion_matrix": cm.tolist(),
    }


def save_prediction_samples(model, test_df):
    sample_df = test_df.copy()
    sample_df["predicted_label"] = model.predict(sample_df["text"].astype(str))

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(sample_df["text"].astype(str))
        classes = list(model.classes_)

        for idx, label in enumerate(classes):
            sample_df[f"score_{label}"] = probabilities[:, idx]

        sample_df["max_score"] = probabilities.max(axis=1)

    output_path = REPORT_DIR / "test_predictions_v1.csv"
    sample_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print("\nSaved test predictions to:", output_path)


def main():
    print("Loading dataset...")

    train_df, valid_df, test_df = load_dataset()

    print("\nDataset size:")
    print("Train:", len(train_df))
    print("Valid:", len(valid_df))
    print("Test :", len(test_df))

    print("\nTrain label distribution:")
    print(train_df["label"].value_counts())

    print("\nValid label distribution:")
    print(valid_df["label"].value_counts())

    print("\nTest label distribution:")
    print(test_df["label"].value_counts())

    # Train final model bằng train + valid, giữ test làm đánh giá cuối.
    train_full_df = pd.concat([train_df, valid_df], ignore_index=True)

    X_train = train_full_df["text"].astype(str)
    y_train = train_full_df["label"].astype(str)

    X_test = test_df["text"].astype(str)
    y_test = test_df["label"].astype(str)

    print("\nTraining final model with train + valid...")
    print("Training rows:", len(train_full_df))

    model = build_model()
    model.fit(X_train, y_train)

    test_metrics = evaluate_model(model, X_test, y_test, "test")

    model_path = ARTIFACT_DIR / "scam_detector_pipeline_v1.joblib"
    metrics_path = ARTIFACT_DIR / "metrics_v1.json"

    joblib.dump(model, model_path)

    metrics = {
        "model_name": "TF-IDF word+char ngram + LogisticRegression",
        "dataset": {
            "train_rows": len(train_df),
            "valid_rows": len(valid_df),
            "test_rows": len(test_df),
            "train_full_rows": len(train_full_df),
        },
        "test_metrics": test_metrics,
        "notes": [
            "Model is a local baseline scam detector.",
            "TF-IDF word n-grams capture keyword and phrase patterns.",
            "Character n-grams improve robustness for no-diacritics, typos, abbreviations, and obfuscated text.",
            "class_weight='balanced' is used to reduce class imbalance impact.",
            "For scam-prevention use case, SCAM recall should be monitored carefully.",
        ],
    }

    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    save_prediction_samples(model, test_df)

    print("\nDONE")
    print("Saved model to  :", model_path)
    print("Saved metrics to:", metrics_path)


if __name__ == "__main__":
    main()