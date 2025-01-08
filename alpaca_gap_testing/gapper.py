
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from datetime import datetime, timedelta
import pandas as pd
import os

# Your API credentials
API_KEY = "AK1L8F4KFEBI63PT7ODI"
SECRET_KEY = "0K4dmimNx0wQuqlj6GB1RvfOGj55xKvFUFcNcgOh"
BASE_URL = "https://api.alpaca.markets"

# Initialize with your Market Data API keys
client = StockHistoricalDataClient(
    api_key="AK1L8F4KFEBI63PT7ODI",
    secret_key="0K4dmimNx0wQuqlj6GB1RvfOGj55xKvFUFcNcgOh"
)

trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
data_client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

def get_all_symbols():
    print("Loading common stock symbols...")
    try:
        # Read your existing NASDAQ file
        nasdaq_df = pd.read_csv('nasdaq_tickers.csv.xls')
        nasdaq_symbols = nasdaq_df['Tickers'].dropna().astype(str).tolist()
        
        # Remove any obvious non-stock symbols
        clean_symbols = [sym for sym in nasdaq_symbols if sym.isalpha() and len(sym) < 5]
        
        print(f"Found {len(clean_symbols)} tradable symbols")
        return clean_symbols

    except Exception as e:
        print(f"Error loading symbols: {e}")
        return []

# Rest of your code remains the same...
# def get_all_symbols():
#     print("Fetching symbols from all exchanges...")
#     try:
#         assets = trading_client.get_all_assets()
#         symbols = []
#         for asset in assets:
#             if (asset.tradable and 
#                 asset.status == 'active' and 
#                 asset.exchange in ['NYSE', 'NASDAQ', 'AMEX', 'ARCA']):
#                 symbols.append(asset.symbol)
        
#         print(f"Found {len(symbols)} tradable symbols")
#         return symbols

#     except Exception as e:
#         print(f"Error fetching symbols: {e}")
#         return []

def save_to_csv(df, filename):
    try:
        df.to_csv(filename, index=False)
    except PermissionError:
        base, ext = os.path.splitext(filename)
        new_filename = f"{base}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
        df.to_csv(new_filename, index=False)
        print(f"File saved as: {new_filename}")

def clean_symbols(symbols):
    cleaned = []
    for sym in symbols:
        try:
            # Remove any whitespace
            sym = str(sym).strip()
            
            # Take only the part before any space, period, or special character
            sym = sym.split()[0]
            sym = sym.split('.')[0]
            sym = sym.split('-')[0]
            sym = sym.split('/')[0]
            
            # Remove any remaining special characters
            sym = ''.join(c for c in sym if c.isalnum())
            
            # Only keep if it's a valid looking symbol
            if sym.isalnum() and 1 < len(sym) <= 4 and not sym.isdigit():
                cleaned.append(sym)
                
        except Exception as e:
            print(f"Error cleaning symbol {sym}: {e}")
            continue
            
    cleaned = list(set(cleaned))  # Remove duplicates
    cleaned.sort()  # Sort alphabetically
    return cleaned

# Read and clean the NASDAQ tickers
nasdaq_df = pd.read_csv('nasdaq_tickers.csv.xls')
raw_symbols = nasdaq_df['Tickers'].dropna().astype(str).tolist()
symbols = clean_symbols(raw_symbols)

# Print first few raw and cleaned symbols for debugging
print("\nFirst 10 raw symbols:", raw_symbols[:10])
print("\nFirst 10 cleaned symbols:", symbols[:10])
print(f"\nCleaned {len(raw_symbols)} raw symbols to {len(symbols)} valid symbols")


