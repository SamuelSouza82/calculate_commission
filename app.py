import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="DigiSac - Gestão de Metas", layout="wide", page_icon="🎯")

# --- LÓGICA DE NEGÓCIO ---

def calculate_commission_standard(sales_value, target_value):
    if target_value == 0: return 0.0
    achievement = (sales_value / target_value) * 100
    rate = 0.0
    if 50 <= achievement < 80: rate = 0.015
    elif 80 <= achievement < 100: rate = 0.02
    elif 100 <= achievement < 110: rate = 0.04
    elif achievement >= 110: rate = 0.08
    return sales_value * rate, rate * 100, achievement

def calculate_commission_waba(sales_value):
    return sales_value * 0.10

def format_brl(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- INTERFACE ---

st.title("🎯 Gerenciador de Metas Comercial – DigiSac")
st.markdown("---")

# Sidebar - Configurações e Upload
with st.sidebar:
    st.header("⚙️ Configurações")
    seller_name = st.text_input("Nome do Vendedor", "João Silva")
    target_value = st.number_input("Meta Mensal (R$)", min_value=0.0, value=50000.0, step=1000.0)
    
    st.markdown("---")
    st.header("📥 Importar Dados")
    uploaded_file = st.file_uploader("Upload Excel (Vendas)", type=["xlsx", "xls"])
    
    st.info("""
    **Formato Esperado:**
    - Colunas: Nome, Tipo, Status, Valor, Data
    - Status 'Pago' conta para meta.
    """)

# Dados Simulados (Caso não haja upload)
if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        # Normalização básica
        df.columns = df.columns.str.strip().str.lower()
        # Filtro Pago
        if 'status' in df.columns:
            df = df[df['status'].astype(str).str.lower() == 'pago']
        # Limpeza de valor
        if 'valor' in df.columns:
            df['valor'] = df['valor'].astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.').astype(float)
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}")
        df = pd.DataFrame()
else:
    # Dados Mockados para demonstração
    data = {
        'tipo': ['Standard', 'Standard', 'WABA', 'Trial', 'Standard', 'WABA'],
        'valor': [5000, 12000, 3000, 1000, 8000, 5000],
        'data': pd.date_range(start='2023-10-01', periods=6)
    }
    df = pd.DataFrame(data)

# --- PROCESSAMENTO ---

if not df.empty:
    # Separação por Tipo
    val_standard = df[df['tipo'].astype(str).str.lower() == 'standard']['valor'].sum()
    val_waba = df[df['tipo'].astype(str).str.lower() == 'waba']['valor'].sum()
    val_trial = df[df['tipo'].astype(str).str.lower() == 'trial']['valor'].sum()
    
    total_revenue = val_standard + val_waba + val_trial
    progress_percent = (total_revenue / target_value) * 100 if target_value > 0 else 0
    
    # Cálculo Comissões
    comm_standard, rate_standard, achievement = calculate_commission_standard(val_standard, target_value)
    comm_waba = calculate_commission_waba(val_waba)
    total_commission = comm_standard + comm_waba

    # --- DASHBOARD ---
    
    # KPIs
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    with kpi1:
        st.metric("Faturamento Total", format_brl(total_revenue))
    with kpi2:
        st.metric("Progresso da Meta", f"{progress_percent:.1f}%", delta=f"{format_brl(total_revenue - target_value)}")
    with kpi3:
        st.metric("Comissão Estimada", format_brl(total_commission), delta=f"{rate_standard:.1f}% (Standard)")
    with kpi4:
        st.metric("Vendas Pagas", len(df))

    st.markdown("---")

    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Distribuição por Tipo")
        fig_pie = px.pie(values=[val_standard, val_waba, val_trial], 
                         names=['Standard', 'WABA', 'Trial'],
                         color=['Standard', 'WABA', 'Trial'],
                         color_discrete_map={'Standard': '#3B82F6', 'WABA': '#10B981', 'Trial': '#F59E0B'})
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col2:
        st.subheader("📈 Evolução de Vendas")
        df['data'] = pd.to_datetime(df['data'])
        df_sorted = df.sort_values('data')
        fig_bar = px.bar(df_sorted, x='data', y='valor', color='tipo',
                         color_discrete_map={'Standard': '#3B82F6', 'WABA': '#10B981', 'Trial': '#F59E0B'})
        st.plotly_chart(fig_bar, use_container_width=True)

    # Tabela de Comissões
    st.subheader("💰 Detalhamento de Comissão")
    st.write(f"**Vendedor:** {seller_name}")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.info(f"""
        **Standard**  
        Vendido: {format_brl(val_standard)}  
        Taxa Aplicada: {rate_standard:.1f}%  
        **Comissão: {format_brl(comm_standard)}**
        """)
    with col_c2:
        st.success(f"""
        **WABA**  
        Vendido: {format_brl(val_waba)}  
        Taxa Fixa: 10%  
        **Comissão: {format_brl(comm_waba)}**
        """)

    # Barra de Progresso Visual
    st.markdown("### 🏁 Progresso da Meta")
    st.progress(min(progress_percent / 100, 1.0))
    if progress_percent >= 100:
        st.balloons()
        st.success("🎉 Parabéns! Meta batida!")
    elif progress_percent >= 80:
        st.warning("⚠️ Quase lá! Falta pouco para a faixa de 4%.")
    else:
        st.info("💪 Continue focado para atingir a meta mínima de 50%.")

else:
    st.warning("Nenhuma venda encontrada para exibir. Faça o upload de uma planilha.")

# Footer
st.markdown("---")
st.caption("Sistema DigiSac v1.0 • Desenvolvido para Gestão Comercial")
