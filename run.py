import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import io

st.set_page_config(layout="wide", page_icon="🏗️")

# LOGIN (mantido)
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = ""

if not st.session_state.logged_in:
    st.markdown("# 🔐 LicitaContract PMRO v2.0")
    col1, col2 = st.columns(2)
    user = col1.text_input("👤 Usuário")
    senha = col2.text_input("🔑 Senha", type="password")
    if st.button("🚀 Acessar"):
        if (user == "guilherme" and senha == "engenharia123") or \
           (user == "engenheiro" and senha == "pmro2026"):
            st.session_state.logged_in = True
            st.session_state.user = user.title()
            st.rerun()
        else:
            st.error("❌ Credenciais inválidas")
    st.stop()

st.sidebar.success(f"👨‍💼 {st.session_state.user}")
if st.sidebar.button("Sair"): st.session_state.logged_in = False; st.rerun()

DB_PATH = "licitacontract.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS contratos (
        id INTEGER PRIMARY KEY,
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

@st.cache_data(ttl=60)
def get_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM contratos ORDER BY data DESC", conn)
    conn.close()
    return df.fillna('')

st.title("🏗️ LicitaContract PMRO **v2.0**")
st.caption("Prefeitura Porto Velho | Licitações Inteligentes")

# FILTROS TOP!
col1, col2, col3 = st.columns(3)
status_filtro = col1.multiselect("Status", get_data()['status'].unique())
data_inicio = col2.date_input("Desde")
data_fim = col3.date_input("Até", value=date.today())

df_filtrado = get_data()
if status_filtro: 
    df_filtrado = df_filtrado[df_filtrado['status'].isin(status_filtro)]
df_filtrado['data'] = pd.to_datetime(df_filtrado['data'])
df_filtrado = df_filtrado[(df_filtrado['data'] >= pd.to_datetime(data_inicio)) & 
                         (df_filtrado['data'] <= pd.to_datetime(data_fim))]

tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "➕ Cadastrar", "📈 Analytics", "📥 Export"])

with tab1:
    col1, col2, col3 = st.columns(3)
    col1.metric("Obras", len(df_filtrado))
    col2.metric("Valor", f"R$ {df_filtrado.valor.sum():,.0f}")
    col3.metric("Média", f"R$ {df_filtrado.valor.mean():,.0f}")
    st.dataframe(df_filtrado, use_container_width=True)

with tab2:
    with st.form("form"):
        col1, col2 = st.columns(2)
        numero = col1.text_input("Número")
        valor = col2.number_input("Valor R$", value=0.0)
        status = st.selectbox("Status", ["Em execução", "Concluído", "Paralisado"])
        obs = st.text_area("Observações")
        if st.form_submit_button("✅ Salvar"):
            conn = sqlite3.connect(DB_PATH)
            try:
                conn.execute("INSERT INTO contratos VALUES (NULL, ?, ?, ?, ?, ?, ?)",
                           (numero, valor, status, datetime.now().strftime("%Y-%m-%d"), obs, st.session_state.user))
                conn.commit()
                st.success("✅ Salvo!")
                st.rerun()
            except:
                st.error("❌ Número existe!")
            conn.close()

with tab3:
    col1, col2 = st.columns(2)
    fig1 = px.pie(df_filtrado, names='status', title="Distribuição Status")
    col1.plotly_chart(fig1)
    fig2 = px.bar(df_filtrado, x='numero', y='valor', title="Valores")
    col2.plotly_chart(fig2)

with tab4:
    csv = df_filtrado.to_csv(index=False).encode('utf-8')
    st.download_button("📥 CSV Filtrado", csv, f"pmro_{datetime.now().strftime('%Y%m%d')}.csv", use_container_width=True)

st.markdown("---")
