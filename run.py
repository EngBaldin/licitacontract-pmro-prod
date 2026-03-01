import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
import io
import os

st.set_page_config(page_title="LicitaContract", page_icon="🏗️", layout="wide", initial_sidebar_state="expanded")
st.cache_data.clear()  # Limpa cache sempre

st.title("🏗️ LicitaContract PMRO")
st.caption("Gestão Completa Licitações - Eng. Guilherme Baldin")

DB_PATH = "licitacontract.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS contratos (
            numero TEXT PRIMARY KEY,
            valor REAL,
            status TEXT,
            data TEXT,
            observacoes TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_contratos():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM contratos ORDER BY data DESC", conn)
    conn.close()
    return df

# Sidebar
st.sidebar.title("📂 Menu")
page = st.sidebar.selectbox(":", ["📊 Dashboard", "➕ Cadastrar", "📄 Relatórios", "📈 Gráficos"])
if st.sidebar.button("🔄 Atualizar"):
    st.cache_data.clear()
    st.rerun()

if page == "📊 Dashboard":
    st.header("📊 Dashboard")
    df = get_contratos()
    st.write(f"**Total registros: {len(df)}**")
    
    if len(df) > 0:
        col1, col2, col3 = st.columns(3)
        col1.metric("Contratos", len(df))
        col2.metric("Valor", f"R$ {df.valor.sum():,.0f}")
        col3.metric("Em Execução", len(df[df.status=='Em execução']))
        
        fig = px.pie(df, names='status', title="Status")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Cadastre obras!")

elif page == "➕ Cadastrar":
    st.header("➕ Cadastrar Obra")
    with st.form("form"):
        col1, col2 = st.columns(2)
        numero = col1.text_input("Número")
        valor = col2.number_input("Valor R$", value=0.0)
        status = st.selectbox("Status", ["Em execução", "Concluído"])
        obs = st.text_area("Obs")
        
        if st.form_submit_button("Salvar"):
            conn = sqlite3.connect(DB_PATH)
            try:
                conn.execute("INSERT INTO contratos VALUES (?, ?, ?, ?, ?)",
                           (numero, valor, status, datetime.now().strftime("%Y-%m-%d"), obs))
                conn.commit()
                st.success("✅ Salvo!")
                st.rerun()
            except:
                st.error("❌ Já existe!")
            conn.close()

elif page == "📄 Relatórios":
    st.header("📄 Relatórios")
    df = get_contratos()
    if len(df) > 0:
        st.dataframe(df)
        output = io.BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        st.download_button("Excel", output.getvalue(), "relatorio.xlsx")
    else:
        st.info("Sem dados")

elif page == "📈 Gráficos":
    st.header("📈 Gráficos")
    df = get_contratos()
    if len(df) > 0:
        fig_bar = px.bar(df, x='numero', y='valor')
        st.plotly_chart(fig_bar)
    else:
        st.info("Sem dados")

st.sidebar.markdown("---")
st.sidebar.caption("PMRO 2026")
