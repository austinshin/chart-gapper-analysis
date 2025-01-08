import mplfinance as mpf
import pandas as pd
import numpy as np
import os
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
import time
from config import API_KEY, SECRET_KEY, GAP_RESULTS_FILE, TOP_N_GAPPERS
import matplotlib.pyplot as plt  # Add this import


client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

def calculate_vwap(df):
    df['Typical_Price'] = (df['High'] + df['Low'] + df['Close']) / 3
    df['VP'] = df['Typical_Price'] * df['Volume']
    df['Cumulative_VP'] = df['VP'].cumsum()
    df['Cumulative_Volume'] = df['Volume'].cumsum()
    df['VWAP'] = df['Cumulative_VP'] / df['Cumulative_Volume']
    return df

def prepare_data_for_mpl(df, gap_date):
    try:
        if isinstance(df.index, pd.MultiIndex):
            df = df.reset_index(level=0)
        
        if 'timestamp' in df.columns:
            df.set_index('timestamp', inplace=True)
        
        df.index = pd.to_datetime(df.index)
        df = df.between_time('03:30', '16:30')
        
        # Add market session column
        df['market_session'] = 'normal'
        df.loc[df.index.time < pd.Timestamp('09:30').time(), 'market_session'] = 'pre'
        df.loc[df.index.time >= pd.Timestamp('16:00').time(), 'market_session'] = 'post'
        
        df = df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        })
        
        df = calculate_vwap(df)
        return df
        
    except Exception as e:
        print(f"Error in prepare_data_for_mpl: {e}")
        raise

def plot_charts(symbol, gap_date_str):
    gap_date = pd.to_datetime(gap_date_str)
    
    # For daily chart, get more historical context
    daily_start = gap_date - timedelta(days=20)
    daily_end = gap_date + timedelta(days=20)
    
    # For intraday, focus on the gap day
    intraday_start = gap_date.replace(hour=3, minute=30)  # 3:30 AM PST
    intraday_end = gap_date.replace(hour=16, minute=30)   # 4:30 PM PST

    try:
        daily_params = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Day,
            start=daily_start,
            end=daily_end
        )
        
        fivemin_params = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Minute,
            start=intraday_start,
            end=intraday_end
        )
        
        onemin_params = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Minute,
            start=intraday_start,
            end=intraday_end
        )

        print(f"Fetching data for {symbol}...")
        
        daily_bars = client.get_stock_bars(daily_params)
        time.sleep(1)
        fivemin_bars = client.get_stock_bars(fivemin_params)
        time.sleep(1)
        onemin_bars = client.get_stock_bars(onemin_params)

        daily_df = prepare_data_for_mpl(daily_bars.df, gap_date)
        fivemin_df = prepare_data_for_mpl(fivemin_bars.df, gap_date)
        onemin_df = prepare_data_for_mpl(onemin_bars.df, gap_date)

        # Style settings
        mc = mpf.make_marketcolors(up='g', down='r',
                                 edge='inherit',
                                 wick='inherit',
                                 volume='in',
                                 ohlc='inherit')
        
        style = mpf.make_mpf_style(
            base_mpf_style='charles',
            marketcolors=mc,
            gridstyle='-',
            gridcolor='gray',
            gridaxis='both',
            rc={
                'axes.grid.axis': 'both',
                'axes.grid': True,
                'grid.alpha': 0.3,
                'axes.labelsize': 12,
                'xtick.labelsize': 10,
                'lines.linewidth': 2.5,
                'lines.markersize': 15,
            }
        )

        # Common plot settings
        kwargs = dict(
            type='candle',
            volume=True,
            style=style,
            figsize=(15, 10),
            tight_layout=False,  # Changed to False to allow panel spacing
            datetime_format='%I:%M %p',  # 12-hour format
            xrotation=45,
            ylabel='Price ($)',
            ylabel_lower='Volume',
            panel_ratios=(3,1),  # Ratio between price and volume panels
            figratio=(15,8),     # More horizontal figure
            volume_panel=1       # Separate volume panel
        )

        def plot_zoomed(df, title, filename):
            # Filter for 7 AM EST to 7 PM EST (4 AM PST to 4 PM PST)
            df = df.between_time('04:00', '16:00')
            
            # Calculate price padding
            price_range = df['High'].max() - df['Low'].min()
            price_padding = price_range * 0.1  # 10% padding
            ylim = (df['Low'].min() - price_padding, 
                   df['High'].max() + price_padding)
            
            market_open = pd.Timestamp('09:30').time()
            market_close = pd.Timestamp('16:00').time()
            
            fill_colors = []
            for idx in df.index:
                if idx.time() < market_open:
                    fill_colors.append('lightgray')
                elif idx.time() >= market_close:
                    fill_colors.append('lightblue')
                else:
                    fill_colors.append('white')

            fig, axlist = mpf.plot(df,
                    title=title,
                    addplot=[mpf.make_addplot(df['VWAP'], color='blue', width=2, label='VWAP')],
                    ylim=ylim,
                    savefig=filename,
                    fill_between={'y1': df['Low'].values,
                                'y2': df['High'].values,
                                'alpha': 0.1,
                                'color': fill_colors},
                    returnfig=True,
                    **kwargs)
            
            # Add space between panels
            fig.subplots_adjust(hspace=0.3)
            
            fig.savefig(filename)
            plt.close(fig)

        # Daily chart
        fig, axlist = mpf.plot(daily_df, 
                title=f'\n{symbol} Daily Chart',
                addplot=[mpf.make_addplot(daily_df['VWAP'], color='blue', width=2)],
                returnfig=True,
                **kwargs)
        
        fig.subplots_adjust(hspace=0.3)  # Add space between panels
        fig.savefig('daily_chart.png')
        plt.close(fig)
        
        # 5-minute chart
        plot_zoomed(fivemin_df, 
                   f'\n{symbol} 5-Minute Chart', 
                   '5min_chart.png')
        
        # 1-minute chart
        plot_zoomed(onemin_df, 
                   f'\n{symbol} 1-Minute Chart', 
                   '1min_chart.png')

    except Exception as e:
        print(f"Error creating charts: {e}")
        raise


# Read results and process top gappers
print("Reading results file...")
results_df = pd.read_csv(GAP_RESULTS_FILE)
top_gappers = results_df.head(TOP_N_GAPPERS)

# Create charts directory
if not os.path.exists('charts'):
    os.makedirs('charts')

# Process each gapper
for idx, gapper in top_gappers.iterrows():
    print(f"\nAnalyzing gapper {idx+1} of {TOP_N_GAPPERS}:")
    print(f"Symbol: {gapper['symbol']}")
    print(f"Date: {gapper['date']}")
    print(f"Gap: {gapper['gap_percentage']}%")
    
    try:
        symbol_dir = f"charts/{gapper['symbol']}"
        if not os.path.exists(symbol_dir):
            os.makedirs(symbol_dir)
        
        plot_charts(gapper['symbol'], gapper['date'])
        
        for timeframe in ['daily', '5min', '1min']:
            old_path = f'{timeframe}_chart.png'
            new_path = f'{symbol_dir}/{timeframe}_chart.png'
            if os.path.exists(old_path):
                os.rename(old_path, new_path)
        
        print(f"Charts saved in {symbol_dir}")
        
    except Exception as e:
        print(f"Error processing {gapper['symbol']}: {e}")
        continue
    
    time.sleep(1)

print("\nAll charts have been generated!")