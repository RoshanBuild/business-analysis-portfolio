import streamlit as st
import pandas as pd

# Page setup
st.set_page_config(
    page_title="AI Payment Dispute Platform",
    page_icon="💳",
    layout="wide"
)

# Load dataset
@st.cache_data
def load_data():
    try:
        return pd.read_csv("../data/payment_dispute_data.csv", encoding="utf-8")
    except UnicodeDecodeError:
        return pd.read_csv("../data/payment_dispute_data.csv", encoding="latin1")

df = load_data()

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        "Executive Dashboard",
        "Dispute Case List",
        "AI Triage",
        "Refund Eligibility Checker",
        "SLA Checker",
        "Customer Response Generator"
    ]
)

# Main title
st.title("AI-Assisted Digital Payment Dispute & Refund Management Platform")
st.caption("Technical Business Analyst Portfolio Prototype | Built by Roshan Thakur")

# Page 1: Executive Dashboard
if page == "Executive Dashboard":
    st.header("Executive Dashboard")

    total_cases = len(df)

    if "SLA_Breach" in df.columns:
        sla_breaches = df[df["SLA_Breach"] == "Yes"].shape[0]
        sla_breach_rate = round((sla_breaches / total_cases) * 100, 2)
    else:
        sla_breaches = 0
        sla_breach_rate = 0

    if "Refund_Amount" in df.columns:
        total_refund_value = round(df["Refund_Amount"].sum(), 2)
    else:
        total_refund_value = 0

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Dispute Cases", total_cases)
    col2.metric("SLA Breach Rate", f"{sla_breach_rate}%")
    col3.metric("Total Refund Value", f"£{total_refund_value}")

    st.subheader("Dispute Type Breakdown")
    if "Dispute_Type" in df.columns:
        dispute_counts = df["Dispute_Type"].value_counts()
        st.bar_chart(dispute_counts)

    st.subheader("Risk Level Breakdown")
    if "Risk_Level" in df.columns:
        risk_counts = df["Risk_Level"].value_counts()
        st.bar_chart(risk_counts)

    st.subheader("Dataset Preview")
    st.dataframe(df.head(20), use_container_width=True)


# Page 2: Dispute Case List
elif page == "Dispute Case List":
    st.header("Dispute Case List")

    st.write("This page allows users to view dispute cases in a structured case management format.")

    search_text = st.text_input("Search by Case ID, Customer ID, Dispute Type or Status")

    if search_text:
        filtered_df = df[df.astype(str).apply(
            lambda row: row.str.contains(search_text, case=False, na=False).any(),
            axis=1
        )]
    else:
        filtered_df = df

    st.dataframe(filtered_df, use_container_width=True)


# Page 3: AI Triage
elif page == "AI Triage":
    st.header("AI-Assisted Dispute Triage")

    st.write("Enter a customer dispute message. The prototype will classify the dispute using simple rule-based AI-style logic.")

    customer_message = st.text_area(
        "Customer dispute message",
        placeholder="Example: My money was debited but the payment failed."
    )

    if st.button("Classify Dispute"):
        message = customer_message.lower()

        if "failed" in message or "debited" in message:
            dispute_type = "Failed Payment"
            assigned_team = "Payment Operations"
            risk_level = "Medium"
        elif "duplicate" in message or "twice" in message:
            dispute_type = "Duplicate Debit"
            assigned_team = "Payment Operations"
            risk_level = "Medium"
        elif "unauthorised" in message or "fraud" in message or "not me" in message:
            dispute_type = "Unauthorised Transaction"
            assigned_team = "Fraud Review"
            risk_level = "High"
        elif "merchant" in message or "not credited" in message:
            dispute_type = "Merchant Not Credited"
            assigned_team = "Merchant Support"
            risk_level = "Medium"
        elif "refund" in message or "delay" in message:
            dispute_type = "Refund Delay"
            assigned_team = "Refund Support"
            risk_level = "Low"
        else:
            dispute_type = "Unclear / Manual Review Required"
            assigned_team = "Customer Support"
            risk_level = "Medium"

        st.success("AI-style triage completed")

        col1, col2, col3 = st.columns(3)
        col1.metric("Suggested Dispute Type", dispute_type)
        col2.metric("Assigned Team", assigned_team)
        col3.metric("Risk Level", risk_level)

        st.info("Note: This is decision-support only. Final decision must remain with an authorised human user.")


