from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "datasets" / "processed"
TEST_SUITE_DIR = BASE_DIR / "datasets" / "test_suites"

TEST_SUITE_DIR.mkdir(parents=True, exist_ok=True)

DATASET_FILES = [
    PROCESSED_DIR / "vietnamese_synthetic_full.csv",
    PROCESSED_DIR / "public_adapted_vi.csv",
    PROCESSED_DIR / "self_collected_vi.csv",
]

REQUIRED_COLUMNS = [
    "id",
    "base_case_id",
    "text",
    "label",
    "scam_type",
    "severity",
    "reason",
    "evidence_span",
    "recommended_action",
    "risk_factor",
    "harm_type",
    "target_group",
    "region_variant",
    "noise_type",
    "source",
    "license",
    "is_synthetic",
    "privacy_level",
    "split",
]

TRAIN_RATIO = 0.70
VALID_RATIO = 0.15
TEST_RATIO = 0.15


def load_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing dataset file: {path}")

    df = pd.read_csv(path)

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df = df[REQUIRED_COLUMNS]

    df["text"] = df["text"].astype(str).str.strip()
    df["label"] = df["label"].astype(str).str.strip().str.upper()
    df["scam_type"] = df["scam_type"].astype(str).str.strip().str.upper()
    df["split"] = df["split"].astype(str).str.strip().str.lower()

    df = df[df["text"] != ""]
    df = df[df["label"].isin(["SCAM", "SUSPICIOUS", "SAFE"])]

    return df


def resplit_by_label(df: pd.DataFrame) -> pd.DataFrame:
    """
    Chia lại train/valid/test theo từng label để giữ tỷ lệ nhãn cân bằng.
    Không dùng split cũ từ dataset nguồn vì sau merge dễ bị lệch.
    """
    parts = []

    for label, group in df.groupby("label"):
        group = group.sample(frac=1, random_state=42).reset_index(drop=True)

        n = len(group)
        train_end = int(n * TRAIN_RATIO)
        valid_end = train_end + int(n * VALID_RATIO)

        train_df = group.iloc[:train_end].copy()
        valid_df = group.iloc[train_end:valid_end].copy()
        test_df = group.iloc[valid_end:].copy()

        train_df["split"] = "train"
        valid_df["split"] = "valid"
        test_df["split"] = "test"

        parts.extend([train_df, valid_df, test_df])

    result = pd.concat(parts, ignore_index=True)
    result = result.sample(frac=1, random_state=42).reset_index(drop=True)
    return result


def main():
    frames = []

    for file_path in DATASET_FILES:
        df = load_dataset(file_path)
        print(f"Loaded {file_path.name}: {len(df)} rows")
        frames.append(df)

    full_df = pd.concat(frames, ignore_index=True)

    # Xóa trùng theo text normalize nhẹ
    full_df["text_key"] = (
        full_df["text"]
        .astype(str)
        .str.lower()
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    before_dedup = len(full_df)
    full_df = full_df.drop_duplicates(subset=["text_key"], keep="first")
    after_dedup = len(full_df)

    full_df = full_df.drop(columns=["text_key"])

    # Chia lại split sau khi merge + dedup
    full_df = resplit_by_label(full_df)

    # Gán lại ID final cho sạch
    full_df = full_df.reset_index(drop=True)
    full_df["id"] = [f"FINAL_{i+1:06d}" for i in range(len(full_df))]

    # Xuất full dataset
    full_path = PROCESSED_DIR / "scam_dataset_full.csv"
    full_df.to_csv(full_path, index=False, encoding="utf-8-sig")

    # Xuất train/valid/test
    train_df = full_df[full_df["split"] == "train"]
    valid_df = full_df[full_df["split"] == "valid"]
    test_df = full_df[full_df["split"] == "test"]

    train_df.to_csv(PROCESSED_DIR / "train.csv", index=False, encoding="utf-8-sig")
    valid_df.to_csv(PROCESSED_DIR / "valid.csv", index=False, encoding="utf-8-sig")
    test_df.to_csv(PROCESSED_DIR / "test.csv", index=False, encoding="utf-8-sig")

    # Test suites cho Responsible AI
    fairness_df = full_df[
        full_df["region_variant"].isin(["NORTH", "CENTRAL", "SOUTH"])
    ]

    robustness_df = full_df[
        full_df["noise_type"].notna()
        & (full_df["noise_type"].astype(str).str.upper() != "NONE")
        & (full_df["noise_type"].astype(str).str.strip() != "")
    ]

    explainability_df = full_df[
        full_df["reason"].notna()
        & full_df["evidence_span"].notna()
        & full_df["recommended_action"].notna()
        & (full_df["reason"].astype(str).str.strip() != "")
        & (full_df["recommended_action"].astype(str).str.strip() != "")
    ]

    fairness_df.to_csv(
        TEST_SUITE_DIR / "fairness_test.csv",
        index=False,
        encoding="utf-8-sig",
    )

    robustness_df.to_csv(
        TEST_SUITE_DIR / "robustness_test.csv",
        index=False,
        encoding="utf-8-sig",
    )

    explainability_df.to_csv(
        TEST_SUITE_DIR / "explainability_test.csv",
        index=False,
        encoding="utf-8-sig",
    )

    print("\nMERGE DONE")
    print("Before dedup:", before_dedup)
    print("After dedup:", after_dedup)
    print("Removed duplicates:", before_dedup - after_dedup)

    print("\nOutput files:")
    print(full_path)
    print(PROCESSED_DIR / "train.csv")
    print(PROCESSED_DIR / "valid.csv")
    print(PROCESSED_DIR / "test.csv")

    print("\nLabel distribution:")
    print(full_df["label"].value_counts())

    print("\nSplit distribution:")
    print(full_df["split"].value_counts())

    print("\nLabel distribution by split:")
    print(pd.crosstab(full_df["split"], full_df["label"]))

    print("\nSource distribution:")
    print(full_df["source"].value_counts())

    print("\nScam type distribution:")
    print(full_df["scam_type"].value_counts().head(20))

    print("\nResponsible AI test suites:")
    print("Fairness:", len(fairness_df))
    print("Robustness:", len(robustness_df))
    print("Explainability:", len(explainability_df))


if __name__ == "__main__":
    main()