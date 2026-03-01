import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, date
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

@st.cache_data(ttl=10)
def get_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM contratos ORDER BY data DESC", conn)
    conn.close()
    return df

st.title("🏗️ LicitaContract PMRO")
st.caption("Prefeitura Porto Velho - Eng. Guilherme Baldin")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "➕ Cadastrar", "📈 Gráficos", "📥 Export"])

with tab1:
    st.header("Dashboard Avançado")
    df = get_data()
    
    if len(df) > 0:
        # Filtros
        col1, col2, col3 = st.columns(3)
        status_filter = col1.multiselect("Status", df.status.unique())
        min_valor = col2.number_input("Valor ≥", value=0.0)
        search_num = col3.text_input("Buscar Nº")
        
        df_filt = df[
            (df.valor >= min_valor) &
            (df.status.isin(status_filter) if status_filter else True) &
            (df.numero.str.contains(search_num, case=False) if search_num else True)
        ]
        
        # Métricas
        col1, col2, col3 = st.columns(3)
        col1.metric("Total", len(df_filt))
        col2.metric("Valor", f"R$ {df_filt.valor.sum():,.0f}")
        col3.metric("Em Execução", len(df_filt[df_filt.status=='Em execução']))
        
        st.dataframe(df_filt, use_container_width=True)
    else:
        st.info("Cadastre obras!")

with tab2:
    st.header("Cadastrar")
    with st.form("form"):
        col1, col2 = st.columns(2)
        numero = col1.text_input("Número Contrato")
        valor = col2.number_input("Valor", value=0.0)
        status = st.selectbox("Status", ["Em execução", "Concluído", "Paralisado"])
        obs = st.text_area("Observações")
        if st.form_submit_button("Salvar"):
            conn = sqlite3.connect(DB_PATH)
            try:
                conn.execute("INSERT INTO contratos (numero, valor, status, data, observacoes) VALUES (?, ?, ?, ?, ?)",
                           (numero, valor, status, datetime.now().strftime("%Y-%m-%d"), obs))
                conn.commit()
                st.success("✅ Salvo!")
                st.rerun()
            except:
                st.error("❌ Já existe")
            conn.close()

with tab3:
    st.header("Gráficos")
    df = get_data()
    if len(df) > 0:
        col1, col2 = st.columns(2)
        fig1 = px.pie(df, names='status')
        col1.plotly_chart(fig1)
        fig2 = px.bar(df, x='numero', y='valor')
        col2.plotly_chart(fig2)

with tab4:
    st.header("Export")
    df = get_data()
    if len(df) > 0:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Obras', index=False)
        st.download_button("Excel Completo", output.getvalue(), "PMRO_obras.xlsx")

    tab5 = st.tabs(["📊 Dashboard", "➕ Cadastrar", "📈 Gráficos", "📥 Export", "📁 Upload"])[-1]

with tab5:
    st.header("📁 Import Excel")
    uploaded_file = st.file_uploader("Escolha planilha obras", type=['xlsx', 'xls'])
    
    if uploaded_file:
        df_upload = pd.read_excel(uploaded_file)
        st.write("Prévia:")
        st.dataframe(df_upload.head())
        
        if st.button("✅ Importar Obras"):
            conn = sqlite3.connect(DB_PATH)
            try:
                # Ajuste colunas sua planilha
                df_upload['data'] = datetime.now().strftime("%Y-%m-%d")
                df_upload.to_sql('contratos', conn, if_exists='append', index=False)
                conn.close()
                st.success(f"✅ {len(df_upload)} obras importadas!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro colunas: {e}")
