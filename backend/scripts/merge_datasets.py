from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "datasets" / "processed"
TEST_SUITE_DIR = BASE_DIR / "datasets" / "test_suites"

TEST_SUITE_DIR.mkdir(parents=True, exist_ok=True)

DATASET_FILES = [
    PROCESSED_DIR / "vietnamese_synthetic_full.csv",
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
    Chia lại train/valid/test theo base_case_id để tránh leakage giữa các
    noise/region variants của cùng một tình huống.
    """
    base_cases = (
        df.groupby("base_case_id", dropna=False)
        .agg(label=("label", lambda values: values.mode().iat[0]), rows=("label", "size"))
        .reset_index()
    )

    split_by_base_case = {}

    for label, group in base_cases.groupby("label"):
        group = group.sample(frac=1, random_state=42).reset_index(drop=True)

        n = int(group["rows"].sum())
        train_end = int(n * TRAIN_RATIO)
        valid_end = train_end + int(n * VALID_RATIO)

        running_rows = 0
        for _, row in group.iterrows():
            if running_rows < train_end:
                split = "train"
            elif running_rows < valid_end:
                split = "valid"
            else:
                split = "test"
            split_by_base_case[row["base_case_id"]] = split
            running_rows += int(row["rows"])

    result = df.copy()
    result["split"] = result["base_case_id"].map(split_by_base_case)
    result = result.sample(frac=1, random_state=42).reset_index(drop=True)
    return result


def assert_no_base_case_overlap(train_like_df: pd.DataFrame, suite_df: pd.DataFrame, suite_name: str) -> None:
    train_like_base_cases = set(train_like_df["base_case_id"].astype(str))
    suite_base_cases = set(suite_df["base_case_id"].astype(str))
    overlap = train_like_base_cases & suite_base_cases
    if overlap:
        raise ValueError(
            f"{suite_name} leaks {len(overlap)} base_case_id values from train/valid"
        )


def insert_zero_width_noise(text: str) -> str:
    words = str(text).split()
    noisy_words = []
    for index, word in enumerate(words):
        if index < 10 and len(word) >= 4:
            noisy_words.append("\u200d".join(word))
        else:
            noisy_words.append(word)
    return " ".join(noisy_words)


def add_punctuation_emoji_noise(text: str) -> str:
    words = str(text).split()
    noisy_words = []
    for index, word in enumerate(words):
        noisy_words.append(word)
        if index % 7 == 3:
            noisy_words.append("!!!")
        elif index % 7 == 6:
            noisy_words.append("🔴")
    return " ".join(noisy_words)


def to_fullwidth_ascii_noise(text: str) -> str:
    result = []
    for char in str(text):
        code = ord(char)
        if 0x21 <= code <= 0x7E:
            result.append(chr(code + 0xFEE0))
        else:
            result.append(char)
    return "".join(result)


def build_robustness_challenge_suite(test_df: pd.DataFrame) -> pd.DataFrame:
    transforms = [
        ("ZERO_WIDTH", insert_zero_width_noise),
        ("EMOJI_PUNCT", add_punctuation_emoji_noise),
        ("FULLWIDTH_ASCII", to_fullwidth_ascii_noise),
    ]
    rows = []

    for _, row in test_df.iterrows():
        for noise_type, transform in transforms:
            challenge_row = row.copy()
            challenge_row["id"] = f"{row['id']}_{noise_type}"
            challenge_row["text"] = transform(row["text"])
            challenge_row["noise_type"] = noise_type
            rows.append(challenge_row)

    if not rows:
        return test_df.iloc[0:0].copy()

    return pd.DataFrame(rows).reset_index(drop=True)


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
    train_like_df = full_df[full_df["split"].isin(["train", "valid"])]

    train_df.to_csv(PROCESSED_DIR / "train.csv", index=False, encoding="utf-8-sig")
    valid_df.to_csv(PROCESSED_DIR / "valid.csv", index=False, encoding="utf-8-sig")
    test_df.to_csv(PROCESSED_DIR / "test.csv", index=False, encoding="utf-8-sig")

    # Test suites cho Responsible AI: chỉ lấy test split để tránh leakage từ
    # train + valid, vì model cuối cùng được fit trên cả hai split này.
    fairness_df = test_df[
        test_df["region_variant"].isin(["NORTH", "CENTRAL", "SOUTH"])
    ]

    robustness_df = build_robustness_challenge_suite(test_df)

    explainability_df = test_df[
        test_df["reason"].notna()
        & test_df["evidence_span"].notna()
        & test_df["recommended_action"].notna()
        & (test_df["reason"].astype(str).str.strip() != "")
        & (test_df["recommended_action"].astype(str).str.strip() != "")
    ]

    assert_no_base_case_overlap(train_like_df, fairness_df, "fairness_test.csv")
    assert_no_base_case_overlap(train_like_df, robustness_df, "robustness_test.csv")
    assert_no_base_case_overlap(train_like_df, explainability_df, "explainability_test.csv")

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
