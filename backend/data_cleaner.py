# backend/data_cleaner.py
import os
import pandas as pd
from config import RAW_PATH, CLEAN_PATH


def ensure_cleaned_dir():
    """Ensure cleaned directory exists."""
    os.makedirs(CLEAN_PATH, exist_ok=True)


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names to lowercase and replace spaces/special chars."""
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("(", "", regex=False)
        .str.replace(")", "", regex=False)
        .str.replace("%", "percent", regex=False)
        .str.replace("/", "_", regex=False)
    )
    return df


def clean_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Convert numeric columns and handle commas or symbols."""
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.replace(",", "", regex=False)
            # Try numeric conversion
            try:
                df[col] = pd.to_numeric(df[col])
            except Exception:
                pass
    return df


def clean_excel_sheets(file_path: str):
    """
    Reads a single Excel file with multiple sheets,
    cleans each sheet, and saves them as CSV in data/cleaned.
    """
    ensure_cleaned_dir()

    all_sheets = pd.read_excel(file_path, sheet_name=None)

    for sheet_name, df in all_sheets.items():
        df = clean_column_names(df)
        df = clean_numeric_columns(df)

        clean_filename = f"{sheet_name.lower().replace(' ', '_')}.csv"
        clean_path = os.path.join(CLEAN_PATH, clean_filename)

        df.to_csv(clean_path, index=False)


def run_data_cleaning():
    """Main function to locate Excel in raw folder and clean all sheets."""
    ensure_cleaned_dir()

    # Find the first Excel file in data/raw/
    raw_files = [f for f in os.listdir(RAW_PATH) if f.endswith((".xlsx", ".xls"))]
    if not raw_files:
        print("No Excel file found in data/raw/. Please add one and retry.")
        return

    excel_file = os.path.join(RAW_PATH, raw_files[0])
    clean_excel_sheets(excel_file)



if __name__ == "__main__":
    run_data_cleaning()
