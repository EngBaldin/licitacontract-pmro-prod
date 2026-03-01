import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

st.set_page_config(layout="wide", page_icon="🏗️")

DB_PATH = "licitacontract.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS contratos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT UNIQUE,
        valor REAL,
        status TEXT,
        data TEXT,
        observacoes TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

@st.cache_data(ttl=30)
def get_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM contratos ORDER BY data DESC", conn)
    conn.close()
    return df

st.title("🏗️ LicitaContract PMRO")
st.caption("Prefeitura Porto Velho - Eng. Guilherme Baldin 2026")

# 5 TABS VISÍVEIS
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "➕ Cadastrar", "📈 Gráficos", "📥 Export", "📁 Upload"])

with tab1:
    st.header("📊 Dashboard Avançado")
    df = get_data()
    
    if len(df) > 0:
        # FILTROS SUPERIORES
        col1, col2, col3 = st.columns(3)
        status_filter = col1.multiselect("Status", options=df.status.unique(), default=df.status.unique())
        valor_min = col2.number_input("Valor Min. R$", value=float(df.valor.min()))
        busca = col3.text_input("Buscar Contrato")
        
        df_filt = df[
            (df.status.isin(status_filter)) &
            (df.valor >= valor_min) &
            (df.numero.str.contains(busca, case=False, na=False) if busca else True)
        ]
        
        # MÉTRICAS
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Obras", len(df_filt))
        col2.metric("Valor Total", f"R$ {df_filt.valor.sum():,.0f}")
        col3.metric("Em Execução", len(df_filt[df_filt.status == 'Em execução']))
        
        st.dataframe(df_filt, use_container_width=True)
    else:
        st.info("👆 Cadastre primeira obra!")

with tab2:
    st.header("➕ Nova Obra")
    with st.form("obra_form"):
        col1, col2 = st.columns([1,1])
        numero = col1.text_input("Número Contrato", help="Ex: 001/2026")
        valor = col2.number_input("Valor R$", value=0.0, format="%.2f")
        col3, col4 = st.columns([1,2])
        status = col3.selectbox("Status", ["Em execução", "Concluído", "Paralisado"])
        obs = col4.text_area("Observações", help="Local, memorial...")
        
        if st.form_submit_button("✅ Salvar Obra", use_container_width=True):
            conn = sqlite3.connect(DB_PATH)
            try:
                conn.execute("""
                    INSERT INTO contratos (numero, valor, status, data, observacoes) 
                    VALUES (?, ?, ?, ?, ?)
                """, (numero, valor, status, datetime.now().strftime("%Y-%m-%d"), obs))
                conn.commit()
                st.success(f"✅ {numero} salva!")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("❌ Número já existe!")
            except Exception as e:
                st.error(f"Erro: {e}")
            finally:
                conn.close()

with tab3:
    st.header("📈 Analytics")
    df = get_data()
    if len(df) > 0:
        col1, col2 = st.columns(2)
        fig1 = px.pie(df, names='status', title="Distribuição Status")
        col1.plotly_chart(fig1, use_container_width=True)
        fig2 = px.bar(df, x='numero', y='valor', title="Valores Obras")
        fig2.update_xaxes(tickangle=45)
        col2.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Sem dados")

with tab4:
    st.header("📥 Relatórios")
    df = get_data()
    if len(df) > 0:
        st.dataframe(df)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Obras', index=False)
            resumo = df.groupby('status')['valor'].agg(['count', 'sum']).round()
            resumo.to_excel(writer, sheet_name='Resumo')
        st.download_button("📥 Excel PMRO", output.getvalue(), 
                          f"PMRO_obras_{datetime.now().strftime('%d%m%Y')}.xlsx", use_container_width=True)
    else:
        st.info("Sem dados")

with tab5:
    st.header("📁 Upload Planilhas")
    st.info("📋 Colunas: numero | valor | status | observacoes")
    
    uploaded = st.file_uploader("Escolha Excel", type=['xlsx'])
    
    if uploaded:
        df_upload = pd.read_excel(uploaded)
        st.write("**Prévia importação:**")
        st.dataframe(df_upload.head())
        
        col1, col2 = st.columns(2)
        if col1.button("✅ IMPORTAR", use_container_width=True):
            conn = sqlite3.connect(DB_PATH)
            try:
                df_upload['data'] = datetime.now().strftime("%Y-%m-%d")
                df_upload.to_sql('contratos', conn, if_exists='append', index=False)
                conn.close()
                st.success(f"✅ {len(df_upload)} obras importadas!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erro colunas: {e}")
        if col2.button("❌ Cancelar", use_container_width=True):
            st.rerun()

st.markdown("---")
st.caption("👨‍💼 Eng. Guilherme Baldin | Prefeitura Porto Velho")
