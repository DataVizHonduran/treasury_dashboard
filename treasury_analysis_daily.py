import pandas as pd
import plotly.graph_objects as go
import plotly.subplots as sp
from datetime import datetime, timedelta
import yfinance as yf

def get_treasury_data(years=2):
    series = {
        '13W': '^IRX',
        '5Y': '^FVX',
        '10Y': '^TNX',
        '30Y': '^TYX'
    }
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * years)
    
    print("🏛️  DAILY TREASURY YIELD ANALYSIS")
    print(f"📅 {end_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    data = {}
    for maturity, ticker in series.items():
        try:
            df_ticker = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if not df_ticker.empty:
                data[maturity] = df_ticker['Close'] / 10
                print(f"✓ {maturity}")
        except Exception as e:
            print(f"✗ {maturity}: {str(e)[:50]}...")
    
    if not data:
        return pd.DataFrame()
    
    df = pd.concat(data, axis=1).dropna(how='all')
    df.columns = data.keys()
    today_str = end_date.strftime('%Y%m%d')
    df.to_csv(f'treasury_yields_{today_str}.csv')
    
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
        f'{n_days}D_Median': recent.median()
    })
    
    print(f"\n📊 YIELD SNAPSHOT ({df.index[-1].strftime('%Y-%m-%d')})")
    print("=" * 50)
    for maturity in ['13W', '5Y', '10Y', '30Y']:
        if maturity in current.index:
            print(f"{maturity:>3}: {current[maturity]:.3f}%")
    
    s13w10s = current['10Y'] - current['13W'] if '13W' in current and '10Y' in current else None
    s5s30s = current['30Y'] - current['5Y'] if '5Y' in current and '30Y' in current else None
    
    print(f"\n📈 KEY SPREADS")
    print("-" * 20)
    if s13w10s is not None: print(f"13w10s: {s13w10s:+.3f}%")
    if s5s30s is not None: print(f"5s30s:  {s5s30s:+.3f}%")
    
    return stats

def plot_curve(df, stats, n_days=90):
    if df.empty:
        return
    
    maturity_map = {'13W': 0.25, '5Y': 5, '10Y': 10, '30Y': 30}
    current = stats['Current'].dropna()
    maturities = [m for m in current.index if m in maturity_map]
    y_vals = [current[m] for m in maturities]
    
    fig = sp.make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            'Current Yield Curve', 
            'Historical Yield Trends', 
            '13w10s & 5s30s Spreads', 
            f'Current vs {n_days}D Range'
        ]
    )
    
    fig.add_trace(
        go.Scatter(x=maturities, y=y_vals, mode='lines+markers+text',
                   text=[f'{y:.2f}%' for y in y_vals], textposition='top center',
                   line=dict(width=3, color='blue'), name='Current Yield'),
        row=1, col=1
    )
    
    recent_data = df.tail(252)
    colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA']
    for i, m in enumerate(['13W', '5Y', '10Y', '30Y']):
        if m in df.columns:
            fig.add_trace(
                go.Scatter(x=recent_data.index, y=recent_data[m], mode='lines',
                           name=m, line=dict(width=2, color=colors[i])),
                row=1, col=2
            )
    
    if '10Y' in df.columns and '13W' in df.columns:
        s13w10s = (df['10Y'] - df['13W']).tail(252)
        fig.add_trace(go.Scatter(x=s13w10s.index, y=s13w10s, name='13w10s', line=dict(color='red')), row=2, col=1)
        
    if '30Y' in df.columns and '5Y' in df.columns:
        s5s30s = (df['30Y'] - df['5Y']).tail(252)
        fig.add_trace(go.Scatter(x=s5s30s.index, y=s5s30s, name='5s30s', line=dict(color='green')), row=2, col=1)

    fig.add_hline(y=0, line_dash="dash", line_color="black", row=2, col=1)
    
    comp = stats[['Current', f'{n_days}D_Min', f'{n_days}D_Max']].dropna()
    for col, color in zip([f'{n_days}D_Min', 'Current', f'{n_days}D_Max'], ['lightblue', 'blue', 'lightcoral']):
        fig.add_trace(
            go.Scatter(x=list(comp.index), y=comp[col], mode='lines+markers',
                       name=col, line=dict(color=color)),
            row=2, col=2
        )
    
    fig.update_layout(height=800, template='plotly_white', title_text=f"US Treasury Yield Analysis - {datetime.now().strftime('%Y-%m-%d')}")
    fig.update_yaxes(title_text="Yield (%)")
    fig.write_html('treasury_yield_analysis.html')

def main():
    df = get_treasury_data(years=2)
    if not df.empty:
        stats = analyze_rates(df, n_days=90)
        plot_curve(df, stats, n_days=90)
        print("\n✅ Yield Analysis Complete. Files saved.")

if __name__ == "__main__":
    main()
