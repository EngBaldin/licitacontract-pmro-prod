import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

st.set_page_config(layout="wide", page_icon="🏗️")

# LOGIN SIMPLES PMRO
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = ""

if not st.session_state.logged_in:
    st.title("🔐 LicitaContract PMRO")
    col1, col2 = st.columns([1,2])
    with col1:
        user = st.text_input("Usuário PMRO")
        senha = st.text_input("Senha", type="password")
    with col2:
        st.info("👨‍💼 **guilherme** / **engenharia123**\n👷 **engenheiro** / **pmro2026**")
    
    if st.button("Entrar"):
        if user == "guilherme" and senha == "engenharia123":
            st.session_state.logged_in = True
            st.session_state.user = "Guilherme Baldin"
            st.rerun()
        elif user == "engenheiro" and senha == "pmro2026":
            st.session_state.logged_in = True
            st.session_state.user = "Engenheiro PMRO"
            st.rerun()
        else:
            st.error("❌ Credenciais inválidas")
    st.stop()

# USUÁRIO LOGADO
st.sidebar.success(f"👋 {st.session_state.user}")
if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.session_state.user = ""
    st.rerun()

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
        usuario TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

@st.cache_data(ttl=30)
def get_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM contratos ORDER BY data DESC", conn)
    conn.close()
    return df

st.title(f"🏗️ LicitaContract PMRO - {st.session_state.user}")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "➕ Cadastrar", "📈 Gráficos", "📥 Export"])

with tab1:
    df = get_data()
    if len(df) > 0:
        col1.metric("Obras", len(df))
        col2.metric("Valor", f"R$ {df.valor.sum():,.0f}")
        st.dataframe(df)
    else:
        st.info("Cadastre obras!")

with tab2:
    with st.form("form"):
        numero = st.text_input("Número")
        valor = st.number_input("Valor")
        status = st.selectbox("Status", ["Em execução", "Concluído"])
        obs = st.text_area("Obs")
        if st.form_submit_button("Salvar"):
            conn = sqlite3.connect(DB_PATH)
            conn.execute("INSERT INTO contratos VALUES (NULL, ?, ?, ?, ?, ?, ?)",
                        (numero, valor, status, datetime.now().strftime("%Y-%m-%d"), obs, st.session_state.user))
            conn.commit()
            conn.close()
            st.success("✅ Salva!")
            st.rerun()

with tab3:
    df = get_data()
    if len(df) > 0:
        fig = px.bar(df, x='numero', y='valor')
        st.plotly_chart(fig)

with tab4:
    df = get_data()
    st.download_button("Excel", df.to_csv(index=False), "pmro.csv")

st.sidebar.caption("guilherme/engenharia123 | engenheiro/pmro2026")
