import pandas as pd
import os

# Input CSV with all profiles
input_file = r'perfiles_combinados.csv'

# Output directory for individual CSVs
output_dir = ''
os.makedirs(output_dir, exist_ok=True)

# Read CSV (semicolon separator, comma decimal)
df = pd.read_csv(input_file, sep=';', decimal=',')

# Save each column as an individual CSV (no normalization)
for column in df.columns:
    df[column].to_csv(f'{output_dir}/{column}.csv', index=False, header=False)
    print(f"Saved {column}.csv")
