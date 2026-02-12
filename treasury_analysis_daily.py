import pandas as pd
import requests
import io
import plotly.graph_objects as go
import plotly.subplots as sp
from datetime import datetime, timedelta

def get_fred_csv(series_id):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    response = requests.get(url)
    if response.status_code == 200:
        df = pd.read_csv(io.StringIO(response.text), index_col='DATE', parse_dates=True)
        df.replace('.', pd.NA, inplace=True)
        return df.astype(float)
    return pd.DataFrame()

def get_treasury_data(years=2):
    series = {
        '2Y': 'DGS2',
        '5Y': 'DGS5',
        '10Y': 'DGS10',
        '30Y': 'DGS30'
    }
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * years)
    
    print("🏛️  DAILY TREASURY YIELD ANALYSIS (FRED DIRECT)")
    print(f"📅 {end_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    all_data = []
    for name, s_id in series.items():
        print(f"Fetching {name}...")
        df_s = get_fred_csv(s_id)
        if not df_s.empty:
            df_s.columns = [name]
            all_data.append(df_s)
            
    if not all_data:
        return pd.DataFrame()
        
    df = pd.concat(all_data, axis=1).dropna(how='all')
    df = df[df.index >= start_date]
    df.fillna(method='ffill', inplace=True)
    
    return df

def analyze_rates(df, n_days=90):
    if df.empty: return
    recent = df.tail(n_days)
    current = df.iloc[-1]
    
    stats = pd.DataFrame({
        'Current': current,
        f'{n_days}D_Max': recent.max(),
        f'{n_days}D_Min': recent.min()
    })
    
    print(f"\n📊 YIELD SNAPSHOT ({df.index[-1].strftime('%Y-%m-%d')})")
    print("=" * 50)
    for m in ['2Y', '5Y', '10Y', '30Y']:
        print(f"{m:>3}: {current[m]:.3f}%")
        
    print(f"\n📈 KEY SPREADS")
    print("-" * 20)
    print(f"2s10s: {current['10Y'] - current['2Y']:+.3f}%")
    print(f"5s30s: {current['30Y'] - current['5Y']:+.3f}%")
    
    return stats

def plot_curve(df, stats, n_days=90):
    maturities = ['2Y', '5Y', '10Y', '30Y']
    y_vals = [stats['Current'][m] for m in maturities]
    
    fig = sp.make_subplots(
        rows=2, cols=2,
        subplot_titles=['Current Yield Curve', 'Historical Yields', '2s10s & 5s30s Spreads', f'Current vs {n_days}D Range']
    )
    
    fig.add_trace(go.Scatter(x=maturities, y=y_vals, mode='lines+markers+text',
                   text=[f'{y:.2f}%' for y in y_vals], textposition='top center',
                   line=dict(width=3, color='blue'), name='Current'), row=1, col=1)
    
    recent_data = df.tail(252)
    for m in maturities:
        fig.add_trace(go.Scatter(x=recent_data.index, y=recent_data[m], name=m, mode='lines'), row=1, col=2)
    
    s2s10s = (df['10Y'] - df['2Y']).tail(252)
    s5s30s = (df['30Y'] - df['5Y']).tail(252)
    fig.add_trace(go.Scatter(x=s2s10s.index, y=s2s10s, name='2s10s', line=dict(color='red')), row=2, col=1)
    fig.add_trace(go.Scatter(x=s5s30s.index, y=s5s30s, name='5s30s', line=dict(color='green')), row=2, col=1)
    fig.add_hline(y=0, line_dash="dash", line_color="black", row=2, col=1)
    
    for col, color in zip([f'{n_days}D_Min', 'Current', f'{n_days}D_Max'], ['lightblue', 'blue', 'lightcoral']):
        fig.add_trace(go.Scatter(x=maturities, y=stats[col], mode='lines+markers', name=col, line=dict(color=color)), row=2, col=2)
    
    fig.update_layout(height=800, template='plotly_white', showlegend=False)
    fig.write_html('treasury_direct_fred.html')

def main():
    df = get_treasury_data(years=2)
    if not df.empty:
        stats = analyze_rates(df)
        plot_curve(df, stats)
        print("\n✅ Success. Chart saved to 'treasury_direct_fred.html'")

if __name__ == "__main__":
    main()
