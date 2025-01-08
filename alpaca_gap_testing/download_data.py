from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
from config import API_KEY, SECRET_KEY
import pandas as pd
import os
import time

# Initialize client
API_KEY = "AK1L8F4KFEBI63PT7ODI"
SECRET_KEY = "0K4dmimNx0wQuqlj6GB1RvfOGj55xKvFUFcNcgOh"

client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

# Create data directory if it doesn't exist
if not os.path.exists('stock_data'):
    os.makedirs('stock_data')

def download_symbol_data(symbol):
    output_file = f'stock_data/{symbol}_data.csv'
    
    # Skip if already downloaded
    if os.path.exists(output_file):
        print(f"Already have data for {symbol}, skipping...")
        return True
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)  # 2 years
    
    try:
        request_params = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Day,
            start=start_date,
            end=end_date
        )
        
        bars = client.get_stock_bars(request_params)
        if bars:
            df = bars.df
            df.to_csv(output_file)
            print(f"Successfully downloaded {symbol}")
            return True
            
    except Exception as e:
        print(f"Error downloading {symbol}: {e}")
        return False

# Read the NASDAQ tickers
nasdaq_df = pd.read_csv('nasdaq_tickers.csv.xls')
symbols = nasdaq_df['Tickers'].dropna().astype(str).tolist()

# Clean symbols (remove special characters and spaces)
clean_symbols = []
for symbol in symbols:
    # Take only the part before any space or special character
    clean_symbol = symbol.split()[0].split('.')[0].split('-')[0]
    if clean_symbol.isalnum() and len(clean_symbol) <= 4:
        clean_symbols.append(clean_symbol)

# Remove duplicates and sort
clean_symbols = sorted(list(set(clean_symbols)))

print(f"Starting download of {len(clean_symbols)} symbols...")

# Track progress
total = len(clean_symbols)
successful = 0
failed = []

for i, symbol in enumerate(clean_symbols, 1):
    print(f"\nProcessing {i}/{total}: {symbol}")
    
    if download_symbol_data(symbol):
        successful += 1
    else:
        failed.append(symbol)
    
    # Progress update
    if i % 10 == 0:
        print(f"\nProgress Update:")
        print(f"Processed: {i}/{total} ({(i/total*100):.1f}%)")
        print(f"Successful: {successful}")
        print(f"Failed: {len(failed)}")
    
    time.sleep(1)  # Small delay between requests

# Save failed symbols to file
if failed:
    with open('failed_downloads.txt', 'w') as f:
        f.write('\n'.join(failed))

print("\nDownload Complete!")
print(f"Successfully downloaded: {successful}/{total} symbols")
print(f"Failed: {len(failed)} symbols")
if failed:
    print("Failed symbols have been saved to 'failed_downloads.txt'")
print("\nData has been saved to the 'stock_data' directory")