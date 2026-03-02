import streamlit as st
import sqlite3
import pandas as pd
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
if st.sidebar.button("Logout"): st.session_state.logged_in = False; st.rerun()

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

def extrair_pmro(pdf_file):
    try:
        with pdfplumber.open(pdf_file) as pdf:
            texto = ""
            for p in pdf.pages:
                txt = p.extract_text()
                if txt: texto += txt
        
        # 🔍 REGEX EXATOS PMRO (seus exemplos)
        numero_match = re.search(r'\((\d{3}/PGM/\d{4})\)', texto) or \
                      re.search(r'CONTRATO.*?(\d+/\d+)', texto, re.I) or \
                      re.search(r'PROCESSO.*?(\d+/\d+)', texto, re.I)
        
        valor_match = re.search(r'VALOR.*?R\$\s*([\d. ]+,?\d{2})', texto, re.I) or \
                     re.search(r'contratação.*?R\$\s*([\d. ]+,?\d{2})', texto, re.I) or \
                     re.search(r'total.*?R\$\s*([\d. ]+,?\d{2})', texto, re.I)
        
        objeto_match = re.search(r'OBJETO[:\s]*([^\n.]{30,400})', texto, re.I)
        reajuste_match = re.search(r'(?:REAJUSTE|SINAPI).*?([A-Z]+/\d{4})', texto, re.I)
        
        dados = {
            'numero': numero_match.group(1) if numero_match else "❌",
            'valor': valor_match.group(1) if valor_match else "❌",
            'objeto': objeto_match.group(1).strip()[:250] if objeto_match else "❌",
            'reajuste': reajuste_match.group(1) if reajuste_match else "❌"
        }
        return dados
    except:
        return {"erro": "PDF"}

def valor_real(valor_txt):
    if valor_txt == "❌": return 0.0
    try:
        # Remove tudo menos números, pontos, vírgulas
        limpo = re.sub(r'[^\d,.]', '', valor_txt)
        # BR: milhar=ponto, decimal=vírgula → float
        return float(limpo.replace('.', '').replace(',', '.'))
    except:
        return 0.0

st.title("🏗️ PMRO LicitaContract **v3.7 PMRO**")

tab1, tab2 = st.tabs(["📊 Dashboard", "📄 IA PMRO"])

with tab1:
    df = df_data()
    c1, c2 = st.columns(2)
    c1.metric("Contratos", len(df))
    c2.metric("R$", f"{df.valor.sum():,.0f}")
    st.dataframe(df[['numero','valor','objeto']])

with tab2:
    st.header("🤖 IA PMRO - Seus Exemplos")
    pdf = st.file_uploader("📄 PDF", type="pdf")
    
    if pdf:
        dados = extrair_pmro(pdf)
        st.success("✅ IA PMRO!")
        st.json(dados)
        
        with st.form("form"):
            numero = st.text_input("Número Contrato", dados['numero'])
            valor_txt = st.text_input("Valor Encontrado", dados['valor'])
            valor = valor_real(valor_txt)
            st.number_input("Valor Numérico", value=valor, disabled=True)
            objeto = st.text_area("Objeto", dados['objeto'])
            status = st.selectbox("Status", ["Em execução"])
            
            col1, col2 = st.columns(2)
            if col1.form_submit_button("💾 Salvar"):
                try:
                    c.execute("INSERT INTO contratos VALUES(NULL,?,?,?,?,?,?,?,?)",
                            (numero, valor, status, datetime.now().strftime("%d/%m/%Y"),
                             objeto, dados['reajuste'], pdf.name, st.session_state.user))
                    conn.commit()
                    st.balloons()
                    st.success(f"✅ {numero} salvo!")
                    st.rerun()
                except:
                    st.error("❌ Já existe")
            
            if col2.form_submit_button("🔄 Outro PDF"): st.rerun()

st.download_button("📥 CSV PMRO", df_data().to_csv(index=False).encode(), "pmro.csv")
