import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import random
import os
import time
from datetime import datetime

# --- CORE BACKEND INTEGRATIONS ---
import database_manager
import notifications
import predictor
import styles
from core import parallel_risk, risk_engine
from core.investment_mix_calculator import InvestmentMixCalculator

# --- INITIALIZATION ---
st.set_page_config(page_title="Crypto Portfolio Manager", layout="wide", initial_sidebar_state="expanded")
st.markdown(styles.get_css(), unsafe_allow_html=True)
database_manager.init_db()

# --- SESSION STATE MANAGEMENT ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False
if "temp_email" not in st.session_state:
    st.session_state.temp_email = ""

# --- CONTROLLED PIPELINE FUNCTION ---
def run_pipeline(user_email):
    """
    Single controlled entry-point for data refresh.
    ONLY called by the Sync button — never automatically.
    """
    from core import collect_data
    collect_data.fetch_latest_prices()
    database_manager.process_all_risk_alerts(user_email)
    st.session_state.last_updated = datetime.now().strftime("%H:%M:%S")

# --- AUTHENTICATION VIEW ---
def auth_view():
    st.title("Welcome to Crypto Portfolio Manager")
    st.write("Please log in or register to access your professional dashboard.")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login", key="btn_login"):
            res = database_manager.authenticate_user(email, password)
            if res["authenticated"]:
                if res["is_verified"]:
                    st.session_state.authenticated = True
                    st.session_state.user_email = email
                    st.rerun()
                else:
                    st.warning("Account not verified. Please register again to get a new OTP.")
            else:
                st.error("Invalid email or password.")
                
    with tab2:
        st.subheader("Register")
        if not st.session_state.otp_sent:
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Password", type="password", key="reg_pass")
            if st.button("Send OTP", key="btn_send_otp"):
                otp = str(random.randint(1000, 9999))
                if database_manager.create_user(reg_email, reg_password, otp):
                    notifications.send_otp(reg_email, otp)
                    st.session_state.temp_email = reg_email
                    st.session_state.otp_sent = True
                    st.success("OTP Sent! Check your email.")
                    st.rerun()
                else:
                    st.error("Email already exists or error occurred.")
        else:
            st.write(f"OTP sent to {st.session_state.temp_email}")
            otp_input = st.text_input("Enter 4-digit OTP:", key="otp_input")
            if st.button("Verify", key="btn_verify_otp"):
                if database_manager.verify_user(st.session_state.temp_email, otp_input):
                    st.success("Verification successful! You can now log in.")
                    st.session_state.otp_sent = False
                else:
                    st.error("Invalid OTP.")

# --- DATA HELPERS ---
@st.cache_data
def load_market_data():
    """Loads current market prices from the CSV (READ-ONLY, no DB)."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "data", "market_snapshot.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        np.random.seed(42)
        df['Price Change (24h)'] = [round(random.uniform(-10, 15), 2) for _ in range(len(df))]
        return df
    return pd.DataFrame()

def get_current_price(coin_id):
    """Helper to fetch a specific coin's live price."""
    df = load_market_data()
    if not df.empty:
        match = df[df['coin_id'] == coin_id]
        if not match.empty:
            return match.iloc[0]['current_price']
    return 0.0

