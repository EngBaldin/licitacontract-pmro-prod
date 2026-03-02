import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import pdfplumber
import re
from datetime import datetime

st.set_page_config(layout="wide", page_icon="🏗️")

if 'user' not in st.session_state:
    st.session_state.user = None
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 LicitaContract PMRO v3.4")
    col1, col2 = st.columns(2)
    username = col1.text_input("👤 Usuário")
    password = col2.text_input("🔑 Senha", type="password")
    if st.button("🚀 Entrar"):
        if (username == "guilherme" and password == "engenharia123") or \
           (username == "engenheiro" and password == "pmro2026"):
            st.session_state.user = username.title()
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("❌")
    st.stop()

st.sidebar.success(f"👋 {st.session_state.user}")
if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.session_state.logged_in = False
    st.rerun()

# DB
DB = "pmro.db"
conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS contratos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT UNIQUE, valor REAL, status TEXT, data TEXT,
    objeto TEXT, reajuste TEXT, pdf TEXT, usuario TEXT
)''')
conn.commit()

@st.cache_data(ttl=60)
def get_df():
    return pd.read_sql("SELECT * FROM contratos ORDER BY id DESC", conn)

def parse_pdf(pdf_file):
    try:
        with pdfplumber.open(pdf_file) as pdf:
            texto = ""
            for p in pdf.pages:
                texto += p.extract_text() or ""
        
        dados = {}
        dados['contrato'] = re.search(r'CONTRATO.*?(\d+/\d+)', texto, re.I | re.DOTALL)
        dados['valor'] = re.search(r'R\$\s*([\d.,]+)', texto)
        dados['objeto'] = re.search(r'OBJETO[:\s](.{50,300})', texto, re.I | re.DOTALL)
        dados['reajuste'] = re.search(r'(SINAPI|reajuste).*?(\w+/\d{4})', texto, re.I | re.DOTALL)
        
        return {k: (m.group(1).strip() if m else "❌") for k, m in dados.items()}
    except:
        return {"erro": "Falha PDF"}

st.title("🏗️ PMRO LicitaContract **v3.4 PRO**")

tab1, tab2 = st.tabs(["📊 Dashboard", "📄 PDF IA"])

with tab1:
    df = get_df()
    col1, col2 = st.columns(2)
    col1.metric("Contratos", len(df))
    col2.metric("Total R$", f"{df.valor.sum():,.0f}")
    st.dataframe(df[['numero','valor','objeto','status']])

with tab2:
    pdf = st.file_uploader("📄 PDF Contrato", type="pdf")
    if pdf:
        dados = parse_pdf(pdf)
        st.success("✅ IA extraiu!")
        st.json(dados)
        
        # FORM COM BOTÃO
        with st.form("form"):
            numero = st.text_input("Contrato Nº", value=dados.get('contrato', ''))
            valor_txt = st.text_input("Valor", value=dados.get('valor', ''))
            
            # VALOR SEGURO
            try:
                valor = float(valor_txt.replace('R$','').replace('.','').replace(',','.'))
            except:
                valor = 0.0
            
            objeto = st.text_area("Objeto", value=dados.get('objeto', ''), height=80)
            status = st.selectbox("Status", ["Em execução", "Concluído"])
            
            col1, col2 = st.columns(2)
            if col1.form_submit_button("💾 Salvar"):
                try:
                    c.execute("INSERT INTO contratos VALUES(NULL,?,?,?,?,?,?,?,?)",
                            (numero, valor, status, datetime.now().strftime("%Y-%m-%d"),
                             objeto[:500], dados.get('reajuste', '❌'), pdf.name, st.session_state.user))
                    conn.commit()
                    st.balloons()
                    st.success(f"✅ {numero} salvo!")
                    st.rerun()
                except:
                    st.error("❌ Já existe")
            if col2.form_submit_button("🔄 Novo"):
                st.rerun()

# DOWNLOAD
st.download_button("📥 CSV", get_df().to_csv(index=False).encode(), "pmro.csv")
