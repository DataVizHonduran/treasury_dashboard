import pandas as pd
import plotly.graph_objects as go
import plotly.subplots as sp
from datetime import datetime, timedelta
import os
import yfinance as yf

def get_treasury_data(years=2):
    series = {
        '2Y': 'ZT=F',
        '5Y': 'ZF=F',
        '10Y': 'ZN=F',
        '30Y': 'ZB=F'
    }
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * years)
    
    print("🏛️  DAILY TREASURY ANALYSIS")
    print(f"📅 {end_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    print("Fetching Treasury Futures data from Yahoo Finance...")
    
    data = {}
    
    for maturity, ticker in series.items():
        try:
            df_ticker = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if not df_ticker.empty:
                data[maturity] = df_ticker['Close']
                print(f"✓ {maturity}")
        except Exception as e:
            print(f"✗ {maturity}: {str(e)[:50]}...")
    
    if not data:
        print("❌ No data retrieved. Check connection to Yahoo Finance.")
        return pd.DataFrame()
    
    df = pd.concat(data, axis=1).dropna(how='all')
    df.columns = data.keys()
    print(f"✅ Got {len(df.columns)} rates, {len(df)} days")
    
    today_str = end_date.strftime('%Y%m%d')
    df.to_csv(f'treasury_data_{today_str}.csv')
    
    return df

def analyze_rates(df, n_days=90):
    if df.empty:
        return
    
    recent = df.tail(n_days)
    current = df.iloc[-1]
    
    stats = pd.DataFrame({
        'Current': current,
        f'{n_days}D_Max': recent.max(),
        f'{n_days}D_Min': recent.min(),
        f'{n_days}D_Median': recent.median(),
        f'{n_days}D_Mean': recent.mean()
    })
    
    print(f"\n📊 YIELD CURVE SNAPSHOT ({df.index[-1].strftime('%Y-%m-%d')})")
    print("=" * 50)
    
    order = ['2Y', '5Y', '10Y', '30Y']
    for maturity in order:
        if maturity in current.index:
            print(f"{maturity:>3}: {current[maturity]:6.3f}")
    
    spread_2s10s = current['10Y'] - current['2Y'] if '2Y' in current and '10Y' in current else None
    spread_5s30s = current['30Y'] - current['5Y'] if '5Y' in current and '30Y' in current else None
    
    print(f"\n📈 KEY SPREADS")
    print("-" * 20)
    if spread_2s10s is not None: print(f"2s10s: {spread_2s10s:+.3f}")
    if spread_5s30s is not None: print(f"5s30s: {spread_5s30s:+.3f}")
    
    today_str = datetime.now().strftime('%Y%m%d')
    summary_data = {
        'date': df.index[-1].strftime('%Y-%m-%d'),
        '2s10s': spread_2s10s,
        '5s30s': spread_5s30s,
        **{f'{m}_price': current.get(m, None) for m in order}
    }
    
    pd.DataFrame([summary_data]).to_csv(f'treasury_summary_{today_str}.csv', index=False)
    
    return stats

def plot_curve(df, stats, n_days=90):
    if df.empty:
        return
    
    maturity_map = {'2Y': 2, '5Y': 5, '10Y': 10, '30Y': 30}
    current = stats['Current'].dropna()
    maturities = [m for m in current.index if m in maturity_map]
    y_vals = [current[m] for m in maturities]
    
    fig = sp.make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            'Current Curve (Prices)', 
            'Historical Trends', 
            '2s10s & 5s30s Spreads', 
            f'Current vs {n_days}D Range'
        ]
    )
    
    fig.add_trace(
        go.Scatter(x=maturities, y=y_vals, mode='lines+markers+text',
                   text=[f'{y:.2f}' for y in y_vals], textposition='top center',
                   line=dict(width=3, color='blue'), name='Current'),
        row=1, col=1
    )
    
    recent_data = df.tail(252)
    colors = ['red', 'green', 'blue', 'orange']
    for i, rate in enumerate(['2Y', '5Y', '10Y', '30Y']):
        if rate in df.columns:
            fig.add_trace(
                go.Scatter(x=recent_data.index, y=recent_data[rate], mode='lines',
                           name=rate, line=dict(width=2, color=colors[i])),
                row=1, col=2
            )
    
    if '10Y' in df.columns and '2Y' in df.columns:
        s2s10s = (df['10Y'] - df['2Y']).tail(252)
        fig.add_trace(
            go.Scatter(x=s2s10s.index, y=s2s10s, mode='lines',
                       line=dict(color='red'), name='2s10s'),
            row=2, col=1
        )
        
    if '30Y' in df.columns and '5Y' in df.columns:
        s5s30s = (df['30Y'] - df['5Y']).tail(252)
        fig.add_trace(
            go.Scatter(x=s5s30s.index, y=s5s30s, mode='lines',
                       line=dict(color='green'), name='5s30s'),
            row=2, col=1
        )

    fig.add_hline(y=0, line_dash="dash", line_color="black", row=2, col=1)
    
    comp = stats[['Current', f'{n_days}D_Min', f'{n_days}D_Max']].dropna()
    for col, color in zip([f'{n_days}D_Min', 'Current', f'{n_days}D_Max'], ['lightblue', 'blue', 'lightcoral']):
        fig.add_trace(
            go.Scatter(x=list(comp.index), y=comp[col], mode='lines+markers',
                       name=col, line=dict(color=color)),
            row=2, col=2
        )
    
    fig.update_layout(height=800, showlegend=True, title_text=f"Treasury Analysis - {datetime.now().strftime('%Y-%m-%d')}")
    fig.write_html('treasury_analysis_plotly.html')

def main():
    df = get_treasury_data(years=2)
    if not df.empty:
        stats = analyze_rates(df, n_days=90)
        plot_curve(df, stats, n_days=90)
        print("✅ Analysis Complete.")

if __name__ == "__main__":
    main()
