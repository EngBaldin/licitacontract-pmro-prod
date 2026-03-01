import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import pdfplumber
import re
from datetime import datetime
import io

# Config
st.set_page_config(layout="wide", page_icon="🏗️", page_title="LicitaContract PMRO")

# Inicializa session
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# LOGIN PAGE
if not st.session_state.logged_in:
    st.title("🔐 LicitaContract PMRO v3.2")
    st.markdown("### Acesso Restrito - Engenharia PMRO")
    
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("👤 Usuário PMRO")
    with col2:
        password = st.text_input("🔑 Senha", type="password")
    
    if st.button("🚀 Entrar no Sistema", type="primary", use_container_width=True):
        if (username == "guilherme" and password == "engenharia123") or \
           (username == "engenheiro" and password == "pmro2026"):
            st.session_state.logged_in = True
            st.session_state.user = username.title()
            st.success("✅ Acesso liberado!")
            st.rerun()
        else:
            st.error("❌ Credenciais inválidas!")
    st.stop()

# APP PRINCIPAL
st.sidebar.title("👋 Olá!")
st.sidebar.success(f"**{st.session_state.user}**")
if st.sidebar.button("🔓 Logout"):
    st.session_state.logged_in = False
    st.session_state.user = None
    st.rerun()

DB_PATH = "pmro_contratos.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS contratos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT UNIQUE,
        valor REAL,
        status TEXT,
        data_contrato TEXT,
        objeto TEXT,
        reajuste TEXT,
        pdf_nome TEXT,
        usuario TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

@st.cache_data(ttl=300)
def carregar_dados():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM contratos ORDER BY data_contrato DESC", conn)
    conn.close()
    return df.fillna('')

def extrair_dados_pdf(pdf_file):
    dados = {
        'contrato': 'NÃO ENCONTRADO', 'valor': 'NÃO ENCONTRADO', 
        'objeto': 'NÃO ENCONTRADO', 'reajuste': 'NÃO ENCONTRADO'
    }
    try:
        with pdfplumber.open(pdf_file) as pdf:
            texto = ''
            for pagina in pdf.pages:
                pagina_texto = pagina.extract_text()
                if pagina_texto: texto += pagina_texto
        
        # Regex otimizados PMRO
        regex = {
            'contrato': r'(?:CONTRATO|PROCESSO)\s*[Nº°]?\s*[:\-]?\s*(\d+/\d+(?:/\d+)?)',
            'valor': r'(?:VALOR\s*(?:TOTAL|CONTRATUAL)|TOTAL\s*(?:DO\s*)?CONTRATO)\s*[:\-]?\s*R?\$?\s*([\d\.,]+(?:\s*\(.*?R\$\s*[\d\.,]+\))?)?',
            'objeto': r'OBJETO\s*[:\-]?\s*([A-Z][^.\n]{15,400})',
            'reajuste': r'(?:REAJUSTE|INDEXADOR|SINAPI)[^.\n]*?(?:referência|contar|inicia)[^.\n]*?(\w+/\d{4}|proposta|orçamento|assinatura)'
        }
        
        for campo, padrao in regex.items():
            achou = re.search(padrao, texto, re.IGNORECASE | re.DOTALL)
            if achou: dados[campo] = achou.group(1).strip()
            
    except Exception as e:
        st.error(f"Erro PDF: {e}")
    
    return dados

st.title("🏗️ LicitaContract PMRO **v3.2 - PDF Inteligente**")
st.caption("Prefeitura Municipal de Porto Velho - Engenharia Civil")

# DASHBOARD PRINCIPAL
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📄 Upload PDF IA", "📈 Relatórios"])

with tab1:
    df = carregar_dados()
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Contratos", len(df))
    col2.metric("Valor Total", f"R$ {df['valor'].sum():,.0f}")
    col3.metric("Processados IA", len(df[df['objeto'] != 'NÃO ENCONTRADO']))
    
    st.subheader("📋 Lista Contratos")
    st.dataframe(df[['numero', 'valor', 'status', 'objeto', 'reajuste', 'usuario']], 
                use_container_width=True)

with tab2:
    st.header("🤖 Upload Contrato PDF - Extração Automática")
    pdf_upload = st.file_uploader("📁 Selecione PDF do Contrato", type=['pdf'])
    
    if pdf_upload is not None:
        st.success(f"✅ Carregado: **{pdf_upload.name}**")
        
        with st.spinner("🔍 IA processando documento..."):
            dados_extraidos = extrair_dados_pdf(pdf_upload)
        
        # EXIBIR EXTRAÇÃO
        col_esq, col_dir = st.columns([1, 2])
        with col_esq:
            st.markdown("### 📋 Dados Extraídos")
            for campo, valor in dados_extraidos.items():
                st.write(f"**{campo.upper()}**: {valor}")
        
        # FORMULÁRIO PRE-PREENCHIDO
        with st.form(key="form_contrato"):
            st.subheader("✏️ Confirmar e Salvar")
            
            numero = st.text_input("Contrato Nº", value=dados_extraidos['contrato'])
            valor_raw = st.text_input("Valor Total", value=dados_extraidos['valor'])
            try:
                valor = float(valor_raw.replace('R$', '').replace('.', '').replace(',', '.'))
            except:
                valor = 0.0
            
            objeto = st.text_area("Objeto do Contrato", value=dados_extraidos['objeto'], height=100)
            reajuste = st.text_input("Data/Base Reajuste", value=dados_extraidos['reajuste'])
            status = st.selectbox("Status Atual", ["Em execução", "Concluído", "Paralisado"])
            
            col_btn1, col_btn2 = st.columns(2)
            if col_btn1.form_submit_button("💾 Salvar Contrato", use_container_width=True):
                conn = sqlite3.connect(DB_PATH)
                try:
                    conn.execute("""INSERT INTO contratos 
                                  (numero, valor, status, data_contrato, objeto, reajuste, pdf_nome, usuario)
                                  VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                               (numero, valor, status, datetime.now().strftime("%d/%m/%Y"),
                                objeto, reajuste, pdf_upload.name, st.session_state.user))
                    conn.commit()
                    st.balloons()
                    st.success(f"🎉 Contrato **{numero}** salvo com IA!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("❌ Número de contrato já existe!")
                except Exception as e:
                    st.error(f"Erro: {e}")
                finally:
                    conn.close()
    
    else:
        st.info("👆 Faça upload de um PDF de contrato para análise automática")

with tab3:
    df = carregar_dados()
    col1, col2 = st.columns(2)
    
    fig_status = px.pie(df, names='status', title="Distribuição por Status")
    col1.plotly_chart(fig_status, use_container_width=True)
    
    fig_valor = px.bar(df, x='numero', y='valor', title="Valores por Contrato")
    col2.plotly_chart(fig_valor, use_container_width=True)

# SIDEBAR DOWNLOAD
with st.sidebar:
    st.markdown("### 📥 Exportar")
    df_all = carregar_dados()
    csv_data = df_all.to_csv(index=False).encode('utf-8')
    st.download_button("📊 Todos Contratos CSV", csv_data, 
                      f"PMRO_Contratos_{datetime.now().strftime('%Y%m%d')}.csv",
                      use_container_width=True)
    
st.markdown("---")
st.caption("🏛️ Prefeitura de Porto Velho | Sistema de Licitações v3.2")
