import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import io

st.set_page_config(layout="wide", page_title="OrçaFascio PMRO", page_icon="🏗️")

# LOGIN PMRO
if 'user' not in st.session_state:
    st.session_state.user = None
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 OrçaFascio PMRO")
    st.markdown("### Gestão de Obras - Prefeitura Porto Velho")
    col1, col2 = st.columns(2)
    u = col1.text_input("👤 Usuário")
    p = col2.text_input("🔑 Senha", type="password")
    if st.button("🚀 Acessar"):
        if (u == "guilherme" and p == "engenharia123") or (u == "engenheiro" and p == "pmro2026"):
            st.session_state.user = u.title()
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

st.sidebar.image("https://orcafascio.com/wp-content/uploads/2023/11/orcafascio-logo.png", width=200)
st.sidebar.success(f"👋 {st.session_state.user}")

DB = "orcafascio_pmro.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS obras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT UNIQUE,
        descricao TEXT,
        valor_orcado REAL,
        status TEXT,
        data_cadastro TEXT,
        data_inicio DATE,
        data_fim DATE,
        percent_execucao REAL DEFAULT 0,
        usuario TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS itens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        obra_id INTEGER,
        item TEXT,
        quantidade REAL,
        unidade TEXT,
        valor_unitario REAL,
        valor_total REAL,
        FOREIGN KEY(obra_id) REFERENCES obras(id)
    )''')
    conn.commit()
    conn.close()

init_db()

@st.cache_data(ttl=300)
def get_obras():
    conn = sqlite3.connect(DB)
    df_obras = pd.read_sql("SELECT * FROM obras ORDER BY id DESC", conn)
    df_itens = pd.read_sql("SELECT * FROM itens", conn)
    conn.close()
    return df_obras, df_itens

df_obras, df_itens = get_obras()

st.title("🏗️ **OrçaFascio PMRO**")
st.caption("Gestão Completa de Obras | SINAPI/CBUQ | Planejamento | Controle")

# DASHBOARD
col1, col2, col3, col4 = st.columns(4)
col1.metric("Obras", len(df_obras))
col2.metric("Valor Orçado", f"R$ {df_obras.valor_orcado.sum():,.0f}")
col3.metric("Em Execução", len(df_obras[df_obras.status=='Em Execução']))
col4.metric("% Execução Média", f"{df_obras.percent_execucao.mean():.1f}%")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "➕ Nova Obra", "📋 Planejamento", "📈 Relatórios"])

with tab1:
    st.header("📊 Visão Geral")
    # Gráfico Status
    fig_status = px.pie(df_obras, names='status', title="Status Obras")
    st.plotly_chart(fig_status, use_container_width=True)
    
    # Tabela Obras
    st.subheader("Obras Ativas")
    st.dataframe(df_obras[['numero','descricao','valor_orcado','percent_execucao','status']], use_container_width=True)

with tab2:
    st.header("➕ Nova Obra")
    with st.form("nova_obra"):
        col1, col2 = st.columns(2)
        numero = col1.text_input("Número Obra (ex: 010/PGM/2026)")
        descricao = col1.text_area("Descrição/Objeto", height=80)
        
        col3, col4 = st.columns(2)
        valor_orcado = col3.number_input("Valor Orçado R$", format="R$ %.2f")
        status = col4.selectbox("Status", ["Planejamento", "Em Execução", "Concluída", "Paralisada"])
        
        col5, col6 = st.columns(2)
        data_inicio = col5.date_input("Início Previsto")
        data_fim = col6.date_input("Fim Previsto")
        
        if st.form_submit_button("🚀 Criar Obra"):
            conn = sqlite3.connect(DB)
            c = conn.cursor()
            try:
                c.execute("INSERT INTO obras (numero,descricao,valor_orcado,status,data_cadastro,data_inicio,data_fim,usuario) VALUES(?,?,?,?,?,?,?,?)",
                        (numero, descricao, valor_orcado, status, datetime.now().strftime("%d/%m/%Y"), data_inicio, data_fim, st.session_state.user))
                conn.commit()
                st.success("✅ Obra criada!")
                st.rerun()
            except:
                st.error("❌ Número duplicado")
            conn.close()

with tab3:
    st.header("📋 Planejamento & Medição")
    obra_selecionada = st.selectbox("Obra", df_obras.numero.tolist())
    
    if obra_selecionada:
        obra = df_obras[df_obras.numero == obra_selecionada].iloc[0]
        st.info(f"**{obra.descricao}** | Orçado: R$ {obra.valor_orcado:,.0f}")
        
        # Cronograma Gantt
        st.subheader("📅 Cronograma")
        fig_gantt = px.timeline(df_obras[df_obras.numero==obra_selecionada], 
                               x_start="data_inicio", x_end="data_fim", 
                               text="numero", title="Planejamento")
        st.plotly_chart(fig_gantt)
        
        # Itens orçamento
        st.subheader("📐 Composições")
        with st.form("itens_form"):
            col1, col2, col3 = st.columns(3)
            item = col1.text_input("Item/Composição")
            qtd = col2.number_input("Qtd")
            und = col3.selectbox("Und", ["m²", "m³", "m", "un", "kg"])
            vu = st.number_input("Valor Unit. R$", format="R$ %.2f")
            
            if st.form_submit_button("➕ Adicionar Item"):
                valor_total = qtd * vu
                c.execute("INSERT INTO itens (obra_id,item,quantidade,unidade,valor_unitario,valor_total) VALUES(?,?,?,?,?,?)",
                         (obra.id, item, qtd, und, vu, valor_total))
                conn.commit()
                st.success("✅ Item adicionado!")
                st.rerun()

with tab4:
    st.header("📈 Relatórios PMRO")
    
    # Gráfico Evolução
    fig_evo = px.bar(df_obras, x='numero', y='valor_orcado', 
                    color='status', title="Valor por Obra")
    st.plotly_chart(fig_evo)
    
    # Tabela Completa
    st.dataframe(df_obras, use_container_width=True)
    
    # Download
    csv = df_obras.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Excel Oficial PMRO", csv, f"PMRO_Orcafascio_{datetime.now().strftime('%Y%m%d')}.csv")

st.markdown("---")
st.caption("🏛️ OrçaFascio PMRO | Baseado OrçaFascio.com | Engenharia Civil Porto Velho")
