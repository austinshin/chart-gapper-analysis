import pandas as pd
import os
from datetime import datetime
import glob
from config import MIN_PRICE, MIN_GAP_PERCENTAGE, MAX_GAP_PERCENTAGE, MIN_VOLUME

def is_valid_data_file(df):
    """Check if the dataframe has the required columns"""
    required_columns = ['open', 'high', 'low', 'close', 'volume', 'timestamp']
    return all(col in df.columns for col in required_columns)

def analyze_stored_data():
    print("Starting analysis of stored data...")
    all_gappers = []
    processed = 0
    invalid_files = []
    errors = []
    
    data_files = glob.glob('stock_data/*.csv')
    total_files = len(data_files)
    
    for file in data_files:
        symbol = os.path.basename(file).replace('_data.csv', '')
        processed += 1
        
        if processed % 100 == 0:
            print(f"Processed {processed}/{total_files} files")
            
        try:
            df = pd.read_csv(file)
            
            # Check if file has valid data
            if not is_valid_data_file(df):
                invalid_files.append(f"{symbol}: Invalid columns - {df.columns.tolist()}")
                continue
            
            # Check if file is empty
            if df.empty:
                invalid_files.append(f"{symbol}: Empty file")
                continue
                
            # Calculate gaps
            df['previous_close'] = df['close'].shift(1)
            df['gap_percentage'] = ((df['open'] - df['previous_close']) / df['previous_close']) * 100
            
            # Find big gaps that meet all criteria
            big_gaps = df[
                (df['gap_percentage'] > MIN_GAP_PERCENTAGE) &
                (df['gap_percentage'] < MAX_GAP_PERCENTAGE) &
                (df['open'] >= MIN_PRICE) &
                (df['volume'] >= MIN_VOLUME)
            ]
            
            if not big_gaps.empty:
                for _, row in big_gaps.iterrows():
                    all_gappers.append({
                        'date': row['timestamp'],
                        'symbol': symbol,
                        'gap_percentage': float(round(row['gap_percentage'], 2)),
                        'previous_close': round(row['previous_close'], 2),
                        'open': round(row['open'], 2),
                        'high': round(row['high'], 2),
                        'low': round(row['low'], 2),
                        'close': round(row['close'], 2),
                        'volume': int(row['volume']),
                        'dollar_change': round(row['open'] - row['previous_close'], 2)
                    })
                
        except Exception as e:
            errors.append(f"{symbol}: {str(e)}")
            continue

    # Print summary of invalid files
    if invalid_files:
        print("\nInvalid files found:")
        for file in invalid_files:
            print(file)
        
        # Optionally create a list of symbols to re-download
        with open('invalid_symbols.txt', 'w') as f:
            for file in invalid_files:
                symbol = file.split(':')[0]
                f.write(f"{symbol}\n")
        print("\nInvalid symbols saved to 'invalid_symbols.txt' for re-downloading")

    # Print error summary
    if errors:
        print("\nOther errors encountered:")
        for error in errors:
            print(error)

    if all_gappers:
        gappers_df = pd.DataFrame(all_gappers)
        gappers_df['date'] = pd.to_datetime(gappers_df['date'])
        gappers_df = gappers_df.sort_values('gap_percentage', ascending=False)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'gap_results_{timestamp}.csv'
        gappers_df.to_csv(output_file, index=False)
        
        print(f"\nFound {len(gappers_df)} total gaps")
        print(f"Results saved to {output_file}")
        
        return gappers_df
    
    return pd.DataFrame()

if __name__ == "__main__":
    results = analyze_stored_data()
    if not results.empty:
        print("\nTop 500 Gaps by Percentage:")
        # Set pandas to show all rows
        pd.set_option('display.max_rows', 500)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        
        # Show specific columns for better readability
        display_columns = ['date', 'symbol', 'gap_percentage', 'previous_close', 'open', 'volume']
        print(results[display_columns].head(500))
        
        print(f"\nTotal number of gaps found: {len(results)}")