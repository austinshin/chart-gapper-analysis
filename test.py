import pandas as pd

# Read and check the first few rows of your CSV
df = pd.read_csv('nasdaq_tickers.csv.xls')
print(df.head())