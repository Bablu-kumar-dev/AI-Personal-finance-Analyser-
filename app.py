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

# 1. PAGE CONFIGURATION
st.set_page_config(page_title=" AI Finance Analyser", page_icon="📊", layout="wide")

st.title("🧠 AI Personal Finance Analyser")
st.caption("Track your automated 2026 SIP portfolios, ledger entries, and liquid balances instantly.")

<<<<<<< HEAD
# Dashboard Layout Config (Wide mode is perfect for large data tables)
st.set_page_config(page_title="AI Personal Finance Analyzer", layout="wide", page_icon="📈")
st.title("📈 AI Personal Finance Analyzer")
st.write("Upload large-scale financial statements. Optimized with Pandas vector aggregation and smart AI chunking.")

uploaded_file = st.file_uploader("Upload your Bank Statement (CSV)", type=["csv"])

@st.cache_data
def clean_currency_string(val):
    if pd.isna(val) or str(val).strip() == "":
        return 0.0
    val_str = str(val).replace(" ", "").replace(",", "").replace("?", "")
    is_negative = "-" in val_str
    numeric_parts = "".join(re.findall(r'[0-9.]', val_str))
    if not numeric_parts:
        return 0.0
    try:
        amount = float(numeric_parts)
        return -amount if is_negative else amount
    except ValueError:
        return 0.0
        
   # Rule-based local pre-categorizer to process large rows instantly without hitting AI limits
def local_categorize(desc):
    """
    Rule-based local pre-categorizer with explicit handling for ICCL Mutual Fund SIPs and ICCW ATM Failed Transaction Refunds.
    """
    # Bulletproof text cleaning to remove copy-paste artifacts
    cleaned_desc = str(desc).upper()
    for artifact in ["MISCELLANEOUS", "THISUPIAB/", "THISUPIAR/", "ADD THIS IN TRANSPORT & COMMUTE"]:
        cleaned_desc = cleaned_desc.replace(artifact, "")
    cleaned_desc = cleaned_desc.strip()
    
    # 1.Transport & Commute
    if "BMTC BUS" in cleaned_desc or any(keyword in cleaned_desc for keyword in ["UBER", "OLA", "RAPIDO", "METRO", "TRAIN"]):
        return "Transport & Commute"
        
    # 2. Mutual Fund SIPs via ICCL (Indian Clearing Corporation Ltd)
    elif "ICCLDHR" in cleaned_desc or "INDIAN CLEARING CORP" in cleaned_desc:
        return "Investments & Trading"
        
    # 3. Other Stock Market Accounts
    elif any(keyword in cleaned_desc for keyword in ["MONEY LIC", "MONEYLICIOUS", "RAISE SECURITIES", "DS AXISCN", "RAISE SE", "RAISE.RZP1"]):
        return "Investments & Trading"
        
    # 4. Mobile Recharges & Utilities (FIXED TO UPPERCASE)
    elif any(keyword in cleaned_desc for keyword in ["JIO MOBIL", "JIO PREP", "AMAZON", "SMS CHARGES", "NEXTGENFASTFAS", "PAYTM-JIOMOBIL", "FLIPKART"]):
        return "Bills & Utilities"
        
    # 5. Cash Transactions & Physical Deposits
    elif any(keyword in cleaned_desc for keyword in ["BY CASH", "CARDLESS DEPOSIT", "CASH DEPOSITS"]):
        return "Cash Deposits"
        
    # 6. Standard Cardless ATM Withdrawals (Successful ones)
    elif "ICCW" in cleaned_desc:
        return "ATM Cash Withdrawals"
        
    # 7. Peer-to-Peer Transfers
    elif any(keyword in cleaned_desc for keyword in ["SANJAY K", "NARESH M", "BELA KUM", "BABLU KU", "MIHIR K", "GOURI PR", "RAKESH K", "MR RAMES", "ASMIT KU", "SUMAN KU", "RUDRA PR", "RANJIT K"]):
        return "Peer Transfers"
        
    # 8. Fixed Account Interest Credits
    elif "INT.PD" in cleaned_desc or "INT CARD" in cleaned_desc:
        return "Bank Interest Income"

    # 9. ATM Failed Transactions & Reversals (ICCW FA)
    if "ICCW FA" in cleaned_desc or "FAILED TRANSACTION" in cleaned_desc or "REFUND" in cleaned_desc:
        return "ATM Reversals & Refunds"
        
    return "Other Expenses"
