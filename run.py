import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import pdfplumber
import re
from datetime import datetime

st.set_page_config(layout="wide", page_icon="🏗️")

# SESSION STATE
if 'user' not in st.session_state:
    st.session_state.user = None
    st.session_state.logged_in = False

# LOGIN
if not st.session_state.logged_in:
    st.title("🔐 LicitaContract PMRO v3.3")
    
    col1, col2 = st.columns(2)
    username = col1.text_input("Usuário")
    password = col2.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        if (username == "guilherme" and password == "engenharia123") or \
           (username == "engenheiro" and password == "pmro2026"):
            st.session_state.user = username
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("❌ Inválido")
    st.stop()

# INTERFACE
st.sidebar.markdown(f"**👋 {st.session_state.user}**")
if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.session_state.logged_in = False
    st.rerun()

DB = "pmro.db"
conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS contratos (
    id INTEGER PRIMARY KEY AUTOINCREMENT, numero TEXT UNIQUE, valor REAL,
    status TEXT, data TEXT, objeto TEXT, reajuste TEXT, pdf TEXT, usuario TEXT
)''')
conn.commit()

@st.cache_data(ttl=60)
def df_contratos():
    return pd.read_sql("SELECT * FROM contratos ORDER BY id DESC", conn)

def ler_pdf(pdf_file):
    try:
        with pdfplumber.open(pdf_file) as pdf:
            texto = ""
            for p in pdf.pages:
                texto += p.extract_text() or ""
        
        dados = {}
        dados['contrato'] = re.search(r'CONTRATO.*?(\d+/\d+)', texto, re.I)
        dados['valor'] = re.search(r'VALOR.*?R\$\s*([\d.,]+)', texto, re.I)
        dados['objeto'] = re.search(r'OBJETO[:\s](.*?)(?=\n[A-Z]{3,})', texto, re.I | re.DOTALL)
        dados['reajuste'] = re.search(r'(SINAPI|reajuste).*?(\w+/\d{4})', texto, re.I)
        
        return {k: m.group(1).strip() if m else "❌" for k, m in dados.items()}
    except:
        return {"erro": "PDF inválido"}

st.title("🏗️ PMRO LicitaContract v3.3")

tab1, tab2 = st.tabs(["📊 Contratos", "📄 PDF IA"])

with tab1:
    df = df_contratos()
    col1, col2 = st.columns(2)
    col1.metric("Contratos", len(df))
    col2.metric("Valor", f"R$ {df.valor.sum():,.0f}")
    st.dataframe(df)

with tab2:
    st.header("🤖 Upload PDF")
    pdf = st.file_uploader("PDF", "pdf")
    
    if pdf:
        dados = ler_pdf(pdf)
        st.json(dados)
        
        with st.form("salvar"):
            numero = st.text_input("Número", dados.get('contrato', ''))
            valor_txt = st.text_input("Valor", dados.get('valor', ''))
            valor = float(valor_txt.replace(',', '.').replace('R$', '')) if valor_txt != '❌' else 0
            objeto = st.text_area("Objeto", dados.get('objeto', ''))
            status = st.selectbox("Status", ["Em execução"])
            
            if st.form_submit_button("Salvar"):
                try:
                    c.execute("INSERT INTO contratos VALUES (NULL,?,?,?,?,?,?,?,?)", 
                            (numero, valor, status, datetime.now().strftime("%Y-%m-%d"),
                             objeto, dados.get('reajuste', ''), pdf.name, st.session_state.user))
                    conn.commit()
                    st.success("✅ Salvo!")
                    st.rerun()
                except:
                    st.error("❌ Duplicado")

st.download_button("CSV", df_contratos().to_csv(index=False).encode(), "pmro.csv")
