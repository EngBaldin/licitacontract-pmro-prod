import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import pdfplumber
import re
import io
from datetime import datetime, date

st.set_page_config(layout="wide", page_icon="🏗️")

# LOGIN
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.markdown("# 🔐 LicitaContract PMRO v3.1")
    col1, col2 = st.columns(2)
    u = col1.text_input("👤"); s = col2.text_input("🔑", type="password")
    if st.button("🚀"): 
        if (u == "guilherme" and s == "engenharia123") or (u == "engenheiro" and s == "pmro2026"):
            st.session_state.logged_in = True; st.session_state.user = u.title(); st.rerun()
        st.stop()

st.sidebar.success(st.session_state.user)
if st.sidebar.button("Sair"): st.session_state.logged_in = False; st.rerun()

DB_PATH = "licitacontract.db"
def init_db(): 
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS contratos (
        id INTEGER PRIMARY KEY, numero TEXT UNIQUE, valor REAL, status TEXT, 
        data TEXT, objeto TEXT, reajuste TEXT, pdf_nome TEXT, usuario TEXT
    )''')
    conn.commit()
    conn.close()
init_db()

@st.cache_data
def get_data(): 
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM contratos ORDER BY data DESC", conn)
    conn.close()
    return df.fillna('')

def extrair_pdf(pdf_file):
    """PDF IA PMRO - pdfplumber"""
    dados = {'objeto': 'NÃO ENCONTRADO', 'contrato': 'NÃO ENCONTRADO', 
             'assinatura': 'NÃO ENCONTRADO', 'reajuste': 'NÃO ENCONTRADO', 'valor': 'NÃO ENCONTRADO'}
    
    try:
        with pdfplumber.open(pdf_file) as pdf:
            texto = ""
            for page in pdf.pages: texto += page.extract_text() or ""
        
        # REGEX CONTRATOS BRASILEIROS
        padroes = {
            'contrato': r'CONTRATO\s*[Nº°]?\s*:?\s*(\d+/\d+(?:/\d+)?)',
            'objeto': r'OBJETO[:\s]*([A-Z][^.\n]{20,300})',
            'valor': r'(?:VALOR\s*TOTAL|TOTAL\s*DO\s*CONTRATO)[:\s]*R\$\s*([\d.,]+)',
            'assinatura': r'\d{1,2}[/\-\.]?\d{1,2}[/\-\.]?\d{2,4}',
            'reajuste': r'(?:REAJUSTE|SINAPI)[^.\n]*?(\w+/\d{4}|proposta|orçamento)'
        }
        
        for chave, padrao in padroes.items():
            match = re.search(padrao, texto, re.IGNORECASE | re.MULTILINE)
            if match: dados[chave] = match.group(1).strip()
    
    except: pass
    
    return dados

st.title("🏗️ LicitaContract PMRO **v3.1 PDF IA**")

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📄 PDF IA", "📈 Gráficos"])

with tab1:
    df = get_data()
    col1, col2, col3 = st.columns(3)
    col1.metric("Contratos", len(df))
    col2.metric("Valor Total", f"R$ {df.valor.sum():,.0f}")
    col3.metric("IA Extraídos", len(df[df.objeto!='']))
    st.dataframe(df[['numero','valor','objeto','reajuste','status']], use_container_width=True)

with tab2:
    st.header("🤖 UPLOAD CONTRATO - EXTRAÇÃO AUTOMÁTICA")
    pdf_file = st.file_uploader("📄 PDF Contrato", type="pdf")
    
    if pdf_file:
        col1, col2 = st.columns([1,2])
        col1.success(f"✅ {pdf_file.name}")
        
        with st.spinner("🔍 IA analisando..."):
            dados_ia = extrair_pdf(pdf_file)
        
        col1.json(dados_ia)
        st.info("📝 Dados extraídos com IA - revise e salve!")
        
        # FORM PREENCHIDO IA
        with st.form("ia_form"):
            st.subheader("💾 Salvar Dados IA")
            numero = st.text_input("Contrato Nº", value=dados_ia['contrato'])
            valor_txt = st.text_input("Valor", value=dados_ia['valor'])
            valor = float(valor_txt.replace('.','').replace(',','.').replace('R$','')) if valor_txt!='NÃO ENCONTRADO' else 0
            objeto = st.text_area("Objeto", value=dados_ia['objeto'], height=80)
            reajuste = st.text_input("Reajuste", value=dados_ia['reajuste'])
            status = st.selectbox("Status", ["Em execução", "Concluído", "Paralisado"])
            
            col_btn, _ = st.columns(2)
            if col_btn.form_submit_button("✅ Salvar IA", use_container_width=True):
                conn = sqlite3.connect(DB_PATH)
                try:
                    conn.execute("""INSERT INTO contratos VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?)""",
                               (numero, valor, status, datetime.now().strftime("%Y-%m-%d"), 
                                objeto, reajuste, pdf_file.name, st.session_state.user))
                    conn.commit()
                    st.balloons()
                    st.success("🎉 Contrato IA SALVO!")
                    st.rerun()
                except: st.error("❌ Número duplicado")
                conn.close()

with tab3:
    df = get_data()
    col1, col2 = st.columns(2)
    fig1 = px.pie(df, names='status', title="Status")
    col1.plotly_chart(fig1, use_container_width=True)
    fig2 = px.bar(df, x='numero', y='valor', title="Valores")
    col2.plotly_chart(fig2, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.download_button("📥 Export CSV", get_data().to_csv(index=False).encode(), "pmro_v3.csv")
