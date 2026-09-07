import streamlit as st
import json

st.set_page_config(page_title="CausalCollect Action Engine", layout="wide")

st.title("CausalCollect: Next Best Action Dashboard")
st.markdown("### Optimizing recovery net of cost, goodwill, and compliance.")

# --- Sidebar: Account State Simulator ---
st.sidebar.header("Account State Inputs")
account_id = st.sidebar.text_input("Account ID", value="ACC_99821")
dpd = st.sidebar.slider("Days Past Due (DPD)", 0, 180, 15)
bucket = st.sidebar.selectbox("Bucket", ["X", "1-30", "31-60", "61-90", "90+"])
salary_date_proximity = st.sidebar.slider("Days to Salary Credit", 0, 30, 5)
consent = st.sidebar.checkbox("DPDP Consent Given", value=True)
contacts_this_week = st.sidebar.slider("Contacts this week (FPC Limit)", 0, 3, 1)

# --- Mock Inference Logic ---
if st.sidebar.button("Generate Next Best Action"):
    # Mocking the calculation
    if not consent:
        action = "NO_ACTION"
        reason = "DPDP Consent Missing. Hard constraint triggered."
        net_val = 0
    elif contacts_this_week >= 2:
        action = "NO_ACTION"
        reason = "FPC Frequency Limit Reached. Hard constraint triggered."
        net_val = 0
    elif dpd < 30 and salary_date_proximity < 7:
        action = "WhatsApp"
        net_val = 250.50
        reason = "High uplift for low-cost digital channel. Salary credit imminent."
    elif dpd > 60:
        action = "Tele-call"
        net_val = 800.00
        reason = "High DPD requires human intervention. Uplift justifies tele-call cost."
    else:
        action = "AI Voice Bot"
        net_val = 450.00
        reason = "Optimal cost-to-uplift ratio. Empathetic tone advised."

    # --- Main Dashboard Output ---
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Recommended Action")
        st.success(f"**Channel:** {action}")
        if action != "NO_ACTION":
            st.write(f"**Timing:** Tomorrow, 11:00 AM - 12:00 PM")
            st.write(f"**Language:** Hindi")
            st.write(f"**Tone:** Empathetic")
        
        st.subheader("Audit-Grade Reason Codes")
        st.info(reason)

    with col2:
        st.subheader("Business Value")
        st.metric(label="Expected Net Value (₹)", value=f"{net_val:.2f}")
        st.metric(label="Confidence Score", value="85%")

    st.markdown("---")
    st.subheader("Champion-Challenger Tracker (Simulated)")
    chart_data = {"Metric": ["Incremental Resolution", "Cost per ₹ Recovered", "Complaint Rate"],
                  "Champion (Rule-based)": ["12%", "₹0.45", "2.1%"],
                  "Challenger (CausalCollect AI)": ["18%", "₹0.31", "1.4%"]}
    st.table(chart_data)