=======
# 2. COMPLETE STATEMENT PROCESSING & PIPELINE ENGINE
def process_and_categorize_statement(df):
    """
    Dynamically maps columns, strips character noise, preserves negative mathematical signs 
    for debits, and enforces strict day-first Indian date parsing.
    """
    # Dynamic Column Matcher
    date_keywords = ['date', 'txn date', 'transaction date', 'value date']
    desc_keywords = ['desc', 'narration', 'particular', 'transaction details', 'remarks', 'description']
    amt_keywords = ['amount', 'amt', 'volume', 'transaction amount', 'credit/debit', 'balance']

    date_col = [c for c in df.columns if any(k in c.lower() for k in date_keywords)]
    desc_col = [c for c in df.columns if any(k in c.lower() for k in desc_keywords)]
    amt_col = [c for c in df.columns if any(k in c.lower() for k in amt_keywords)]

    # Fallback indexes if labels are completely generic
    date_col = date_col[0] if date_col else df.columns[0]
    desc_col = desc_col[0] if desc_col else (df.columns[1] if len(df.columns) > 1 else df.columns[0])
    amt_col = amt_col[0] if amt_col else (df.columns[2] if len(df.columns) > 2 else df.columns[-1])

    # Extract required series
    processed_df = df[[date_col, desc_col, amt_col]].copy()
    processed_df.columns = ['Date', 'Description', 'Amount']

    # Strict Day-First Indian Date Conversion (DD-MM-YYYY)
    processed_df['Date'] = pd.to_datetime(processed_df['Date'], dayfirst=True, errors='coerce')
    
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

    # Clean intermediate tracking flags
    processed_df = processed_df.drop(columns=['Amount_Str', 'Amount_Clean', 'Is_Debit'])

    # Local Rule-Based Keyword Router
    def local_categorize(raw_desc):
        cleaned = str(raw_desc).upper()
        # Instantly clear structural string noise from layout builders
        cleaned = re.sub(r'(MISCELLANEOUS|OTHER EXPENSES)', '', cleaned)
        # Normalize separators and unify the description for robust keyword matching
        cleaned = re.sub(r'[^A-Z0-9 ]+', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        if any(k in cleaned for k in ["ICCW FA", "FAILED TRANSACTION", "REFUND"]):
            return "ATM Reversals & Refunds"
        elif any(k in cleaned for k in ["ICCLDHR", "INDIAN CLEARING CORP", "MONEY LIC", "MONEYLICIOUS", "RAISE SECURITIES", "DS AXISCN"]):
            return "Investments & Trading"
        elif any(k in cleaned for k in ["JIO MOBIL", "JIO PREP", "AMAZON", "SMS CHARGES", "NEXTGENFASTFAS", "PAYTM JIOMOBIL", "FLIPKART"]):
            return "Bills & Utilities"
        elif any(k in cleaned for k in ["BY CASH", "CARDLESS DEPOSIT", "CASH DEPOSITS", "DEPOSIT"]):
            return "Cash Deposits"
        elif "ICCW" in cleaned:
            return "ATM Cash Withdrawals"
        elif any(k in cleaned for k in ["SANJAY K", "NARESH M", "BELA KUM", "BABLU KU", "MIHIR K", "GOURI PR", "RAKESH K", "ASMIT KU", "SUMAN KR", "MR RAMES", "RUDRA PR", "RANJIT K"]):
            return "Peer Transfers"
        elif "INT PD" in cleaned or "INT CARD" in cleaned:
            return "Bank Interest Income"
        if any(k in cleaned for k in ["BMTC BUS", "UBER", "OLA", "RAPIDO", "METRO", "TRAIN"]):
            return "Transport & Commute"
        return "Other Spending"

    processed_df['Category'] = processed_df['Description'].apply(local_categorize)
    total_net_volume = processed_df['Amount'].sum()
    
    return processed_df, total_net_volume

def build_financial_plan(monthly_income, savings_target, debt_payment=0.0):
    """Create a simple monthly financial plan from income, savings, and debt inputs."""
    monthly_income = float(monthly_income or 0.0)
    savings_target = float(savings_target or 0.0)
    debt_payment = float(debt_payment or 0.0)

    remaining_after_fixed = max(monthly_income - savings_target - debt_payment, 0.0)
    essentials = remaining_after_fixed * 0.55
    discretionary = remaining_after_fixed * 0.20
    emergency = remaining_after_fixed * 0.15
    buffer = max(remaining_after_fixed - essentials - discretionary - emergency, 0.0)

    plan_rows = [
        ("Savings & Investments", savings_target, "Build long-term wealth and secure future goals"),
        ("Debt Repayment", debt_payment, "Reduce liabilities and lower interest burden"),
        ("Essential Expenses", essentials, "Rent, groceries, bills, and transport"),
        ("Discretionary Spending", discretionary, "Dining, entertainment, shopping, and hobbies"),
        ("Emergency Buffer", emergency, "Unexpected expenses and medical needs"),
        ("Buffer / Miscellaneous", buffer, "Flexible cushion for irregular spending"),
    ]

    plan_df = pd.DataFrame(plan_rows, columns=["Category", "Planned Amount", "Advice"])
    plan_df["Planned Amount"] = plan_df["Planned Amount"].round(2)

    if monthly_income > 0:
        plan_df["Share of Income (%)"] = (plan_df["Planned Amount"] / monthly_income * 100).round(1)
    else:
        plan_df["Share of Income (%)"] = 0.0

    return plan_df

# 3. STREAMLIT FILE UPLOADER & INTERFACE
st.subheader("🧾 Financial Planning Assistant")
with st.form("financial_plan_form"):
    col_plan1, col_plan2, col_plan3 = st.columns(3)
    with col_plan1:
        monthly_income = st.number_input("Monthly income (₹)", min_value=0.0, step=1000.0, value=50000.0)
    with col_plan2:
        savings_target = st.number_input("Savings target (₹)", min_value=0.0, step=1000.0, value=10000.0)
    with col_plan3:
        debt_payment = st.number_input("Debt repayment (₹)", min_value=0.0, step=500.0, value=0.0)

    submitted = st.form_submit_button("Generate Financial Plan")

if submitted:
    plan_df = build_financial_plan(monthly_income, savings_target, debt_payment)
    st.dataframe(plan_df, width='stretch')
    st.bar_chart(plan_df, x="Category", y="Planned Amount", width='stretch')

uploaded_file = st.file_uploader("Upload your transaction CSV/Excel Statement data", type=["csv", "xlsx"])
>>>>>>> feature1

if uploaded_file is not None:
    # Read layout formats safely
    if uploaded_file.name.endswith('.csv'):
        raw_df = pd.read_csv(uploaded_file)
    else:
        raw_df = pd.read_excel(uploaded_file)

    # Run processing engine
    clean_df, continuous_calculated_total = process_and_categorize_statement(raw_df)

    # Split dashboard calculations accurately
    total_income = clean_df[clean_df['Amount'] > 0]['Amount'].sum()
    total_expenses = clean_df[clean_df['Amount'] < 0]['Amount'].sum()

    # ==========================================
    # 4. REFACTORED KPI CALCULATIONS (SPLITTING OUT SIPs)
    # ==========================================
    # 1. Total Inflows (Interest, Deposits, etc.)
    total_income = clean_df[clean_df['Amount'] > 0]['Amount'].sum()
    
    # 2. Wealth Accumulation (Only Investments & SIPs)
    # Detect SIPs inside investment descriptions (common keywords) and split them out
    sip_keywords = ['SIP', 'AUTO DEBIT', 'SYSTEMATIC', 'SIP-']
    def is_sip(row):
        desc = str(row['Description']).upper()
        cat = row['Category']
        if cat == 'Investments & Trading' and any(k in desc for k in sip_keywords):
            return True
        return False

    clean_df['Is_SIP'] = clean_df.apply(is_sip, axis=1)

    total_sips = clean_df[clean_df['Is_SIP']]['Amount'].sum()
    total_invested = clean_df[(clean_df['Category'] == 'Investments & Trading') & (~clean_df['Is_SIP'])]['Amount'].sum()
    
    # 3. True Operational Expenses (Everything else that is negative)
    total_expenses = clean_df[
        (clean_df['Amount'] < 0) & 
        (clean_df['Category'] != 'Investments & Trading')
    ]['Amount'].sum()
    
    # 4. Ultimate Liquid Variance (-6,172.64)
    net_variance = clean_df['Amount'].sum()

    # --- UI Layout Render ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📥 Total Income Tracked", f"₹{total_income:,.2f}")
    col2.metric("💸 Core Expenses (Outlays)", f"₹{abs(total_expenses):,.2f}")
    col3.metric("📈 Asset Building (SIPs)", f"₹{abs(total_sips):,.2f}")
    col4.metric("💼 Other Investments", f"₹{abs(total_invested):,.2f}")

    # Secondary KPIs row
    net_col1, net_col2, net_col3, net_col4 = st.columns(4)
    net_col1.metric("⚖️ Net Cashflow Change", f"₹{net_variance:,.2f}", delta=f"₹{net_variance:,.2f}")
    net_col2.metric("📈 Total Invested (All)", f"₹{abs(total_sips + total_invested):,.2f}")
    
    # 5. DATA EXPLORER GRAPHICS
    st.subheader("📊 Expense Distribution by Volume")
    chart_data = clean_df.groupby('Category')['Amount'].sum().reset_index()
    # Force visualization numbers positive for rendering clean bars
    chart_data['Absolute Volume'] = chart_data['Amount'].abs()
    st.bar_chart(data=chart_data, x='Category', y='Absolute Volume', width='stretch')

    st.subheader("🔍 Interactive Data Explorer")
    st.dataframe(clean_df, width='stretch')

    # 6. GENERATE SCRIPT SUMMARY PACK FOR THE LLM PROMPT
    summary_metrics = clean_df.groupby('Category')['Amount'].agg(['count', 'sum']).to_string()

    # Integrated System Prompt Template
    ai_prompt = f"""
    You are an expert Indian personal finance portfolio manager and accounting auditor reviewing a user's bank statement metrics.
    Analyze the data and structure your response EXACTLY into the specified headings. Do not modify layout tags.

    CRITICAL SYSTEM LAWS:
    1. CURRENCY: Prefix every single monetary balance with the Indian Rupee symbol (₹). Never use dollars ($).
    2. THE INVESTMENT LAW: Outflows under 'Investments & Trading' (negative sum balances) indicate wealth asset formation like Mutual Fund SIPs via ICCL AND RAISE SECURITIES. Do not describe this as a loss—praise it as disciplined capital compounding.
    3. MATHEMATICAL ACCURACY: The precise absolute net change calculated by the ledger engine is strictly ₹{continuous_calculated_total:,.2f}. Frame all text paragraphs completely around this reality.

    ---
    EXPECTED FORMAT STRUCTURE:
    
    ### 📊 Portfolio Data Summary
    (Provide a clean markdown table breaking down category distributions)

    ### 🧠  AI finance Analytics Report
    > **Executive Financial Health Note:** (Summary of balance changes)

    #### 1. Strategic Investment & Capital Formation
    (Analysis of SIP wealth creation and broker account transactions)

    #### 2. Cash Flow & Liquidity Management
    (Analysis of ATM, cash entries, and bills stability)

    ### 📈 Actionable Portfolio Recommendations
    - (2-3 targeted portfolio health bullets)
    ---

    Metrics Dataset to Analyze:
    {summary_metrics}
    """

    # 7. EXECUTING DEPLOYED AI REVIEW
    if st.button("Run AI Financial Diagnostics"):
        if not OPENAI_AVAILABLE:
            st.error("The `openai` Python package is not installed in this environment. Install it with `pip install openai` and restart the app.")
        else:
<<<<<<< HEAD
            df['Net_Amount'] = df[df.columns[2]].apply(clean_currency_string)

        # Calculate or extract Running Balance
        balance_cols = [col for col in df.columns if 'balance' in col.lower()]
        if balance_cols:
            df['Calculated_Balance'] = df[balance_cols[0]].apply(clean_currency_string)
        else:
            df['Calculated_Balance'] = df['Net_Amount'].cumsum()

        # Handle Timestamps
        df['Parsed_Date'] = pd.to_datetime(df[date_col], format='%d-%m-%Y', errors='coerce')
        df_clean_dates = df.dropna(subset=['Parsed_Date']).sort_values('Parsed_Date')

        # 4. FAST LOCAL CATEGORIZATION ENGINE
        df_clean_dates['Category'] = df_clean_dates[desc_col].apply(local_categorize)

        # 5. HIGH-LEVEL KPI METRICS
        total_income = df_clean_dates[df_clean_dates['Net_Amount'] > 0]['Net_Amount'].sum()
        total_expense = df_clean_dates[df_clean_dates['Net_Amount'] < 0]['Net_Amount'].sum()
        
        last_month_spending = 0.0
        last_month_name = "N/A"
        
        if not df_clean_dates.empty:
            latest_date = df_clean_dates['Parsed_Date'].max()
            df_clean_dates['YearMonth'] = df_clean_dates['Parsed_Date'].dt.to_period('M')
            latest_month_period = latest_date.to_period('M')
            latest_month_data = df_clean_dates[df_clean_dates['YearMonth'] == latest_month_period]
            last_month_spending = latest_month_data[latest_month_data['Net_Amount'] < 0]['Net_Amount'].sum()
            last_month_name = latest_date.strftime('%B %Y')

        # Display Metrics Dashboard
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Income Tracked", f"₹{total_income:,.2f}")
        col2.metric("Total Overall Expenses", f"₹{abs(total_expense):,.2f}")
        col3.metric(f"Spending in {last_month_name}", f"₹{abs(last_month_spending):,.2f}")
        latest_balance = df_clean_dates['Calculated_Balance'].iloc[-1] if not df_clean_dates.empty else 0.0
        col4.metric("Final Statement Balance", f"₹{latest_balance:,.2f}")
        
        st.markdown("---")
        
        # --- GRAPH LAYOUTS FOR BIG DATA ---
        chart_col, table_col = st.columns([1, 1])
        
        with chart_col:
            st.subheader("📊 Expense Distribution by Volume")
            # Group rows locally first before making charts to prevent browser lag
            expense_summary = df_clean_dates[df_clean_dates['Net_Amount'] < 0].groupby('Category')['Net_Amount'].sum().abs().reset_index()
            if not expense_summary.empty:
                fig_bar = px.bar(expense_summary, x='Category', y='Net_Amount', color='Category',
                                 text_auto='.2s', title="Total Spent per Category",
                                 color_discrete_sequence=px.colors.qualitative.Safe)
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No expense data found to plot.")
                
        with table_col:
            st.subheader("🔍 Interactive Data Explorer")
            # Added a quick dropdown filter so you can sift through huge files easily
            selected_cat = st.selectbox("Filter view by Category:", ["All Categories"] + list(df_clean_dates['Category'].unique()))
            
            filtered_df = df_clean_dates
            if selected_cat != "All Categories":
                filtered_df = df_clean_dates[df_clean_dates['Category'] == selected_cat]
                
            st.dataframe(filtered_df[[date_col, desc_col, 'Category', 'Net_Amount', 'Calculated_Balance']], use_container_width=True, height=260)
            
        st.markdown("---")
        
        # --- BIG DATA SMART AI INTERFACE ---
        st.subheader("🧠 AI Personal Finance Analyzer")
        if st.button("🚀 Run AI Analysis on Data Summary"):
            with st.spinner("AI is evaluating financial trends from compressed data summaries..."):
                try:
                    # SMART CHUNKING: Group data by category and calculate counts and sums
                    # This shrinks 10,000 lines into just 5 clean lines for the AI prompt!
                    ai_summary = df_clean_dates.groupby('Category').agg(
                        Transaction_Count=('Net_Amount', 'count'),
                        Total_Net_Volume=('Net_Amount', 'sum')
                    ).reset_index().to_string(index=False)

                    prompt = f"""
You are an expert Indian financial analytics assistant.
Analyze the following summarized banking transaction dataset.

CRITICAL INSTRUCTIONS FOR CURRENCY FORMATTING:
- NEVER use the dollar sign ($) anywhere in your analysis.
- Keep the exact raw numeric values from the data but swap the symbol. For example, if you calculate 4,200, display it strictly as \u20b94,200 (DO NOT convert \u20b94,200 into $50 USD).
- Every single monetary transaction value, budget cap, or total breakdown figure MUST be prefixed with the Indian Rupee symbol (\u20b9).

Data Summary:
{ai_summary}
"""
                    
                    response = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": "You are a strategic corporate financial advisor."},
                            {"role": "user", "content": prompt}
                        ],
                        model="gpt-4o-mini"
                    )
                    
                    st.success("Analysis Complete!")
                    st.markdown(response.choices[0].message.content)
                    
                except Exception as ai_err:
                    st.error(f"AI Matrix Exception: {ai_err}")
                    
    except Exception as e:
        st.error(f"Execution Error: {e}")
else:
    st.info("💡 Please upload your CSV file to test true database auto-categorization.")
=======
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
>>>>>>> feature1