# --- DASHBOARD PAGE ---
def page_dashboard():
    st.title("Investment Terminal Dashboard")
    st.write(f"Welcome back, **{st.session_state.user_email}**")
    
    # NO auto-pipeline execution here.
    # Data is fetched ONLY when user clicks "Sync Live Prices" in sidebar.
    
    # Fetch live user data (READ-ONLY queries)
    portfolio = database_manager.get_live_portfolio(st.session_state.user_email)
    threshold = database_manager.get_settings(st.session_state.user_email)
    
    # RISK SENTINEL — display only, no DB writes
    latest_alert = database_manager.get_latest_active_alert(st.session_state.user_email)
    if latest_alert:
        st.warning(f"🚨 Market Alert: {latest_alert['coin_id'].upper()} dropped {latest_alert['drop_pct']:.2f}%")
    
    # --- PERFORMANCE KPI METRICS ---
    last_upd = st.session_state.get('last_updated', 'Click Sync to refresh')
    st.subheader(f"Portfolio Performance (Last Updated: {last_upd})")
    
    total_value = sum(item["quantity"] * item["current_price"] for item in portfolio)
    total_invested = sum(item["quantity"] * item["purchase_price"] for item in portfolio)
    pl_val = total_value - total_invested
    pl_pct = (pl_val / total_invested * 100) if total_invested else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("🟢 Live Balance", f"${total_value:,.2f}", f"{pl_pct:+.2f}%")
    col2.metric("Total Invested", f"${total_invested:,.2f}")
    col3.metric("Net Profit / Loss", f"${pl_val:+,.2f}")
    
    st.markdown("---")
    
    # --- INVESTMENT CONSOLE ---
    with st.expander("➕ Add New Investment", expanded=True):
        st.info("ℹ️ Strategy Guide: Conservative (70% BTC/ETH), Balanced (50/50), Aggressive (70% Altcoins).")
        df_market = load_market_data()
        coins = df_market['coin_id'].tolist() if not df_market.empty else ["bitcoin"]
        
        with st.form("invest_form"):
            col_a, col_b = st.columns([1, 1])
            with col_a:
                selected_coin = st.selectbox("Select Asset to Base Focus", coins, key="invest_coin_select")
            with col_b:
                inv_amt = st.number_input("Capital to Allocate (USD)", min_value=10.0, value=1000.0, step=100.0, key="invest_amount_input")
            
            st.write("Select Strategy to Automate Diversification:")
            c1, c2, c3 = st.columns(3)
            btn_cons = c1.form_submit_button("🛡️ Conservative")
            btn_bal = c2.form_submit_button("⚖️ Balanced")
            btn_agg = c3.form_submit_button("🔥 Aggressive")
            
            if btn_cons or btn_bal or btn_agg:
                strategy = "Low" if btn_cons else "Medium" if btn_bal else "High"
                with st.spinner(f"Computing {strategy} Allocations..."):
                    historical_data = risk_engine.load_data()
                    risk_metrics = parallel_risk.compute_risk_metrics_parallel(historical_data)
                    
                    calc = InvestmentMixCalculator(risk_metrics, inv_amt, strategy)
                    allocations = calc.calculate_allocation()
                    
                    if allocations:
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        for alloc in allocations:
                            if alloc["allocated_amount"] > 0:
                                c_id = alloc["coin_id"]
                                c_price = get_current_price(c_id)
                                if c_price > 0:
                                    qty = alloc["allocated_amount"] / c_price
                                    database_manager.add_to_portfolio(st.session_state.user_email, c_id, qty, c_price, now)
                        st.success(f"{strategy} Strategy Executed!")
                        st.rerun()
    
    # --- LIVE HOLDINGS & DONUT CHART ---
    st.subheader("Personal Asset Allocation")
    col_alloc, col_holdings = st.columns([1, 2])
    
    with col_alloc:
        if portfolio:
            df_port = pd.DataFrame(portfolio)
            df_port['Live Value'] = df_port['quantity'] * df_port['current_price']
            fig = px.pie(df_port, values='Live Value', names='name', hole=0.4,
                         template="plotly_dark", color_discrete_sequence=px.colors.sequential.Teal)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("Awaiting Capital Deployment...")
            
    with col_holdings:
        if portfolio:
            h_cols = st.columns([2, 2, 2, 2, 1])
            h_cols[0].write("**Asset**")
            h_cols[1].write("**Qty & Purchase Price**")
            h_cols[2].write("**Live Valuation**")
            h_cols[3].write("**ROI (%)**")
            h_cols[4].write("**Action**")
            st.markdown("<hr style='margin:0.2em 0; border-color:#4a5568;'>", unsafe_allow_html=True)
            
            for idx, item in enumerate(portfolio):
                qty = item['quantity']
                live_p = item['current_price']
                purch_p = item['purchase_price']
                val = qty * live_p
                roi_pct = ((live_p - purch_p) / purch_p) * 100 if purch_p > 0 else 0
                
                c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
                c1.write(f"**{item['name'].upper()}**")
                c2.write(f"{qty:.4f} units @ ${purch_p:,.2f}")
                c3.write(f"**${val:,.2f}**")
                
                color = 'green' if roi_pct >= 0 else 'red'
                c4.markdown(f"<span style='color:{color}; font-weight:bold;'>{roi_pct:+.2f}%</span>", unsafe_allow_html=True)
                
                with c5:
                    if st.button("🗑️", key=f"liq_{item['id']}_{idx}", type="primary", help="Sell & Remove Asset"):
                        database_manager.remove_asset(item['id'], st.session_state.user_email)
                        st.toast("Asset Liquidated. Balance Updated.")
                        st.rerun()
                st.markdown("<hr style='margin:0.2em 0; border-color:#2d3748;'>", unsafe_allow_html=True)
        else:
            st.write("No assets held.")