def analyze_gaps(symbols, min_gap_percentage=50):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)  # 2 years
    
    all_gappers = []
    chunk_size = 50  # Reduced chunk size
    
    # Filtering criteria
    MIN_PRICE = 0.20
    MIN_VOLUME = 100000
    
    total_chunks = len(range(0, len(symbols), chunk_size))
    current_chunk = 0
    
    for i in range(0, len(symbols), chunk_size):
        current_chunk += 1
        chunk = symbols[i:i + chunk_size]
        print(f"Processing chunk {current_chunk}/{total_chunks} ({len(chunk)} symbols)...")
        
        clean_chunk = [sym.strip() for sym in chunk if isinstance(sym, str) and sym.strip()]
        
        request_params = StockBarsRequest(
            symbol_or_symbols=clean_chunk,
            timeframe=TimeFrame.Day,
            start=start_date,
            end=end_date,
        )
        
        try:
            bars = client.get_stock_bars(request_params)
            if bars:
                df = bars.df
                print(f"Received data for {len(df.index.get_level_values(0).unique())} symbols")
                
                for symbol in clean_chunk:
                    try:
                        if symbol in df.index.get_level_values(0):
                            symbol_data = df.loc[symbol].copy()
                            print(f"Processing {symbol} - {len(symbol_data)} days of data")
                            
                            symbol_data['previous_close'] = symbol_data['close'].shift(1)
                            symbol_data['gap_percentage'] = ((symbol_data['open'] - symbol_data['previous_close']) / symbol_data['previous_close']) * 100
                            
                            # Print some debug info for the first few symbols
                            if len(all_gappers) == 0:
                                print(f"\nSample data for {symbol}:")
                                print(f"Max gap: {symbol_data['gap_percentage'].max():.2f}%")
                                print(f"Min price: ${symbol_data['open'].min():.2f}")
                                print(f"Max volume: {symbol_data['volume'].max():.0f}")
                            
                            big_gaps = symbol_data[
                                (symbol_data['gap_percentage'] > min_gap_percentage) &
                                (symbol_data['open'] >= MIN_PRICE) &
                                (symbol_data['volume'] >= MIN_VOLUME)
                            ]
                            
                            if not big_gaps.empty:
                                print(f"Found {len(big_gaps)} gaps for {symbol}")
                                for date, row in big_gaps.iterrows():
                                    all_gappers.append({
                                        'date': date.strftime('%Y-%m-%d'),
                                        'symbol': symbol,
                                        'gap_percentage': round(row['gap_percentage'], 2),
                                        'previous_close': round(row['previous_close'], 2),
                                        'open': round(row['open'], 2),
                                        'high': round(row['high'], 2),
                                        'low': round(row['low'], 2),
                                        'close': round(row['close'], 2),
                                        'volume': int(row['volume']),
                                        'dollar_change': round(row['open'] - row['previous_close'], 2)
                                    })
                                    
                    except Exception as e:
                        print(f"Error processing {symbol}: {str(e)}")
                        continue
                        
        except Exception as e:
            print(f"Error fetching chunk data: {str(e)}")
    
    if all_gappers:
        gappers_df = pd.DataFrame(all_gappers)
        gappers_df = gappers_df.sort_values(['date', 'gap_percentage'], ascending=[False, False])
        
        try:
            gappers_df.to_csv('gap_results_2years.csv', index=False)
            print(f"\nResults saved to gap_results_2years.csv")
        except Exception as e:
            print(f"Error saving CSV: {e}")
            
        return gappers_df
    return pd.DataFrame()

# Read the NASDAQ tickers
nasdaq_df = pd.read_csv('nasdaq_tickers.csv.xls')
symbols = nasdaq_df['Tickers'].dropna().astype(str).tolist()

# Take first 100 symbols for testing
test_symbols = symbols[:100]
print(f"Testing with first {len(test_symbols)} symbols...")

# Run the analysis
print("Starting gap analysis for last 2 years...")
results = analyze_gaps(test_symbols)
if not results.empty:
    print("\nGappers found:")
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    print(results)
    print(f"\nTotal number of gappers found: {len(results)}")
else:
    print("No gaps found matching the criteria")