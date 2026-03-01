import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
import io
import streamlit_authenticator as stauth

# CONFIG SEGURANÇA (substitua por secrets.toml depois)
credentials = {
    "usernames": {
        "guilherme": {
            "name": "Guilherme Baldin",
            "password": "engenharia123"
        },
        "engenheiro": {
            "name": "Engenheiro PMRO", 
            "password": "pmro2026"
        }
    }
}
cookie = {"key": "licitacontract", "expiry_days": 7}

authenticator = stauth.Authenticate(
    credentials,
    cookie["key"],
    cookie["name"],
    cookie["expiry_days"]
)

name, authentication_status, username = authenticator.login("Login PMRO", "left")

if authentication_status == False:
    st.error("Senha incorreta")
elif authentication_status == None:
    st.warning("Por favor digite usuário/senha")
    st.stop()
else:
    # SIDEBAR USER
    st.sidebar.success(f"👋 {name}")
    if st.sidebar.button("Logout"):
        authenticator.logout()
        st.rerun()

st.set_page_config(layout="wide", page_icon="🏗️")

DB_PATH = "licitacontract.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS contratos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT UNIQUE,
        valor REAL,
        status TEXT,
        data TEXT,
        observacoes TEXT,
        usuario TEXT DEFAULT ?
    )''', (name,))
    conn.commit()
    conn.close()

init_db()

@st.cache_data(ttl=30)
def get_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM contratos ORDER BY data DESC", conn)
    conn.close()
    return df

st.title("🏗️ LicitaContract PMRO 🔐")
st.caption(f"Usuário: {name}")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "➕ Cadastrar", "📈 Gráficos", "📥 Export"])

with tab1:
    st.header("📊 Dashboard")
    df = get_data()
    if len(df) > 0:
        col1.metric("Obras", len(df))
        col2.metric("Valor", f"R$ {df.valor.sum():,.0f}")
        st.dataframe(df)

with tab2:
    st.header("➕ Nova Obra")
    with st.form("form"):
        numero = st.text_input("Número")
        valor = st.number_input("Valor")
        status = st.selectbox("Status", ["Em execução", "Concluído"])
        obs = st.text_area("Obs")
        if st.form_submit_button("Salvar"):
            conn = sqlite3.connect(DB_PATH)
            conn.execute("INSERT INTO contratos (numero, valor, status, data, observacoes, usuario) VALUES (?, ?, ?, ?, ?, ?)",
                        (numero, valor, status, datetime.now().strftime("%Y-%m-%d"), obs, name))
            conn.commit()
            conn.close()
            st.success("✅ Salva!")
            st.rerun()

# ... outras tabs iguais ...

st.sidebar.title("👥 Usuários")
st.sidebar.info("guilherme / engenharia123\nengenheiro / pmro2026")
