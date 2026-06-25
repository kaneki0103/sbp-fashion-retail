import pandas as pd
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "data")
INPUT_FILE  = os.path.join(DATA_PATH, "transactions.csv")
OUTPUT_FILE = os.path.join(DATA_PATH, "transactions_sample.csv")

SAMPLE_ROWS = 2_500_000

print(f"Učitavam prvih {SAMPLE_ROWS:,} redova iz transactions.csv...")

df = pd.read_csv(INPUT_FILE, nrows=SAMPLE_ROWS)

df.to_csv(OUTPUT_FILE, index=False)

print(f"Sačuvano {len(df):,} redova u transactions_sample.csv")
print(f"Originalni fajl ostaje nepromenjen.")