from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import yfinance as yf
import pandas as pd

app = FastAPI()

SECTORS = {
    "Banking": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS"],
    "IT Services": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "LTIM.NS"],
    "Crypto (24/7 Live)": ["BTC-USD", "ETH-USD", "DOGE-USD"]
}

COMMON_STYLE = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #f4f7f6; padding: 40px; color: #333; }
    .container { max-width: 950px; margin: auto; background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
    .status-box { padding: 25px; border-radius: 12px; margin: 20px 0; font-size: 22px; font-weight: bold; text-align: center; }
    .go { background: #d4edda; color: #155724; border: 2px solid #c3e6cb; }
    .caution { background: #fff3cd; color: #856404; border: 2px solid #ffeeba; }
    .no-go { background: #f8d7da; color: #721c24; border: 2px solid #f5c6cb; }
    .pros-cons-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 30px; }
    .box { padding: 20px; border-radius: 10px; min-height: 150px; }
    .pros { background: #eaffea; border-left: 5px solid #28a745; }
    .cons { background: #ffeaea; border-left: 5px solid #dc3545; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { border: 1px solid #ddd; padding: 12px; text-align: center; }
    th { background: #007bff; color: white; }
    .screener-btn { display: inline-block; background: #1a0dab; color: white; padding: 15px 30px; text-decoration: none; border-radius: 10px; font-weight: bold; margin-top: 30px; transition: 0.3s; }
    .screener-btn:hover { background: #000; transform: scale(1.05); }
</style>
"""

@app.get("/", response_class=HTMLResponse)
def home():
    sector_html = ""
    for sector, stocks in SECTORS.items():
        cards = "".join([f'<div style="background:white; padding:15px; border:1px solid #ddd; border-radius:10px; cursor:pointer; margin:5px; display:inline-block;" onclick="window.location=\'/stock/{s}\'"><b>{s.replace(".NS","")}</b></div>' for s in stocks])
        sector_html += f'<div><h3>{sector}</h3>{cards}</div>'
    return f"<html><head>{COMMON_STYLE}</head><body><div class='container'><h1>📊 AI Stock Analyzer v25</h1>{sector_html}</div></body></html>"

@app.get("/stock/{{symbol}}".replace("{{", "{").replace("}}", "}"), response_class=HTMLResponse)
def stock_detail(symbol: str):
    ticker = yf.Ticker(symbol)
    info = ticker.info
    q_fin = ticker.quarterly_financials
    
    if q_fin is None or q_fin.empty:
        return "<h1>Data Not Found</h1>"

    # --- 1. Quarterly Trend (Revenue Check) ---
    rev_row = q_fin.loc['Total Revenue'].dropna()
    go_count = 0
    trend_html = ""
    for i in range(min(len(rev_row) - 1, 3)):
        curr, prev = rev_row.iloc[i], rev_row.iloc[i+1]
        growth = ((curr - prev) / prev) * 100
        if growth > 0: go_count += 1
        color = "#28a745" if growth > 0 else "#dc3545"
        trend_html += f"<tr><td>{rev_row.index[i+1].strftime('%b %y')} vs {rev_row.index[i].strftime('%b %y')}</td><td style='color:{color}; font-weight:bold;'>{round(growth,2)}%</td></tr>"

    # --- 2. Deep Screener-Style Pros & Cons Analysis ---
    pros = []
    cons = []
    
    # PE Ratio
    pe = info.get('forwardPE') or info.get('trailingPE', 0)
    if 0 < pe < 25: pros.append("Attractive Valuation (Good PE Ratio)")
    elif pe > 45: cons.append(f"High PE Ratio ({round(pe, 2)}) - Overvalued")

    # Profit Margins
    margin = info.get('profitMargins', 0)
    if margin > 0.15: pros.append(f"Strong Profit Margins ({round(margin*100, 2)}%)")
    elif margin < 0.05: cons.append("Low Operating Margins")

    # Dividend
    if info.get('dividendYield', 0) > 0.02: pros.append("Healthy Dividend Payout")

    # Sales & Profit Growth (Long Term)
    rev_growth = info.get('revenueGrowth', 0)
    if rev_growth > 0.10: pros.append(f"Good Sales Growth ({round(rev_growth*100, 2)}%)")

    # --- 3. Cons Focus (Screener.in Specifics) ---
    # Interest Coverage Ratio
    icr = info.get('interestCoverage')
    if icr and icr < 2.0:
        cons.append(f"Low Interest Coverage Ratio ({round(icr, 2)})")
    
    # Contingent Liabilities & Other Income Logic
    # yfinance lo direct 'Contingent Liabilities' dorakadu, kani Net Income vs Free Cash Flow tho estimate cheyochu
    fcf = info.get('freeCashflow', 0)
    net_income = info.get('netIncomeToCommon', 0)
    if net_income > 0 and fcf < (net_income * 0.5):
        cons.append("Poor Cash Conversion (FCF is much lower than Net Income)")

    # Other Income Check
    # If Net Income is disproportionately higher than Operating Income
    ebitda = info.get('ebitda', 1)
    if net_income > ebitda:
        cons.append("Earnings include significant 'Other Income'")

    # --- 4. Final Smart Decision Logic ---
    score = go_count + len(pros) - len(cons)
    
    if score >= 4:
        status_class, rec = "go", "🚀 GO: Strong Fundamentals & Consistent Growth!"
    elif score >= 1:
        status_class, rec = "caution", "⚠️ WATCH: Fundamentals are stable but risks exist."
    else:
        status_class, rec = "no-go", "🛑 NO-GO: High Risk or Weak Fundamentals detected."

    clean_sym = symbol.replace(".NS", "")
    screener_url = f"https://www.screener.in/company/{clean_sym}/consolidated/"

    return f"""
    <html>
        <head>{COMMON_STYLE}</head>
        <body>
            <div class="container">
                <a href="/" style="text-decoration:none; color:#007bff; font-weight:bold;">← Back to Home</a>
                <h1>{clean_sym} In-depth Analysis</h1>
                
                <div class="status-box {status_class}">
                    {rec}
                </div>

                <div class="pros-cons-grid">
                    <div class="box pros">
                        <h3>✅ Pros (Strengths)</h3>
                        <ul>{"".join([f"<li>{p}</li>" for p in pros]) if pros else "<li>Analysis in progress...</li>"}</ul>
                    </div>
                    <div class="box cons">
                        <h3>❌ Cons (Risks)</h3>
                        <ul>{"".join([f"<li>{c}</li>" for c in cons]) if cons else "<li>No major risks identified by AI</li>"}</ul>
                    </div>
                </div>

                <h3 style="margin-top:30px;">Quarterly Revenue Trend</h3>
                <table>
                    <thead><tr><th>Comparison Period</th><th>Growth %</th></tr></thead>
                    <tbody>{trend_html}</tbody>
                </table>

                <div style="text-align:center;">
                    <a href="{screener_url}" target="_blank" class="screener-btn">
                        🔍 Confirm Details on Screener.in
                    </a>
                </div>
            </div>
        </body>
    </html>
    """