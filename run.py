import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

st.set_page_config(layout="wide", page_icon="🏗️")

# SESSION LOGIN
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = ""

if not st.session_state.logged_in:
    st.markdown("""
    # 🔐 LicitaContract PMRO
    ## Acesso Restrito Equipe
    """)
    
    col1, col2 = st.columns(2)
    user = col1.text_input("👤 Usuário PMRO")
    senha = col2.text_input("🔑 Senha", type="password")
    
    if st.button("🚀 Entrar", use_container_width=True):
        if (user == "guilherme" and senha == "engenharia123") or \
           (user == "engenheiro" and senha == "pmro2026"):
            st.session_state.logged_in = True
            st.session_state.user = user.title()
            st.rerun()
        else:
            st.error("❌ Credenciais inválidas")
    st.stop()

# LOGADO - SIDEBAR
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

st.title(f"🏗️ LicitaContract PMRO")
st.caption(f"👨‍💼 Logado: {st.session_state.user}")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "➕ Cadastrar", "📈 Gráficos", "📥 Export"])

with tab1:
    st.header("📊 Dashboard")
    df = get_data()
    if len(df) > 0:
        col1, col2 = st.columns(2)
        col1.metric("Total Obras", len(df))
        col2.metric("Valor Total", f"R$ {df.valor.sum():,.0f}")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("👆 Cadastre primeira obra!")

with tab2:
    st.header("➕ Nova Obra")
    with st.form("form"):
        col1, col2 = st.columns(2)
        numero = col1.text_input("Número Contrato")
        valor = col2.number_input("Valor R$", value=0.0)
        status = st.selectbox("Status", ["Em execução", "Concluído", "Paralisado"])
        obs = st.text_area("Observações")
        
        if st.form_submit_button("✅ Salvar", use_container_width=True):
            conn = sqlite3.connect(DB_PATH)
            try:
                conn.execute("""
                    INSERT INTO contratos (numero, valor, status, data, observacoes, usuario)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (numero, valor, status, datetime.now().strftime("%Y-%m-%d"), obs, st.session_state.user))
                conn.commit()
                st.success("✅ Obra cadastrada!")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("❌ Número contrato já existe!")
            except Exception as e:
                st.error(f"Erro: {e}")
            conn.close()

with tab3:
    st.header("📈 Gráficos")
    df = get_data()
    if len(df) > 0:
        col1, col2 = st.columns(2)
        fig1 = px.pie(df, names='status', title="Status Obras")
        col1.plotly_chart(fig1, use_container_width=True)
        fig2 = px.bar(df, x='numero', y='valor', title="Valores")
        col2.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Sem dados")

with tab4:
    st.header("📥 Relatórios")
    df = get_data()
    if len(df) > 0:
        st.dataframe(df)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Obras', index=False)
            resumo = df.groupby(['status', 'usuario'])['valor'].sum().reset_index()
            resumo.to_excel(writer, sheet_name='Resumo', index=False)
        st.download_button("📥 Excel Oficial PMRO", output.getvalue(),
                          f"PMRO_{datetime.now().strftime('%Y%m%d')}.xlsx", use_container_width=True)
    else:
        st.info("Sem dados para exportar")

st.markdown("---")
st.caption("🔒 Acesso restrito PMRO | Equipe Engenharia")