# --- MARKET ANALYSIS PAGE ---
def page_market():
    st.title("Market Analysis")
    df = load_market_data()
    
    if df.empty:
        st.error("Market data missing. Click 'Sync Live Prices' first.")
        return
        
    st.write("Global Market Live Tracker")
    def color_change(val):
        return f'color: {"green" if val > 0 else "red"}'
        
    styled_df = df[['symbol', 'name', 'current_price', 'market_cap', 'Price Change (24h)']].style.map(
        color_change, subset=['Price Change (24h)']
    ).format({
        'current_price': '${:.2f}',
        'market_cap': '${:,.0f}',
        'Price Change (24h)': '{:+.2f}%'
    })
    
    st.dataframe(styled_df, width='stretch', height=600)

# --- RISK & VOLATILITY PAGE ---
def page_risk():
    st.title("Risk & Volatility Engine")
    st.write("Multithreaded analysis calculating statistical variance (Volatility).")
    
    if st.button("Execute Statistical Analysis", key="btn_risk_analysis"):
        with st.spinner("Crunching historical variance..."):
            market_data = risk_engine.load_data()
            if not market_data:
                st.error("Historical data missing!")
                return
            results = parallel_risk.compute_risk_metrics_parallel(market_data)
            
        st.success("Analysis complete!")
        df_risk = pd.DataFrame(results)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Asset Volatility Comparison")
            fig_bar = px.bar(df_risk.sort_values('volatility', ascending=False), 
                             x='coin_id', y='volatility', color='risk_category',
                             template="plotly_dark", color_discrete_map={"High":"red", "Medium":"orange", "Low":"green"})
            st.plotly_chart(fig_bar, width='stretch')
            
        with col2:
            st.subheader("Global Market Risk Gauge")
            avg_vol = df_risk['volatility'].mean()
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = avg_vol * 100,
                gauge = {
                    'axis': {'range': [0, 10]},
                    'steps': [
                        {'range': [0, 3], 'color': "green"},
                        {'range': [3, 6], 'color': "orange"},
                        {'range': [6, 10], 'color': "red"}
                    ]
                }
            ))
            fig_gauge.update_layout(template="plotly_dark")
            st.plotly_chart(fig_gauge, width='stretch')

