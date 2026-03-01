import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

st.set_page_config(layout="wide", page_icon="🏗️")

# LOGIN SESSION
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = ""

if not st.session_state.logged_in:
    st.markdown("# 🔐 LicitaContract PMRO")
    st.markdown("### Acesso Restrito Equipe Engenharia")
    
    col1, col2 = st.columns(2)
    user = col1.text_input("👤 Usuário")
    senha = col2.text_input("🔑 Senha", type="password")
    
    if st.button("🚀 Acessar Sistema", use_container_width=True):
        if (user == "guilherme" and senha == "engenharia123") or \
           (user == "engenheiro" and senha == "pmro2026"):
            st.session_state.logged_in = True
            st.session_state.user = user.title()
            st.rerun()
        else:
            st.error("❌ Credenciais inválidas")
    st.stop()

st.sidebar.success(f"Logado: {st.session_state.user}")
if st.sidebar.button("Sair"):
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
        usuario TEXT DEFAULT 'equipe'
    )''')
    conn.commit()
    conn.close()

init_db()

@st.cache_data(ttl=30)
def get_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM contratos ORDER BY data DESC", conn)
    conn.close()
    return df.fillna('')

st.title("🏗️ LicitaContract PMRO")
st.caption(f"Usuário: {st.session_state.user}")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "➕ Cadastrar", "📈 Gráficos", "📥 Export"])

with tab1:
    st.header("📊 Dashboard PMRO")
    df = get_data()
    if len(df) > 0:
        col1, col2 = st.columns(2)
        col1.metric("Obras", len(df))
        col2.metric("Valor Total", f"R$ {df.valor.sum():,.0f}")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Cadastre obras!")

with tab2:
    st.header("➕ Cadastrar Obra")
    with st.form("form"):
        col1, col2 = st.columns(2)
        numero = col1.text_input("Número Contrato")
        valor = col2.number_input("Valor R$", value=0.0)
        status = st.selectbox("Status", ["Em execução", "Concluído", "Paralisado"])
        obs = st.text_area("Observações")
        
        if st.form_submit_button("Salvar"):
            conn = sqlite3.connect(DB_PATH)
            try:
                conn.execute("""
                    INSERT INTO contratos (numero, valor, status, data, observacoes, usuario)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (numero, valor, status, datetime.now().strftime("%Y-%m-%d"), obs, st.session_state.user))
                conn.commit()
                st.success("✅ Cadastrada!")
                st.rerun()
            except:
                st.error("❌ Número existe!")
            conn.close()

with tab3:
    st.header("📈 Analytics")
    df = get_data()
    if len(df) > 0:
        col1, col2 = st.columns(2)
        fig1 = px.pie(df, names='status')
        col1.plotly_chart(fig1)
        fig2 = px.bar(df, x='numero', y='valor')
        col2.plotly_chart(fig2)

with tab4:
    st.header("📥 Export")
    df = get_data()
    if len(df) > 0:
        st.dataframe(df)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 CSV PMRO", csv, f"pmro_{datetime.now().strftime('%Y%m%d')}.csv", use_container_width=True)
    else:
        st.info("Sem dados")

st.markdown("---")
st.caption("Prefeitura Porto Velho | Licitações Seguras")
