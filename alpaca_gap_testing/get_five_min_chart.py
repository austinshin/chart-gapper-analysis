from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
import pandas as pd
import os
import time

  # Initialize client
API_KEY = "AK1L8F4KFEBI63PT7ODI"
SECRET_KEY = "0K4dmimNx0wQuqlj6GB1RvfOGj55xKvFUFcNcgOh"

client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

# Read your gap results CSV (replace with your actual filename)
gaps_df = pd.read_csv('gap_results_20250107_190233.csv')  # Update this filename
top_20 = gaps_df.head(20)

def fetch_detailed_data(symbol, date_str):
    # Parse the date from the gap results
    gap_date = pd.to_datetime(date_str)
    
    # For daily data: Get 20 days before and after the gap
    daily_start = gap_date - timedelta(days=20)
    daily_end = gap_date + timedelta(days=20)
    
    # For 5min data: Get just the gap day and next day
    fivemin_start = gap_date - timedelta(days=1)
    fivemin_end = gap_date + timedelta(days=1)
    
    try:
        # Get daily data
        daily_params = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Day,
            start=daily_start,
            end=daily_end
        )
        
        # Get 5-minute data
        fivemin_params = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Minute,
            start=fivemin_start,
            end=fivemin_end
        )
        
        # Make requests with delay between them
        daily_bars = client.get_stock_bars(daily_params)
        time.sleep(2)  # Wait between requests
        fivemin_bars = client.get_stock_bars(fivemin_params)
        
        # Save to CSV files
        if daily_bars:
            daily_df = daily_bars.df
            daily_df.to_csv(f'detailed_data/{symbol}_daily_{gap_date.strftime("%Y%m%d")}.csv')
            
        if fivemin_bars:
            fivemin_df = fivemin_bars.df
            fivemin_df.to_csv(f'detailed_data/{symbol}_5min_{gap_date.strftime("%Y%m%d")}.csv')
            
        print(f"Successfully downloaded detailed data for {symbol}")
        return True
        
    except Exception as e:
        print(f"Error downloading detailed data for {symbol}: {e}")
        return False

# Create directory for detailed data
if not os.path.exists('detailed_data'):
    os.makedirs('detailed_data')

# Process top 20 gappers
for _, row in top_20.iterrows():
    print(f"\nProcessing detailed data for {row['symbol']} on {row['date']}")
    fetch_detailed_data(row['symbol'], row['date'])
    time.sleep(5)  # Wait between symbols

print("\nDetailed data download complete!")
print("Data has been saved to the 'detailed_data' directory")