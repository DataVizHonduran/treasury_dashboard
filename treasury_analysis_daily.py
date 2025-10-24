"""
Daily US Treasury Yield Curve Analysis for GitHub Actions
Optimized for automated daily runs with data archiving
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.subplots as sp
from datetime import datetime, timedelta
import os

try:
    from pandas_datareader import data as pdr
except ImportError:
    print("❌ Install pandas_datareader: pip install pandas-datareader")
    exit()

try:
    import plotly
except ImportError:
    print("❌ Install plotly: pip install plotly")
    exit()

def get_treasury_data(years=2):
    """Get Treasury rates from FRED"""
    series = { '1Y': 'DGS1',
        '2Y': 'DGS2', '3Y': 'DGS3', '5Y': 'DGS5', '7Y': 'DGS7',
        '10Y': 'DGS10', '20Y': 'DGS20', '30Y': 'DGS30'
    }
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * years)
    
    print("🏛️  DAILY TREASURY ANALYSIS")
    print(f"📅 {end_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    print("Fetching Treasury rates from FRED...")
    
    data = {}
    
    for maturity, code in series.items():
        try:
            rates = pdr.get_data_fred(code, start_date, end_date)
            data[maturity] = rates[code]
            print(f"✓ {maturity}")
        except Exception as e:
            print(f"✗ {maturity}: {str(e)[:50]}...")
    
    if not data:
        print("❌ No data retrieved. Check connection to fred.stlouisfed.org")
        return pd.DataFrame()
    
    df = pd.DataFrame(data).dropna(how='all')
    print(f"✅ Got {len(df.columns)} rates, {len(df)} days")
    
    # Save raw data to CSV for archiving
    today_str = end_date.strftime('%Y%m%d')
    df.to_csv(f'treasury_data_{today_str}.csv')
    print(f"💾 Data saved to treasury_data_{today_str}.csv")
    
    return df

def analyze_rates(df, n_days=90):
    """Calculate statistics and display results"""
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
    
    # Display in maturity order
    order = ['1Y', '2Y', '3Y', '5Y', '7Y', '10Y', '20Y', '30Y']
    for maturity in order:
        if maturity in current.index:
            rate = current[maturity]
            print(f"{maturity:>3}: {rate:6.3f}%")
    
    # Key spreads with more detail
    if '2Y' in current.index and '10Y' in current.index:
        spread = current['10Y'] - current['2Y']
        print(f"\n📈 KEY SPREADS")
        print("-" * 20)
        print(f"2Y-10Y: {spread:+.3f}% ", end="")
        if spread < 0:
            print("(🔴 INVERTED)")
            inversion_status = "INVERTED"
        elif spread < 0.5:
            print("(🟡 FLAT)")
            inversion_status = "FLAT"
        else:
            print("(🟢 NORMAL)")
            inversion_status = "NORMAL"
    
    # Additional spreads
    if '3M' in current.index and '10Y' in current.index:
        spread_3m10y = current['10Y'] - current.get('3M', 0)
        print(f"3M-10Y: {spread_3m10y:+.3f}%")
    
    if '5Y' in current.index and '30Y' in current.index:
        spread_5y30y = current['30Y'] - current['5Y']
        print(f"5Y-30Y: {spread_5y30y:+.3f}%")
    
    print(f"\n📋 {n_days}-DAY STATISTICS")
    print("-" * 60)
    print(stats.round(3).to_string())
    
    # Save summary statistics
    today_str = datetime.now().strftime('%Y%m%d')
    summary_data = {
        'date': df.index[-1].strftime('%Y-%m-%d'),
        'inversion_status': inversion_status if '2Y' in current.index and '10Y' in current.index else 'N/A',
        '2Y_10Y_spread': spread if '2Y' in current.index and '10Y' in current.index else None,
        **{f'{maturity}_yield': current.get(maturity, None) for maturity in order}
    }
    
    summary_df = pd.DataFrame([summary_data])
    summary_df.to_csv(f'treasury_summary_{today_str}.csv', index=False)
    print(f"💾 Summary saved to treasury_summary_{today_str}.csv")
    
    return stats

def plot_curve(df, stats, n_days=90):
    """Create yield curve visualization with Plotly"""
    if df.empty:
        return
    
    # Maturity mapping for plotting
    maturity_map = {'1M': 1/12, '3M': 0.25, '6M': 0.5, '1Y': 1, '2Y': 2, 
                    '3Y': 3, '5Y': 5, '7Y': 7, '10Y': 10, '20Y': 20, '30Y': 30}
    
    current = stats['Current'].dropna()
    maturities = [m for m in current.index if m in maturity_map]
    x_vals = [maturity_map[m] for m in maturities]
    y_vals = [current[m] for m in maturities]
    
    # Create subplots
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    fig = sp.make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            'Current Yield Curve', 
            '252 Day Trends', 
            'Yield Curve Spread', 
            f'Current vs {n_days}D Range'
        ],
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # 1. Current yield curve with text labels
    fig.add_trace(
        go.Scatter(
            x=maturities,
            y=y_vals,
            mode='lines+markers+text',
            text=[f'{y:.2f}%' for y in y_vals],
            textposition='top center',
            line=dict(width=3, color='blue'),
            marker=dict(size=8),
            name='Current Yield',
            showlegend=False
        ),
        row=1, col=1
    )
    
    # 2. Historical trends
    recent_data = df.tail(252)
    colors = ['red', 'green', 'blue', 'orange']
    for i, rate in enumerate(['2Y', '5Y', '10Y', '30Y']):
        if rate in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=recent_data.index,
                    y=recent_data[rate],
                    mode='lines',
                    name=rate,
                    line=dict(width=2, color=colors[i % len(colors)]),
                    showlegend=False  # Will use annotation instead
                ),
                row=1, col=2
            )
    
    # 3. Yield spread
    if '10Y' in df.columns and '2Y' in df.columns:
        spread = (df['10Y'] - df['2Y']).tail(252)
        fig.add_trace(
            go.Scatter(
                x=spread.index,
                y=spread,
                mode='lines',
                line=dict(width=2, color='red'),
                fill='tonexty',
                fillcolor='rgba(255,0,0,0.3)',
                name='10Y-2Y Spread',
                showlegend=False
            ),
            row=2, col=1
        )
        
        # Add zero line
        fig.add_hline(y=0, line_dash="dash", line_color="black", 
                     opacity=0.7, row=2, col=1)
    
    # 4. Statistics comparison
    comparison = stats[['Current', f'{n_days}D_Min', f'{n_days}D_Max']].dropna()
    
    fig.add_trace(
        go.Scatter(
            x=list(comparison.index),
            y=comparison[f'{n_days}D_Min'],
            mode='lines+markers',
            name=f'{n_days}D Min',
            line=dict(width=2, color='lightblue'),
            opacity=0.7,
            showlegend=False
        ),
        row=2, col=2
    )
    
    fig.add_trace(
        go.Scatter(
            x=list(comparison.index),
            y=comparison['Current'],
            mode='lines+markers',
            name='Current',
            line=dict(width=3, color='blue'),
            showlegend=False
        ),
        row=2, col=2
    )
    
    fig.add_trace(
        go.Scatter(
            x=list(comparison.index),
            y=comparison[f'{n_days}D_Max'],
            mode='lines+markers',
            name=f'{n_days}D Max',
            line=dict(width=2, color='lightcoral'),
            opacity=0.7,
            showlegend=False
        ),
        row=2, col=2
    )
    
    # Update layout with daily timestamp
    fig.update_layout(
        title=dict(
            text=f'US Treasury Analysis - {today_str}',
            x=0.5,
            font=dict(size=16, family='Arial, sans-serif')
        ),
        height=800,
        showlegend=False
    )
    
    # Add individual legends as annotations
    fig.add_annotation(
        text="<b>2Y</b> <span style='color:red'>━━</span><br>" +
             "<b>5Y</b> <span style='color:green'>━━</span><br>" +
             "<b>10Y</b> <span style='color:blue'>━━</span><br>" +
             "<b>30Y</b> <span style='color:orange'>━━</span>",
        xref="paper", yref="paper",
        x=0.52, y=0.95,
        xanchor="left", yanchor="top",
        showarrow=False,
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="gray",
        borderwidth=1,
        font=dict(size=10)
    )
    
    fig.add_annotation(
        text="<b>Current</b> <span style='color:blue'>━━</span><br>" +
             f"<b>{n_days}D Min</b> <span style='color:lightblue'>━━</span><br>" +
             f"<b>{n_days}D Max</b> <span style='color:lightcoral'>━━</span>",
        xref="paper", yref="paper",
        x=0.52, y=0.45,
        xanchor="left", yanchor="top",
        showarrow=False,
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="gray",
        borderwidth=1,
        font=dict(size=10)
    )
    
    # Update axes labels
    fig.update_xaxes(title_text="Maturity", row=1, col=1)
    fig.update_yaxes(title_text="Yield (%)", row=1, col=1)
    
    fig.update_xaxes(title_text="Date", row=1, col=2)
    fig.update_yaxes(title_text="Yield (%)", row=1, col=2)
    
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="10Y-2Y Spread (%)", row=2, col=1)
    
    fig.update_xaxes(title_text="Maturity", row=2, col=2)
    fig.update_yaxes(title_text="Yield (%)", row=2, col=2)
    
    # Add grid to all subplots
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', griddash='dot')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', griddash='dot')
    
    # Save chart
    fig.write_html('treasury_analysis_plotly.html')
    print("✅ Interactive chart saved as 'treasury_analysis_plotly.html'")
    
    # Also save as PNG for GitHub display
    try:
        fig.write_image('treasury_analysis.png', width=1200, height=800, scale=2)
        print("✅ Static chart saved as 'treasury_analysis.png'")
    except Exception as e:
        print(f"⚠️  Could not save PNG (install kaleido for static images): {e}")

def main():
    """Run daily Treasury analysis"""
    # Default parameters for daily run
    n_days = 90  # 90-day statistics
    years = 2    # 2 years of historical data
    
    # Get data
    df = get_treasury_data(years)
    if df.empty:
        return
    
    # Analyze
    stats = analyze_rates(df, n_days)
    
    # Plot
    plot_curve(df, stats, n_days)
    
    print("\n" + "="*50)
    print("✅ DAILY TREASURY ANALYSIS COMPLETE")
    print("📁 Files generated:")
    print("   - treasury_analysis_plotly.html (interactive chart)")
    print("   - treasury_analysis.png (static image)")
    print("   - treasury_data_YYYYMMDD.csv (raw data)")
    print("   - treasury_summary_YYYYMMDD.csv (daily summary)")

if __name__ == "__main__":
    main()
