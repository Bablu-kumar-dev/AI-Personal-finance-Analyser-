import streamlit as st
import pandas as pd
import numpy as np
import re
try:
    import openai
    OPENAI_AVAILABLE = True
except Exception:
    openai = None
    OPENAI_AVAILABLE = False

# OpenAI authentication support from environment or Streamlit secrets
OPENAI_API_KEY = None
if OPENAI_AVAILABLE:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY') or os.getenv('ADMIN_API_KEY')
    if not OPENAI_API_KEY and hasattr(st, 'secrets'):
        try:
            OPENAI_API_KEY = st.secrets.get('OPENAI_API_KEY')
        except Exception:
            OPENAI_API_KEY = None
    if OPENAI_API_KEY:
        openai.api_key = OPENAI_API_KEY

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="Luxuryverce AI Finance Analyser", page_icon="📊", layout="wide")

st.title("🧠 AI Personal Finance Analyser")
st.caption("Track your automated 2026 SIP portfolios, ledger entries, and liquid balances instantly.")

# 2. COMPLETE STATEMENT PROCESSING & PIPELINE ENGINE
def process_and_categorize_statement(df):
    """
    Dynamically maps columns, strips character noise, preserves negative mathematical signs 
    for debits, and enforces strict day-first Indian date parsing.
    """
    date_keywords = ['date', 'txn date', 'transaction date', 'value date']
    desc_keywords = ['desc', 'narration', 'particular', 'transaction details', 'remarks', 'description']
    amt_keywords = ['amount', 'amt', 'volume', 'transaction amount', 'credit/debit', 'balance']

    date_col = [c for c in df.columns if any(k in c.lower() for k in date_keywords)]
    desc_col = [c for c in df.columns if any(k in c.lower() for k in desc_keywords)]
    amt_col = [c for c in df.columns if any(k in c.lower() for k in amt_keywords)]

    # Fallback indexes if labels are missing
    date_col = date_col[0] if date_col else df.columns[0]
    desc_col = desc_col[0] if desc_col else (df.columns[1] if len(df.columns) > 1 else df.columns[0])
    amt_col = amt_col[0] if amt_col else (df.columns[2] if len(df.columns) > 2 else df.columns[-1])

    processed_df = df[[date_col, desc_col, amt_col]].copy()
    processed_df.columns = ['Date', 'Description', 'Amount']

    # Strict Day-First Indian Date Conversion (DD-MM-YYYY)
    processed_df['Date'] = pd.to_datetime(
        processed_df['Date'], format='mixed', dayfirst=True, errors='coerce'
    )
    
    # Capture Debit vs Credit indicators before removing symbols
    processed_df['Amount_Str'] = processed_df['Amount'].astype(str)
    processed_df['Is_Debit'] = processed_df['Amount_Str'].str.contains(r'-|DR|DEBIT', case=False, regex=True)

    # Sanitize and convert numeric values
    processed_df['Amount_Clean'] = processed_df['Amount_Str'].str.replace(r'[₹\$,\s\-]', '', regex=True)
    processed_df['Amount'] = pd.to_numeric(processed_df['Amount_Clean'], errors='coerce').fillna(0.0)

    # Re-apply negative math values strictly to Debits/Expenses
    processed_df['Amount'] = processed_df.apply(
        lambda row: -row['Amount'] if row['Is_Debit'] else row['Amount'], axis=1
    )

    processed_df = processed_df.drop(columns=['Amount_Str', 'Amount_Clean', 'Is_Debit'])

    # Local Rule-Based Keyword Router
    def local_categorize(raw_desc):
        cleaned = str(raw_desc).upper()
        cleaned = re.sub(r'(MISCELLANEOUS|OTHER EXPENSES)', '', cleaned).strip()
        
        if any(k in cleaned for k in ["ICCW FA", "FAILED TRANCATION", "REFUND"]):
            return "ATM Reversals & Refunds"
        elif any(k in cleaned for k in ["ICCLDHR", "INDIAN CLEARING CORP", "MONEY LIC", "MONEYLICIOUS", "RAISE SECURITIES", "DS AXISCN"]):
            return "Investments & Trading"
        elif any(k in cleaned for k in ["JIO MOBIL", "JIO PREP", "AMAZON", "SMS CHARGES", "NEXTGENFASTFAS"]):
            return "Bills & Utilities"
        elif any(k in cleaned for k in ["BY CASH", "CARDLESS DEPOSIT", "CASH DEPOSITS", "DEPOSIT"]):
            return "Cash Deposits"
        elif "ICCW" in cleaned:
            return "ATM Cash Withdrawals"
        elif any(k in cleaned for k in ["SANJAY K", "NARESH M", "BELA KUM", "BABLU KU", "MIHIR K", "GOURI PR", "RAKESH K", "ASMIT KU"]):
            return "Peer Transfers"
        elif "INT.PD" in cleaned or "INT CARD" in cleaned:
            return "Bank Interest Income"
        
        return "Other Expenses"

    processed_df['Category'] = processed_df['Description'].apply(local_categorize)
    total_net_volume = processed_df['Amount'].sum()
    
    return processed_df, total_net_volume

