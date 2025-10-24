# 🏛️ Daily US Treasury Yield Curve Analysis

[![Daily Treasury Analysis](https://img.shields.io/badge/Treasury-Dashboard-blue)](https://datavizhonduran.github.io/treasury_dashboard/treasury_analysis_plotly.html)

Automated daily analysis of US Treasury yield curves using real-time data from the Federal Reserve Economic Data (FRED). This repository generates interactive charts and data summaries every day after market close.

## 🔄 Automated Daily Updates

This analysis runs automatically every day at **6:00 PM EST** (after US markets close) using GitHub Actions. You can also trigger it manually from the Actions tab.

## 📊 What's Generated Daily

### Interactive Charts
- **Current Yield Curve**: Today's rates across all maturities
- **252-Day Historical Trends**: Rolling year view of key rates (2Y, 5Y, 10Y, 30Y)
- **Yield Spread Analysis**: 10Y-2Y spread with inversion detection
- **Statistical Comparison**: Current rates vs 90-day min/max ranges

### Data Files
- `treasury_analysis_plotly.html` - Interactive Plotly chart
- `treasury_analysis.png` - Static image for quick viewing
- `treasury_data_YYYYMMDD.csv` - Raw daily data
- `treasury_summary_YYYYMMDD.csv` - Key metrics summary

## 🚨 Yield Curve Status

The analysis automatically detects and reports:
- 🟢 **NORMAL**: 2Y-10Y spread > 0.5%
- 🟡 **FLAT**: 2Y-10Y spread 0% to 0.5%
- 🔴 **INVERTED**: 2Y-10Y spread < 0% (recession indicator)

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

---

**📧 Questions?** Open an issue or contact [@DataVizHonduran](https://github.com/DataVizHonduran)

*Automated analysis powered by GitHub Actions* 🤖
