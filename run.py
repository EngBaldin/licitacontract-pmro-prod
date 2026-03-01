import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import fitz  # PyMuPDF
import re
import io
from datetime import datetime, date

st.set_page_config(layout="wide", page_icon="🏗️")

# LOGIN (igual)
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.markdown("# 🔐 LicitaContract PMRO v3.0 - PDF IA")
    col1, col2 = st.columns(2)
    u = col1.text_input("👤"); s = col2.text_input("🔑", type="password")
    if st.button("🚀"): 
        if (u == "guilherme" and s == "engenharia123") or (u == "engenheiro" and s == "pmro2026"):
            st.session_state.logged_in = True; st.session_state.user = u.title(); st.rerun()
        else: st.error("❌"); st.stop()

st.sidebar.success(st.session_state.user)
if st.sidebar.button("Sair"): st.session_state.logged_in = False; st.rerun()

DB_PATH = "licitacontract.db"
def init_db(): 
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS contratos (
        id INTEGER PRIMARY KEY, numero TEXT UNIQUE, valor REAL, status TEXT, 
        data TEXT, objeto TEXT, reajuste TEXT, pdf_path TEXT, usuario TEXT
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

def extrair_contrato(pdf_bytes):
    """🔥 IA EXTRAI CONTRATO PMRO"""
    doc = fitz.open(stream=pdf_bytes.read(), filetype="pdf")
    texto_completo = ""
    for page in doc: texto_completo += page.get_text()
    doc.close()
    
    dados = {
        'objeto': re.search(r'OBJETO[:\s]*([^\n]{10,200})', texto_completo, re.I),
        'contrato': re.search(r'CONTRATO\s*N[°º]?\s*:?\s*(\d+/\d+)', texto_completo, re.I),
        'assinatura': re.search(r'(?:assinatura|data)[^\d]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})', texto_completo),
        'reajuste': re.search(r'(?:reajuste|sinapi)[^\n]*?(\w+/\d{4}|proposta|orçamento)', texto_completo, re.I),
        'valor': re.search(r'VALOR\s*TOTAL[:\s]*R\$\s*([\d,.]+)', texto_completo, re.I)
    }
    
    return {k: v.group(1).strip() if v else "NÃO ENCONTRADO" for k,v in dados.items()}

st.title("🏗️ LicitaContract PMRO **v3.0 PDF IA**")

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📄 UPLOAD PDF IA", "📈 Analytics"])

with tab1:
    df = get_data()
    col1, col2 = st.columns(2)
    col1.metric("Obras", len(df)); col2.metric("Valor", f"R$ {df.valor.sum():,.0f}")
    st.dataframe(df[['numero','valor','status','objeto','reajuste']], use_container_width=True)

with tab2:
    st.header("🚀 UPLOAD CONTRATO PDF - IA EXTRAI!")
    pdf_upload = st.file_uploader("📄 Escolha PDF Contrato", type="pdf")
    
    if pdf_upload:
        st.success(f"✅ PDF: {pdf_upload.name}")
        
        # 🔥 EXTRAÇÃO IA
        with st.spinner("🤖 Analisando contrato..."):
            dados_pdf = extrair_contrato(pdf_upload)
        
        col1, col2 = st.columns(2)
        col1.json(dados_pdf)
        
        # FORM AUTO-PREENCHIDO
        with st.form("contrato_ia"):
            numero = st.text_input("Contrato Nº", dados_pdf['contrato'])
            valor_str = st.text_input("Valor Total", dados_pdf['valor'])
            valor = float(valor_str.replace('R$','').replace('.','').replace(',','.')) if valor_str != "NÃO ENCONTRADO" else 0
            objeto = st.text_area("Objeto", dados_pdf['objeto'], height=100)
            reajuste = st.text_input("Reajuste", dados_pdf['reajuste'])
            status = st.selectbox("Status", ["Em execução", "Concluído"])
            
            if st.form_submit_button("💾 Salvar Contrato IA"):
                conn = sqlite3.connect(DB_PATH)
                try:
                    conn.execute("INSERT INTO contratos VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?)",
                               (numero, valor, status, datetime.now().strftime("%Y-%m-%d"), 
                                objeto, reajuste, pdf_upload.name, st.session_state.user))
                    conn.commit()
                    st.balloons(); st.success("🎉 CONTRATO IA SALVO!"); st.rerun()
                except: st.error("❌ Duplicado")
                conn.close()

with tab3:
    df = get_data()
    col1, col2 = st.columns(2)
    px.pie(df, names='status').show()
    px.bar(df, x='numero', y='valor').show()

# DOWNLOAD
if st.sidebar.button("📥 Export Todos"):
    csv = get_data().to_csv(index=False).encode('utf-8')
    st.download_button("CSV", csv, "pmro_v3.csv")