# 3. STREAMLIT FILE UPLOADER & INTERFACE
uploaded_file = st.file_uploader("Upload your transaction CSV/Excel Statement data", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.lower().endswith('.csv'):
            bytes_data = uploaded_file.read()
            
            try:
                decoded_text = bytes_data.decode('utf-8')
            except UnicodeDecodeError:
                decoded_text = bytes_data.decode('latin-1', errors='replace')

            cleaned_text = decoded_text.replace('\xa0', ' ').replace('\r\n', '\n')
            
            try:
                raw_df = pd.read_csv(
                    io.StringIO(cleaned_text), 
                    engine='python', 
                    on_bad_lines='skip',
                    skipinitialspace=True
                )
            except Exception:
                lines = cleaned_text.split('\n')
                header_idx = 0
                for idx, line in enumerate(lines[:20]):
                    if any(k in line.lower() for k in ['date', 'particulars', 'narration', 'amount', 'description', 'txn']):
                        header_idx = idx
                        break
                
                raw_df = pd.read_csv(
                    io.StringIO('\n'.join(lines[header_idx:])), 
                    engine='python', 
                    on_bad_lines='skip',
                    skipinitialspace=True
                )
        else:
            raw_df = pd.read_excel(uploaded_file)

    except Exception as parse_err:
        st.error(f"⚠️ Unable to parse statement layout: {parse_err}. Please ensure it is a valid CSV or XLSX file.")
        st.stop()

    # Process and sanitize data
    clean_df, continuous_calculated_total = process_and_categorize_statement(raw_df)

    # Split calculations
    total_income = clean_df[clean_df['Amount'] > 0]['Amount'].sum()
    total_invested = clean_df[clean_df['Category'] == 'Investments & Trading']['Amount'].sum()
    total_expenses = clean_df[
        (clean_df['Amount'] < 0) & 
        (clean_df['Category'] != 'Investments & Trading')
    ]['Amount'].sum()
    net_variance = clean_df['Amount'].sum()

    # 4. KPI VALUE LAYOUT DISPLAY
    st.success(f"Successfully optimized and indexed {len(clean_df)} financial transaction rows!")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📥 Total Income", f"₹{total_income:,.2f}")
    col2.metric("💸 Operational Expenses", f"₹{abs(total_expenses):,.2f}")
    col3.metric("📈 Investments (SIPs)", f"₹{abs(total_invested):,.2f}")
    col4.metric("⚖️ Net Cashflow Change", f"₹{net_variance:,.2f}")

    # 5. DATA EXPLORER GRAPHICS
    st.subheader("📊 Expense & Asset Distribution")
    chart_data = clean_df.groupby('Category')['Amount'].sum().reset_index()
    chart_data['Absolute Volume'] = chart_data['Amount'].abs()
    st.bar_chart(data=chart_data, x='Category', y='Absolute Volume', use_container_width=True)

    st.subheader("🔍 Interactive Data Explorer")
    st.dataframe(clean_df, use_container_width=True)

    # 6. AI ANALYSIS & FINANCIAL PLANNER TABS
    summary_metrics = clean_df.groupby('Category')['Amount'].agg(['count', 'sum']).to_string()

    ai_prompt = f"""
    You are an expert Indian personal finance portfolio manager and accounting auditor.
    Analyze the following statement metrics and provide strategic insight.

    CRITICAL LAWS:
    1. CURRENCY: Prefix every single monetary balance with the Indian Rupee symbol (₹).
    2. THE INVESTMENT LAW: Treat 'Investments & Trading' outlays as asset creation, not consumer losses.
    3. ACCURACY: The precise net cashflow change is ₹{continuous_calculated_total:,.2f}.

    Summary Metrics:
    {summary_metrics}
    """

    # 7. EXECUTING DEPLOYED AI REVIEW
    if st.button("Run AI Financial Diagnostics"):
        if not OPENAI_AVAILABLE:
            st.error("The `openai` Python package is not installed in this environment. Install it with `pip install openai` and restart the app.")
        else:
            st.write("### 🧠 AI Personal Finance Analyzer Running...")
            try:
                # Connects directly to your configured dashboard setup
                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": ai_prompt}]
                )
                st.markdown(response.choices[0].message.content)
            except Exception as e:
                st.error(f"AI Diagnostics Connection Error: {e}")