import pandas as pd
import plotly.graph_objects as go
import plotly.subplots as sp
from datetime import datetime, timedelta
import io
import requests

def get_fred_csv(series_id):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        df = pd.read_csv(io.StringIO(response.text))
        date_col = next((col for col in df.columns if 'DATE' in col.upper()), None)
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col])
            df.set_index(date_col, inplace=True)
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
    
    all_data = []
    for name, s_id in series.items():
        df_s = get_fred_csv(s_id)
        if not df_s.empty:
            df_s.columns = [name]
            all_data.append(df_s)
            
    if not all_data:
        return pd.DataFrame()
        
    df = pd.concat(all_data, axis=1).dropna(how='all')
    df = df[df.index >= start_date]
    df.ffill(inplace=True)
    
    return df

def plot_curve(df, n_days=90):
    stats = pd.DataFrame({
        'Current': df.iloc[-1],
        'Min': df.tail(n_days).min(),
        'Max': df.tail(n_days).max()
    })
    
    maturities = ['2Y', '5Y', '10Y', '30Y']
    y_vals = [stats['Current'][m] for m in maturities]
    
    fig = sp.make_subplots(
        rows=2, cols=2,
        subplot_titles=['Current Yield Curve', 'Historical Yields', '2s10s & 5s30s Spreads', f'Current vs {n_days}D Range']
    )
    
    fig.add_trace(go.Scatter(x=maturities, y=y_vals, mode='lines+markers+text',
                   text=[f'{y:.2f}%' for y in y_vals], textposition='top center',
                   line=dict(width=3, color='blue'), name='Current'), row=1, col=1)
    
    for m in maturities:
        fig.add_trace(go.Scatter(x=df.tail(252).index, y=df[m].tail(252), name=m), row=1, col=2)
    
    s2s10s = (df['10Y'] - df['2Y']).tail(252)
    s5s30s = (df['30Y'] - df['5Y']).tail(252)
    fig.add_trace(go.Scatter(x=s2s10s.index, y=s2s10s, name='2s10s', line=dict(color='red')), row=2, col=1)
    fig.add_trace(go.Scatter(x=s5s30s.index, y=s5s30s, name='5s30s', line=dict(color='green')), row=2, col=1)
    fig.add_hline(y=0, line_dash="dash", row=2, col=1)
    
    for col, color in zip(['Min', 'Current', 'Max'], ['lightblue', 'blue', 'lightcoral']):
        fig.add_trace(go.Scatter(x=maturities, y=stats[col], mode='lines+markers', name=col, line=dict(color=color)), row=2, col=2)
    
    fig.update_layout(height=800, template='plotly_white', showlegend=False)
    fig.write_html('treasury_yield_analysis.html')
    fig.show()

if __name__ == "__main__":
    data = get_treasury_data()
    if not data.empty:
        plot_curve(data)
