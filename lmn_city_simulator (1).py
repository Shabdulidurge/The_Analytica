import streamlit as st # type: ignore
import pandas as pd # type: ignore
import numpy as np # type: ignore

st.set_page_config(layout="wide")
st.title("LMN Smart City – Live Command & Control Simulator")

zones = ["Zone 1","Zone 2","Zone 3","Zone 4","Zone 5"]

# ---------------------------------
# Session State
# ---------------------------------
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame({
        "Zone": zones,
        "Traffic": np.random.randint(80,140,size=5),
        "Complaints": np.random.randint(20,80,size=5)
    })

if "smart_signal" not in st.session_state:
    st.session_state.smart_signal = {z: False for z in zones}

if "mode" not in st.session_state:
    st.session_state.mode = "Live Control"


# ---------------------------------
# Core Simulation Engine
# ---------------------------------
def simulate():
    df = st.session_state.data.copy()

    for i,row in df.iterrows():
        zone = row["Zone"]

        # Natural city drift
        traffic_change = np.random.choice([-6,-3,0,3,6], p=[0.1,0.2,0.3,0.25,0.15])
        complaint_change = np.random.choice([-4,-2,0,2,4], p=[0.15,0.25,0.3,0.2,0.1])

        # Intervention effect
        if st.session_state.smart_signal[zone]:
            traffic_change -= np.random.choice([4,6,8], p=[0.4,0.4,0.2])
            complaint_change -= np.random.choice([2,3,4], p=[0.5,0.3,0.2])

        df.loc[i,"Traffic"] = np.clip(row["Traffic"] + traffic_change, 40, 200)
        df.loc[i,"Complaints"] = np.clip(row["Complaints"] + complaint_change, 0, 150)

    st.session_state.data = df


# ---------------------------------
# Sidebar Controls
# ---------------------------------
st.sidebar.header("City Controls")

# Mode Selector
st.session_state.mode = st.sidebar.radio(
    "What-If Mode",
    ["Live Control", "Do Nothing", "AI Auto-Control"]
)

# Disable manual control unless Live Control
disabled = st.session_state.mode != "Live Control"

selected_zones = st.sidebar.multiselect(
    "Zones with Smart Signals ON",
    zones,
    default=[z for z,v in st.session_state.smart_signal.items() if v],
    disabled=disabled
)

# Only allow manual control in Live Control
if st.session_state.mode == "Live Control":
    for z in zones:
        st.session_state.smart_signal[z] = z in selected_zones

# Next tick
if st.sidebar.button("Next 5 Minutes"):
    if st.session_state.mode == "Do Nothing":
        for z in zones:
            st.session_state.smart_signal[z] = False

    elif st.session_state.mode == "AI Auto-Control":
        temp = st.session_state.data.copy()
        temp["Risk"] = temp["Traffic"]*0.6 + temp["Complaints"]*0.4

        for i,row in temp.iterrows():
            st.session_state.smart_signal[row["Zone"]] = row["Risk"] > 100

    simulate()

# 30-min What-If run
if st.sidebar.button("Simulate 30 Minutes"):
    for _ in range(6):

        if st.session_state.mode == "Do Nothing":
            for z in zones:
                st.session_state.smart_signal[z] = False

        elif st.session_state.mode == "AI Auto-Control":
            temp = st.session_state.data.copy()
            temp["Risk"] = temp["Traffic"]*0.6 + temp["Complaints"]*0.4

            for i,row in temp.iterrows():
                st.session_state.smart_signal[row["Zone"]] = row["Risk"] > 100

        simulate()


# ---------------------------------
# Risk Engine
# ---------------------------------
df = st.session_state.data.copy()
df["Risk Score"] = (df["Traffic"]*0.6 + df["Complaints"]*0.4).astype(int)

df["Status"] = np.where(df["Risk Score"]>100,"🔴 High Risk",
                 np.where(df["Risk Score"]>70,"🟡 Medium","🟢 Normal"))


# ---------------------------------
# Display
# ---------------------------------
st.subheader("Live Zone Status")
st.dataframe(df, use_container_width=True)

st.subheader("Risk Zones")
st.table(df[["Zone","Traffic","Complaints","Risk Score","Status"]])

col1,col2,col3 = st.columns(3)
col1.metric("City Avg Traffic", int(df["Traffic"].mean()))
col2.metric("City Avg Complaints", int(df["Complaints"].mean()))
col3.metric("High Risk Zones", int((df["Risk Score"]>100).sum()))

# ---------------------------------
# What-If Outcome
# ---------------------------------
st.subheader("What-If Outcome")
high_risk = (df["Risk Score"] > 100).sum()

if st.session_state.mode == "Do Nothing":
    st.error(f"Without intervention: {high_risk} zones in high-risk condition")
elif st.session_state.mode == "AI Auto-Control":
    st.success(f"With AI intervention: {high_risk} zones in high-risk condition")
else:
    st.info("Live control mode — human operators in charge")


# ---------------------------------
# AI City Planner
# ---------------------------------
st.subheader("🤖 AI City Planner Recommendations")

for i,row in df.iterrows():
    zone = row["Zone"]

    if row["Risk Score"] > 100 and not st.session_state.smart_signal[zone]:
        st.error(f"{zone}: HIGH risk. Recommend activating smart signals + deploying crews.")
    elif row["Risk Score"] > 100:
        st.warning(f"{zone}: Smart signals active. Monitoring impact.")
    elif row["Risk Score"] > 70:
        st.info(f"{zone}: Rising risk. Prepare intervention.")
    else:
        st.success(f"{zone}: Stable.")
