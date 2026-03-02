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
    st.title("🔐 LicitaContract PMRO")
    col1, col2 = st.columns(2)
    username = col1.text_input("👤")
    password = col2.text_input("🔑", type="password")
    if st.button("Entrar"):
        if (username == "guilherme" and password == "engenharia123") or \
           (username == "engenheiro" and password == "pmro2026"):
            st.session_state.user = username.title()
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

st.sidebar.success(st.session_state.user)
if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.session_state.logged_in = False
    st.rerun()

DB = "pmro.db"
conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS contratos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT UNIQUE, valor REAL, status TEXT, data TEXT,
    objeto TEXT, reajuste TEXT, pdf TEXT, usuario TEXT
)''')
conn.commit()

@st.cache_data
def df_data():
    return pd.read_sql("SELECT * FROM contratos ORDER BY id DESC", conn)

def extrair_pdf(pdf_file):
    try:
        with pdfplumber.open(pdf_file) as pdf:
            texto = ""
            for p in pdf.pages:
                txt = p.extract_text()
                if txt: texto += txt
        
        # REGEX CORRIGIDOS PMRO
        contrato = re.search(r'(?:CONTRATO|PROCESSO)[^0-9]*?(\d+/\d+(?:/\d+)?)', texto, re.I)
        valor = re.search(r'VALOR[^R$]*R\$\s*([\d. ]+,?\d{2})', texto, re.I)
        objeto = re.search(r'OBJETO[:\s]*([^\n.]{30,400})', texto, re.I)
        reajuste = re.search(r'(?:REAJUSTE|SINAPI|INPC)[^.\n]*?([a-zA-Z]+/\d{4})', texto, re.I)
        
        dados = {
            'contrato': contrato.group(1) if contrato else "❌",
            'valor': valor.group(1) if valor else "❌",
            'objeto': objeto.group(1).strip()[:250] if objeto else "❌",
            'reajuste': reajuste.group(1) if reajuste else "❌"
        }
        return dados
    except:
        return {"erro": "PDF"}

def float_seguro(valor_txt):
    if valor_txt == "❌": return 0.0
    try:
        limpo = re.sub(r'[^\d,.]', '', valor_txt)
        return float(limpo.replace('.', '').replace(',', '.'))
    except:
        return 0.0

st.title("🏗️ PMRO LicitaContract v3.6")

tab1, tab2 = st.tabs(["📊 Dashboard", "📄 IA PDF"])

with tab1:
    df = df_data()
    c1, c2 = st.columns(2)
    c1.metric("Contratos", len(df))
    c2.metric("R$", f"{df.valor.sum():,.0f}")
    st.dataframe(df)

with tab2:
    pdf = st.file_uploader("PDF", type="pdf")
    if pdf:
        dados = extrair_pdf(pdf)
        st.success("✅ Extraiu!")
        st.json(dados)
        
        with st.form("form"):
            numero = st.text_input("Número", dados['contrato'])
            valor_txt = st.text_input("Valor", dados['valor'])
            valor = float_seguro(valor_txt)
            objeto = st.text_area("Objeto", dados['objeto'])
            status = st.selectbox("Status", ["Em execução"])
            
            if st.form_submit_button("💾 Salvar"):
                try:
                    c.execute("INSERT INTO contratos VALUES(NULL,?,?,?,?,?,?,?,?)",
                            (numero, valor, status, datetime.now().strftime("%Y-%m-%d"),
                             objeto, dados['reajuste'], pdf.name, st.session_state.user))
                    conn.commit()
                    st.success("✅ Salvo!")
                    st.rerun()
                except:
                    st.error("❌ Duplicado")

if st.button("📥 CSV"):
    st.download_button("Baixar", df_data().to_csv(index=False).encode(), "pmro.csv")