# Page 4: Refund Eligibility Checker
elif page == "Refund Eligibility Checker":
    st.header("Refund Eligibility Checker")

    dispute_type = st.selectbox(
        "Select dispute type",
        [
            "Failed Payment",
            "Duplicate Debit",
            "Refund Delay",
            "Merchant Not Credited",
            "Unauthorised Transaction",
            "Customer Error",
            "Other"
        ]
    )

    transaction_status = st.selectbox(
        "Transaction status",
        ["Failed", "Success", "Pending"]
    )

    evidence_available = st.selectbox(
        "Evidence available?",
        ["Yes", "No", "Partial"]
    )

    risk_level = st.selectbox(
        "Risk level",
        ["Low", "Medium", "High"]
    )

    transaction_amount = st.number_input(
        "Transaction amount (£)",
        min_value=0.0,
        value=100.0
    )

    if st.button("Check Refund Recommendation"):
        if risk_level == "High":
            recommendation = "Manual Review Required"
            reason = "High-risk cases must be reviewed by a human user."
        elif transaction_amount > 500:
            recommendation = "Manager Approval Required"
            reason = "High-value cases require manager approval."
        elif evidence_available == "No":
            recommendation = "Awaiting Evidence"
            reason = "Evidence is required before refund decision."
        elif transaction_status == "Failed" and evidence_available == "Yes":
            recommendation = "Eligible"
            reason = "Payment failed and supporting evidence is available."
        elif dispute_type == "Duplicate Debit" and evidence_available == "Yes":
            recommendation = "Eligible"
            reason = "Duplicate debit confirmed with evidence."
        elif dispute_type == "Customer Error":
            recommendation = "Not Eligible"
            reason = "Customer error is not normally refund eligible."
        else:
            recommendation = "Manual Review Required"
            reason = "Case requires further investigation."

        st.subheader("Refund Recommendation")
        st.success(recommendation)
        st.write("Reason:", reason)

        st.warning("AI/automation should support the decision only. Final refund approval must remain with an authorised user.")


# Page 5: SLA Checker
elif page == "SLA Checker":
    st.header("SLA Breach Checker")

    sla_target_days = st.number_input(
        "SLA target days",
        min_value=1,
        value=3
    )

    actual_resolution_days = st.number_input(
        "Actual resolution days",
        min_value=0,
        value=4
    )

    if st.button("Check SLA Status"):
        if actual_resolution_days > sla_target_days:
            st.error("SLA Breach: Yes")
            st.write("The case exceeded the target resolution time.")
        else:
            st.success("SLA Breach: No")
            st.write("The case was resolved within the SLA target.")


# Page 6: Customer Response Generator
elif page == "Customer Response Generator":
    st.header("AI-Assisted Customer Response Generator")

    customer_name = st.text_input("Customer name", value="Customer")
    dispute_type = st.selectbox(
        "Dispute type",
        [
            "Failed Payment",
            "Duplicate Debit",
            "Refund Delay",
            "Merchant Not Credited",
            "Unauthorised Transaction",
            "Other"
        ]
    )

    case_status = st.selectbox(
        "Case status",
        [
            "Received",
            "Under Review",
            "Awaiting Evidence",
            "Refund Approved",
            "Refund Rejected",
            "Escalated"
        ]
    )

    if st.button("Generate Customer Response"):
        response = f"""
Dear {customer_name},

Thank you for contacting us regarding your {dispute_type.lower()} case.

Your case is currently marked as: {case_status}.

Our team is reviewing the details and will provide an update as soon as possible. If further evidence is required, we will contact you with clear instructions.

Please note that refund and fraud-related decisions are reviewed by authorised team members before a final outcome is confirmed.

Kind regards,  
Payment Dispute Support Team
"""

        st.text_area("Suggested Customer Response", response, height=250)