import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pdfplumber
import re
from datetime import datetime, timedelta
import io

# Configuração da página
st.set_page_config(
    layout="wide",
    page_icon="🏛️",
    page_title="LicitaContract PMRO Pro",
    initial_sidebar_state="expanded"
)

# Banco de dados
@st.cache_resource
def init_db():
    conn = sqlite3.connect('licitacontract_pmro.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contratos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT UNIQUE NOT NULL,
            valor REAL NOT NULL,
            reajuste REAL DEFAULT 0,
            status TEXT DEFAULT 'Ativo',
            data_cadastro DATE DEFAULT CURRENT_DATE,
            data_vencimento DATE,
            objeto TEXT,
            empresa TEXT,
            pdf_anexo TEXT,
            usuario TEXT
        )
    ''')
    conn.commit()
    return conn

# Funções utilitárias
def extrair_dados_pdf(pdf_file):
    texto = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            texto += page.extract_text() or ""
    
    # Regex otimizados baseados nos exemplos PMRO reais
    numero_match = re.search(r'\b(?:CONTRATO|PROCESSO)\s*[Nºn°ºoO]\s*:?\s*([0-9]{3}/PGM/[0-9]{4})\b', texto, re.IGNORECASE)
    numero = numero_match.group(1) if numero_match else "❌ Não encontrado"
    
    valor_match = re.search(r'valor\s+(?:desta\s+)?contrat(?:a|ação).*?R\$\s*([\d.,]+)', texto, re.IGNORECASE | re.DOTALL)
    if valor_match:
        valor_txt = valor_match.group(1).replace('.', '').replace(',', '.')
        valor = float(valor_txt)
    else:
        valor = 0
    
    reajuste_match = re.search(r'reajuste.*?([\d.,]+%?)', texto, re.IGNORECASE)
    reajuste = float(reajuste_match.group(1).replace(',', '.').replace('%', '')) if reajuste_match else 0
    
    return {
        'numero': numero,
        'valor': valor,
        'reajuste': reajuste,
        'texto_completo': texto[:2000] + "..." if len(texto) > 2000 else texto
    }

def carregar_dados():
    conn = init_db()
    df = pd.read_sql_query("SELECT * FROM contratos ORDER BY data_cadastro DESC", conn)
    conn.close()
    return df

# Sessão de login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# Sidebar com header profissional
with st.sidebar:
    st.markdown("""
    <div style='background: linear-gradient(90deg, #1e3a8a, #3b82f6); padding: 1rem; border-radius: 10px; color: white; text-align: center;'>
        <h2>🏛️ LicitaContract PMRO Pro</h2>
        <p>Gestão Profissional de Contratos - SEINFRA</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.logged_in:
        st.title("🔐 Login")
        username = st.text_input("👤 Usuário", placeholder="Guilherme Ritter Baldin")
        password = st.text_input("🔑 Senha", type="password", placeholder="******")
        if st.button("Entrar", type="primary"):
            if username and password:  # Simples para demo
                st.session_state.user = username
                st.session_state.logged_in = True
                st.rerun()
    else:
        st.success(f"👋 Bem-vindo, {st.session_state.user}!")
        if st.button("🚪 Sair"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()
    
    st.markdown("---")
    st.caption("Versão 4.0 Pro | 2026")

if not st.session_state.logged_in:
    st.info("🔐 Faça login para acessar o sistema.")
else:
    # Header principal
    st.markdown("""
    <div style='background: linear-gradient(90deg, #1e40af, #3b82f6); padding: 2rem; border-radius: 15px; color: white; text-align: center; margin-bottom: 2rem;'>
        <h1>📋 Gestão de Contratos PMRO</h1>
        <p>Sistema Profissional para Análise, Controle e Relatórios de Licitações</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs profissionais
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Novo Contrato", "📊 Dashboard", "📋 Todos Contratos", "📈 Relatórios Avançados"])
    
    with tab1:
        st.subheader("Upload e Extração Inteligente de PDF")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            uploaded_pdf = st.file_uploader("📄 Upload PDF Contrato", type="pdf")
        with col2:
            manual_numero = st.text_input("🔢 Número Manual (ex: 010/PGM/2026)")
            manual_valor = st.number_input("💰 Valor Manual (R$)", value=0.0, step=1000.0)
            manual_reajuste = st.number_input("📈 Reajuste (%)", value=0.0)
        
        if uploaded_pdf:
            dados = extrair_dados_pdf(uploaded_pdf)
            st.subheader("🤖 Extração IA Automática")
            st.metric("Número do Contrato", dados['numero'])
            st.metric("Valor Total", f"R$ {dados['valor']:,.2f}")
            st.metric("Reajuste", f"{dados['reajuste']:.2f}%")
            
            with st.expander("🔍 Texto Completo do PDF (Ctrl+F para buscar)"):
                st.text_area("", dados['texto_completo'], height=200)
        
        # Formulário de salvamento
        st.subheader("💾 Salvar Contrato")
        objeto = st.text_area("📝 Objeto da Obra", height=80)
        empresa = st.text_input("🏢 Empresa Contratada")
        data_vencimento = st.date_input("📅 Data Prevista de Vencimento", value=datetime.now() + timedelta(days=365))
        
        if st.button("✅ Salvar Contrato", type="primary"):
            conn = init_db()
            numero_final = dados['numero'] if uploaded_pdf and dados['numero'] != "❌" else manual_numero
            valor_final = dados['valor'] if uploaded_pdf and dados['valor'] > 0 else manual_valor
            reajuste_final = dados['reajuste'] if uploaded_pdf else manual_reajuste
            
            try:
                conn.execute('''
                    INSERT INTO contratos (numero, valor, reajuste, status, data_vencimento, objeto, empresa, pdf_anexo, usuario)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (numero_final, valor_final, reajuste_final, 'Ativo', data_vencimento, objeto, empresa, uploaded_pdf.name if uploaded_pdf else '', st.session_state.user))
                conn.commit()
                st.balloons()
                st.success(f"✅ Contrato {numero_final} salvo com sucesso!")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("❌ Número de contrato já existe!")
            finally:
                conn.close()
    
    with tab2:
        df = carregar_dados()
        if not df.empty:
            col1, col2, col3 = st.columns(3)
            total_contratos = len(df)
            valor_total = df['valor'].sum()
            valor_medio = df['valor'].mean()
            
            col1.metric("📋 Total Contratos", f"{total_contratos:,}")
            col2.metric("💰 Valor Total", f"R$ {valor_total:,.2f}")
            col3.metric("📊 Valor Médio", f"R$ {valor_medio:,.2f}")
            
            # Gráficos profissionais
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=('Valor por Contrato', 'Status dos Contratos'),
                specs=[[{"type": "bar"}, {"type": "pie"}]]
            )
            
            fig.add_trace(
                go.Bar(x=df['numero'], y=df['valor'], marker_color='#3b82f6', name='Valores'),
                row=1, col=1
            )
            fig.add_trace(
                go.Pie(labels=df['status'], values=df['valor'], name='Status'),
                row=1, col=2
            )
            
            fig.update_layout(height=500, showlegend=False, title_text="Dashboard Executivo PMRO")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("👆 Cadastre o primeiro contrato na aba ao lado!")
    
    with tab3:
        df = carregar_dados()
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Exportar Excel Oficial PMRO",
                data=csv_data,
                file_name=f"PMRO_Contratos_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        else:
            st.info("📋 Nenhum contrato cadastrado ainda.")
    
    with tab4:
        st.subheader("🔍 Filtros Avançados")
        min_valor = st.slider("Valor Mínimo (R$)", 0, int(carregar_dados()['valor'].max()), 0)
        status_filtro = st.multiselect("Status", ['Ativo', 'Vencido', 'Em Andamento'], default=['Ativo'])
        
        df_filtrado = carregar_dados()
        df_filtrado = df_filtrado[df_filtrado['valor'] >= min_valor]
        df_filtrado = df_filtrado[df_filtrado['status'].isin(status_filtro)]
        
        st.dataframe(df_filtrado, use_container_width=True)
        
        if st.button("📊 Gerar Relatório PDF", type="secondary"):
            st.info("📄 Relatório em desenvolvimento - Exporte CSV por enquanto!")

# Footer profissional
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6b7280;'>
    <p>🏛️ <strong>Sistema LicitaContract PMRO Pro v4.0</strong> | Desenvolvido para SEINFRA - Prefeitura de Porto Velho<br>
    © 2026 Guilherme Ritter Baldin | Baseado em OrçaFascio.com [web:0][cite:6][page:1]</p>
</div>
""", unsafe_allow_html=True)
