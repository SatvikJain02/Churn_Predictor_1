import streamlit as st
import requests

# ---------------- CONFIGURATION ---------------- #
BASE_URL = "http://127.0.0.1:8000"  # Ensure your FastAPI is running here

st.set_page_config(
    page_title="Churn Predictor 😈",
    page_icon="🔮",
    layout="centered"
)

# ---------------- SESSION STATE ---------------- #
if 'token' not in st.session_state:
    st.session_state['token'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None

# ---------------- FUNCTIONS ---------------- #
def login_user(username, password):
    try:
        res = requests.post(f"{BASE_URL}/login", json={"username": username, "password": password})
        if res.status_code == 200:
            data = res.json()
            st.session_state['token'] = data['access_token']
            st.session_state['username'] = username
            st.success(f"Welcome back, {username}! 😈")
            st.rerun()
        else:
            st.error("Invalid credentials! The gatekeeper rejects you.")
    except Exception as e:
        st.error(f"Connection failed: {e}")

def register_user(username, password):
    try:
        res = requests.post(f"{BASE_URL}/register", json={"username": username, "password": password})
        if res.status_code == 200:
            st.success("Registration successful! You may now login.")
        else:
            st.error(res.json().get('detail', 'Registration failed'))
    except Exception as e:
        st.error(f"Connection failed: {e}")

def logout():
    st.session_state['token'] = None
    st.session_state['username'] = None
    st.rerun()

# ---------------- UI LOGIC ---------------- #

# 1. SIDEBAR NAVIGATION
if st.session_state['token']:
    st.sidebar.title(f"User: {st.session_state['username']}")
    if st.sidebar.button("Logout 🚪"):
        logout()
else:
    st.sidebar.title("Access Control")
    choice = st.sidebar.radio("Navigate", ["Login", "Register"])

# 2. MAIN CONTENT
st.title("🔮 The Diabolical Churn Predictor")
st.markdown("---")

if not st.session_state['token']:
    # --- AUTH INTERFACE ---
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("Username")
    with col2:
        password = st.text_input("Password", type="password")

    if choice == "Login":
        if st.button("Enter the Void (Login)"):
            login_user(username, password)
    else:
        if st.button("Join the Cult (Register)"):
            register_user(username, password)

else:
    # --- PREDICTION DASHBOARD ---
    st.subheader("📝 Customer Details")
    
    with st.form("predict_form"):
        c1, c2 = st.columns(2)
        
        # Mapping inputs exactly to the Pydantic Aliases in main.py
        with c1:
            age = st.number_input("Age", min_value=3, max_value=110, value=20)
            gender = st.selectbox("Gender", ["Male", "Female"])
            tenure = st.number_input("Tenure (Months)", min_value=1.0, max_value=60.0, value=30.0)
            usage = st.number_input("Usage Frequency", min_value=1.0, max_value=30.0, value=15.0)
            calls = st.number_input("Support Calls", min_value=0.0, max_value=10.0, value=5.0)
            
        with c2:
            delay = st.number_input("Payment Delay", min_value=0.0, max_value=30.0, value=15.0)
            sub_type = st.selectbox("Subscription Type", ["Standard", "Basic", "Premium"])
            contract = st.selectbox("Contract Length", ["Annual", "Monthly", "Quarterly"])
            spend = st.number_input("Total Spend", min_value=100.0, max_value=1000.0, value=550.0)
            last_inter = st.number_input("Last Interaction", min_value=1.0, max_value=30.0, value=15.0)

        submit = st.form_submit_button("🔮 Predict Fate")

    if submit:
        # Construct payload using keys matching 'alias' in Pydantic
        payload = {
            "Age": age,
            "Gender": gender,
            "Tenure": tenure,
            "Usage Frequency": usage,
            "Support Calls": calls,
            "Payment Delay": delay,
            "Subscription Type": sub_type,
            "Contract Length": contract,
            "Total Spend": spend,
            "Last Interaction": last_inter
        }
        
        headers = {"Authorization": f"Bearer {st.session_state['token']}"}
        
        try:
            res = requests.post(f"{BASE_URL}/predict", json=payload, headers=headers)
            if res.status_code == 200:
                result = res.json()
                
                # Display Results
                st.markdown("### 📊 Analysis Result:")
                if result['prediction'] == 'Churn':
                    st.error(f"🔥 **Prediction:** {result['prediction']}")
                    st.error(f"⚠️ **Risk Level:** {result['risk_level']}")
                    st.toast("Customer is leaving! Panic!", icon="😱")
                else:
                    st.success(f"✅ **Prediction:** {result['prediction']}")
                    st.success(f"🛡️ **Risk Level:** {result['risk_level']}")
                    st.balloons()
            else:
                st.error(f"Error {res.status_code}: {res.text}")
        except Exception as e:
            st.error(f"Prediction failed: {e}")