# --- AI PREDICTION PAGE ---
def page_prediction():
    st.title("AI Machine Learning Predictor")
    st.write("Predicting the next 7 days using Scikit-Learn Linear Regression.")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    hist_path = os.path.join(base_dir, "data", "historical_prices.csv")
    
    if not os.path.exists(hist_path):
        st.error("Historical data missing.")
        return
        
    df = pd.read_csv(hist_path)
    coins = df['coin_id'].unique()
    selected_coin = st.selectbox("Select Asset for AI Forecasting:", coins, key="predict_coin_select")
    
    if st.button("Generate AI Forecast", key="btn_ai_forecast"):
        with st.spinner(f"Training ML Model for {selected_coin}..."):
            future_dates, predictions = predictor.get_7day_prediction(selected_coin)
            
        if future_dates is None:
            st.error("Prediction failed. Data formatting error.")
            return
            
        df_coin = df[df['coin_id'] == selected_coin].copy()
        df_coin['date'] = pd.to_datetime(df_coin['date'])
        df_coin = df_coin.sort_values('date').tail(60) 
        from core.risk_engine import parse_price
        df_coin['close'] = df_coin['close'].apply(parse_price)
        df_coin = df_coin.dropna(subset=['close'])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_coin['date'], y=df_coin['close'], mode='lines', name='Historical'))
        fig.add_trace(go.Scatter(x=future_dates, y=predictions, 
                mode='lines+markers', name='7-Day Prediction',
                line=dict(color='yellow', dash='dot')))
                
        fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=True)
        st.plotly_chart(fig, width='stretch')

# --- SETTINGS PAGE ---
def page_settings():
    st.title("System Configuration")
    
    st.subheader("Risk Alert Threshold")
    current_thresh = database_manager.get_settings(st.session_state.user_email)
    new_thresh = st.slider("Alert if asset drops by (%)", 1.0, 50.0, float(current_thresh))
    
    if st.button("Update Security Protocol", key="btn_update_threshold"):
        database_manager.update_settings(st.session_state.user_email, new_thresh)
        st.success(f"Threshold updated to {new_thresh}%")
        
    st.markdown("---")
    
    st.subheader("Investment Compliance Reporting")
    col1, col2 = st.columns(2)
    with col1:
        st.write("Download a professional PDF Audit Report of your current net exposure.")
        if st.button("🛠️ Generate Audit PDF", key="btn_gen_pdf"):
            with st.spinner("Assembling PDF via FPDF..."):
                portfolio = database_manager.get_live_portfolio(st.session_state.user_email)
                total_val = sum(i["quantity"] * i["current_price"] for i in portfolio)
                total_inv = sum(i["quantity"] * i["purchase_price"] for i in portfolio)
                
                pl_summary = {
                    "Total Investment": f"${total_inv:,.2f}",
                    "Current Value": f"${total_val:,.2f}",
                    "Net P/L": f"${(total_val - total_inv):,.2f}"
                }
                outlook = "Market data indicates sustained volatility. Maintain threshold security."
                
                filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audit_report.pdf")
                status = notifications.generate_pdf_report(st.session_state.user_email, portfolio, pl_summary, outlook, filepath)
                
            if status and os.path.exists(filepath):
                with open(filepath, "rb") as f:
                    st.download_button("💾 Save PDF Report", f, "audit_report.pdf", "application/pdf")

# --- MAIN ROUTING ---
if not st.session_state.authenticated:
    auth_view()
else:
    with st.sidebar:
        st.title("System Navigator")

        # SYNC BUTTON — the ONLY way to trigger pipeline execution
        if st.button("🔄 Sync Live Prices", width='stretch', key="btn_sync_prices"):
            with st.spinner("Syncing live market data..."):
                run_pipeline(st.session_state.user_email)
            st.cache_data.clear()  # Clear cached CSV so fresh data is loaded
            st.success(f"✅ Synced at {st.session_state.last_updated}")
            # NO st.rerun() — avoids infinite rerun loops
                
        page = st.radio("Go to module:", ["Dashboard", "Market Analysis", "Risk & Volatility", "AI Prediction", "Settings"])
        
        if st.button("Secure Logout", key="btn_logout"):
            st.session_state.authenticated = False
            st.rerun()

    if page == "Dashboard": page_dashboard()
    elif page == "Market Analysis": page_market()
    elif page == "Risk & Volatility": page_risk()
    elif page == "AI Prediction": page_prediction()
    elif page == "Settings": page_settings()