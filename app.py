import streamlit as st
import pandas as pd
import numpy as np
import io
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# =====================================================================
# 1. PAGE CONFIGURATION & CUSTOM STYLING (PREMIUM DESIGN)
# =====================================================================
st.set_page_config(
    page_title="Controle financeiro • Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Premium Design aesthetics (Strict Dark Theme)
st.markdown("""
    <style>
        /* Import premium font */
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: #0F172A;
            color: #F1F5F9;
        }
        
        /* Metric Card Container Styling (Premium Dark Glassmorphism) */
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 16px;
            padding: 20px 24px;
            box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease-in-out;
        }
        
        div[data-testid="stMetric"]:hover {
            transform: translateY(-4px);
            border-color: rgba(59, 130, 246, 0.4) !important;
            box-shadow: 0 8px 30px 0 rgba(59, 130, 246, 0.15);
        }
        
        /* Header gradient styling */
        .main-header {
            background: linear-gradient(120deg, #3B82F6 0%, #8B5CF6 50%, #EC4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
            font-size: 2.8rem;
            margin-bottom: 0.2rem;
            letter-spacing: -0.025em;
        }
        .sub-header {
            color: #94A3B8;
            font-size: 1.1rem;
            margin-bottom: 2rem;
            font-weight: 400;
        }
        
        /* Sidebar layout styling */
        .sidebar-title {
            font-size: 1.3rem;
            font-weight: 700;
            margin-bottom: 1rem;
            color: #3B82F6;
        }
        
        /* Custom alert box */
        .custom-card {
            background-color: rgba(59, 130, 246, 0.1);
            border-left: 5px solid #3B82F6;
            padding: 15px;
            border-radius: 4px 12px 12px 4px;
            margin-bottom: 1.5rem;
            color: #F1F5F9;
        }
    </style>
""", unsafe_allow_html=True)


# =====================================================================
# 2. GOOGLE DRIVE API CONNECTOR & ROBUST LOADING
# =====================================================================
def parse_csv_robust(file_buffer):
    """
    Parses a CSV buffer with automatic encoding and delimiter detection (supporting commas, semicolons, and tabs).
    """
    encodings = ['utf-8', 'latin1', 'iso-8859-1', 'utf-16']
    decoded_str = None
    used_encoding = 'utf-8'
    
    for enc in encodings:
        try:
            file_buffer.seek(0)
            decoded_str = file_buffer.read().decode(enc)
            used_encoding = enc
            break
        except Exception:
            continue
            
    if decoded_str is None:
        file_buffer.seek(0)
        return pd.read_csv(file_buffer)
        
    lines = [line for line in decoded_str.split('\n') if line.strip()]
    first_line = lines[0] if lines else ""
    
    # Count occurrence of potential separators
    delimiters = {',': first_line.count(','), ';': first_line.count(';'), '\t': first_line.count('\t')}
    best_delim = max(delimiters, key=delimiters.get)
    
    if delimiters[best_delim] == 0:
        best_delim = ','
        
    file_buffer.seek(0)
    return pd.read_csv(file_buffer, sep=best_delim, encoding=used_encoding)


def load_data_from_drive(credentials_file_path, file_id):
    """
    Downloads a CSV file from Google Drive using Service Account credentials.
    Supports loading from Streamlit secrets (gcp_service_account) or local credentials.json file.
    Returns a Pandas DataFrame or raises an exception with a descriptive error.
    """
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseDownload
    except ImportError:
        raise ImportError(
            "As bibliotecas 'google-api-python-client' e 'google-auth' são necessárias para conectar ao Google Drive. "
            "Certifique-se de instalá-las rodando: pip install google-api-python-client google-auth"
        )
        
    # API Read-Only scope for Google Drive
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    try:
        # Check Streamlit secrets first
        has_secrets = False
        try:
            if "gcp_service_account" in st.secrets:
                has_secrets = True
        except Exception:
            pass

        if has_secrets:
            # Load from Streamlit Secrets (recommended for Streamlit Community Cloud)
            creds = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"], scopes=SCOPES
            )
        else:
            # Fallback to local credentials file
            if not os.path.exists(credentials_file_path):
                raise FileNotFoundError(
                    f"Arquivo de credenciais não encontrado no caminho: '{credentials_file_path}'. "
                    "Para rodar online, certifique-se de configurar o secret 'gcp_service_account' no painel do Streamlit Cloud. "
                    "Para rodar localmente, certifique-se de que o arquivo 'credentials.json' está presente no diretório principal."
                )
            creds = service_account.Credentials.from_service_account_file(
                credentials_file_path, scopes=SCOPES
            )
        
        # Build Drive Service API
        service = build('drive', 'v3', credentials=creds)
        
        # Download file media content
        request = service.files().get_media(fileId=file_id)
        file_buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(file_buffer, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            
        file_buffer.seek(0)
        
        # Read downloaded bytes using robust CSV parser
        return parse_csv_robust(file_buffer)

    except Exception as e:
        error_msg = str(e)
        if "HttpError 404" in error_msg or "fileNotFound" in error_msg:
            raise Exception(
                "Arquivo do Google Drive não encontrado. Verifique se o ID do arquivo está correto e "
                "se você compartilhou o arquivo com o e-mail da Service Account."
            )
        elif "invalid_grant" in error_msg or "HttpError 401" in error_msg:
            raise Exception("Credenciais inválidas. Verifique se as configurações da Service Account estão corretas e ativas.")
        else:
            raise Exception(f"Erro na conexão com o Google Drive API: {error_msg}")


# =====================================================================
# 3. PANDAS DATA CLEANING & BUSINESS RULES PROCESSING
# =====================================================================
def process_financial_data(df):
    """
    Cleans and structures financial dataframe based on exact business rules:
    1. 'Efetivação' empty or '-' -> Pendente/A Pagar
    2. 'Efetivação' contains a valid date -> Paga
    3. Treat 'Valor' as numeric and 'Vencimento' as DD/MM/AAAA datetime.
    """
    # Clean up column names to avoid leading/trailing whitespace errors
    df.columns = [col.strip() for col in df.columns]
    
    # Check for required columns
    required_cols = ['Descrição', 'Valor', 'Vencimento', 'Efetivação', 'Categoria', 'Conta']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"O arquivo carregado não contém todas as colunas obrigatórias. "
            f"Colunas faltantes: {', '.join(missing_cols)}. "
            f"Colunas presentes: {', '.join(df.columns)}"
        )
    
    # Process string fields to prevent whitespace issues
    for col in ['Descrição', 'Categoria', 'Conta', 'Cartão']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Rule 3: Treat column 'Valor' to ensure it's numeric
    # Handles R$, dots as thousands/decimals, commas as decimals, negative values, and spaces
    def parse_valor(val):
        if pd.isna(val):
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        val_str = str(val).strip()
        val_str = val_str.replace('R$', '').replace('r$', '')
        val_str = val_str.strip()
        
        if not val_str:
            return 0.0
            
        # Support both dot as decimal (e.g. 31.50) and comma as decimal (e.g. 31,50)
        # If both comma and dot exist (e.g. 1.200,50), remove the dot and swap comma for dot
        if ',' in val_str and '.' in val_str:
            val_str = val_str.replace('.', '').replace(',', '.')
        elif ',' in val_str:
            # If only comma exists (e.g. 1200,50 or 31,50), replace with dot
            val_str = val_str.replace(',', '.')
        # If only dot exists (e.g. 31.50 or 1420.00), it's already in the correct format for float()
        
        try:
            return float(val_str)
        except ValueError:
            return 0.0

    df['Valor_Clean'] = df['Valor'].apply(parse_valor)
    
    # Rule 3: Convert 'Vencimento' to datetime (format DD/MM/AAAA)
    df['Vencimento_Parsed'] = pd.to_datetime(df['Vencimento'], format='%d/%m/%Y', errors='coerce')
    
    # Check for invalid dates in 'Vencimento'
    invalid_vencimento = df['Vencimento_Parsed'].isna() & df['Vencimento'].notna() & (df['Vencimento'].astype(str).str.strip() != '')
    if invalid_vencimento.any():
        st.sidebar.warning(
            f"Detectadas {invalid_vencimento.sum()} linhas com datas de Vencimento inválidas. "
            "Verifique se estão no formato brasileiro DD/MM/AAAA."
        )

    # Rules 1 & 2: Process payment status based on 'Efetivação'
    # "Pendente/A Pagar" if empty (NaN) or contains '-'
    efetivacao_clean = df['Efetivação'].astype(str).str.strip()
    is_pending = (
        df['Efetivação'].isna() | 
        (efetivacao_clean == '-') | 
        (efetivacao_clean == '') | 
        (efetivacao_clean.str.lower() == 'nan')
    )
    
    df['Status'] = np.where(is_pending, 'Pendente', 'Paga')
    
    # Convert 'Efetivação' to datetime for analytical metrics if needed
    df['Efetivação_Parsed'] = pd.to_datetime(df['Efetivação'], format='%d/%m/%Y', errors='coerce')
    
    # -----------------------------------------------------------------
    # Lote Payday Dynamic Classification Rule
    # -----------------------------------------------------------------
    def get_lote_info(row):
        dt = row['Vencimento_Parsed']
        if pd.isna(dt):
            return pd.Series([None, None, None])
        
        day = dt.day
        month = dt.month
        year = dt.year
        
        if 15 <= day <= 28:
            return pd.Series(["Dia 15", month, year])
        elif day >= 29:
            return pd.Series(["Dia 30", month, year])
        else: # day <= 14
            try:
                # Use DateOffset to subtract exactly 1 month robustly (handles year boundaries like Jan -> Dec automatically)
                prev_dt = dt - pd.DateOffset(months=1)
                return pd.Series(["Dia 30", prev_dt.month, prev_dt.year])
            except Exception:
                # Fallback manual calculation if anything goes wrong
                prev_month = month - 1 if month > 1 else 12
                prev_year = year if month > 1 else year - 1
                return pd.Series(["Dia 30", prev_month, prev_year])
                
    df[['Lote_Tipo', 'Lote_Mes', 'Lote_Ano']] = df.apply(get_lote_info, axis=1)
    df['Lote_Mes'] = pd.to_numeric(df['Lote_Mes'], errors='coerce')
    df['Lote_Ano'] = pd.to_numeric(df['Lote_Ano'], errors='coerce')
    
    return df


# =====================================================================
# 4. AUTOMATIC DATA LOADING FROM GOOGLE DRIVE
# =====================================================================
# Fallback supporting both 'credentials.json' and 'credential.json' naming
CREDENTIALS_FILE = "credentials.json"
if not os.path.exists(CREDENTIALS_FILE) and os.path.exists("credential.json"):
    CREDENTIALS_FILE = "credential.json"

DRIVE_FILE_ID = "12N8C_KQwt469sVaupDtIwA8BpBIiLcKB"

df_raw = None
error_encountered = False
error_details = ""

# Minimal collapsed sidebar with a simple status & refresh option
st.sidebar.markdown('<div class="sidebar-title">🔄 Operações</div>', unsafe_allow_html=True)
st.sidebar.info("Conectado automaticamente ao Google Drive.")
if st.sidebar.button("🔌 Sincronizar Agora", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# Run the real-time fetch on start
try:
    with st.spinner("Carregando suas finanças diretamente do Google Drive..."):
        df_raw = load_data_from_drive(CREDENTIALS_FILE, DRIVE_FILE_ID)
except Exception as e:
    error_encountered = True
    error_details = str(e)


# =====================================================================
# 5. MAIN PAGE RENDERING
# =====================================================================

# Title Section
st.markdown('<div class="main-header">💰 Controle financeiro</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Dashboard Financeiro Residencial Conectado à Nuvem</div>', unsafe_allow_html=True)

if error_encountered:
    st.error("### 🛑 Erro de Conexão ou Carregamento")
    st.markdown(f"""
        <div class="custom-card">
            <strong>Detalhes do Erro:</strong><br/>
            {error_details}
        </div>
        <p>Para solucionar, certifique-se de que o arquivo de credenciais Service Account (JSON) existe, que o ID do arquivo no Drive está correto 
        e que o arquivo no Google Drive foi compartilhado com o e-mail da Service Account.</p>
    """, unsafe_allow_html=True)
    
    # Offer fallback button to see demo data
    if st.button("Alternar para Dados de Demonstração para testar o App"):
        st.info("Altere a 'Fonte de Dados' na barra lateral esquerda para 'Dados de Demonstração (Local)' para testar a interface imediatamente.")
        
elif df_raw is not None:
    try:
        # Process and clean data using Pandas rules
        df_cleaned = process_financial_data(df_raw)
        
        # Portuguese months dictionary
        MESES = {
            1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
            5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
            9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
        }
        
        # Extract unique Year-Months from 'Lote_Ano' and 'Lote_Mes'
        df_cleaned['Lote_Period'] = df_cleaned.apply(
            lambda r: pd.Period(year=int(r['Lote_Ano']), month=int(r['Lote_Mes']), freq='M')
            if pd.notna(r['Lote_Mes']) and pd.notna(r['Lote_Ano']) else pd.NaT,
            axis=1
        )
        unique_periods = sorted(df_cleaned['Lote_Period'].dropna().unique())
        
        # Format periods as "Mês/Ano" (e.g. "Maio/2026")
        def format_period(p):
            return f"{MESES[p.month]}/{p.year}"
            
        period_options = [format_period(p) for p in unique_periods]
        
        # Determine current month string for default pre-selection
        now = datetime.now()
        current_period_str = f"{MESES[now.month]}/{now.year}"
        
        default_index = 0
        if current_period_str in period_options:
            default_index = period_options.index(current_period_str)
        elif len(period_options) > 0:
            # Fallback to the latest available month in the data
            default_index = len(period_options) - 1
            
        # Ensure we have at least one option
        if not period_options:
            period_options = [current_period_str]
            default_index = 0
            
        # -------------------------------------------------------------
        # MONTH FILTER SELECTOR AT THE TOP
        # -------------------------------------------------------------
        col_select, col_info = st.columns([1.2, 2.8])
        with col_select:
            selected_month_str = st.selectbox(
                "📅 Selecionar Mês de Referência:",
                options=period_options,
                index=default_index,
                help="Selecione o mês desejado para atualizar as métricas, gráficos e lotes de pagamento."
            )
        st.markdown("<br/>", unsafe_allow_html=True)
        
        # Parse selected month & year to filter the dataframe
        sel_month_name, sel_year_str = selected_month_str.split('/')
        sel_year = int(sel_year_str)
        sel_month_num = [k for k, v in MESES.items() if v == sel_month_name][0]
        
        # Filtered DataFrame for the monthly dashboard view (using Payday Lotes)
        df_filtered = df_cleaned[
            (df_cleaned['Lote_Mes'] == sel_month_num) &
            (df_cleaned['Lote_Ano'] == sel_year)
        ]
        
        # -------------------------------------------------------------
        # CALCULATE METRICS (using filtered monthly data)
        # -------------------------------------------------------------
        df_paid = df_filtered[df_filtered['Status'] == 'Paga']
        df_pending = df_filtered[df_filtered['Status'] == 'Pendente']
        
        total_pago = df_paid['Valor_Clean'].sum()
        total_pendente = df_pending['Valor_Clean'].sum()
        qtd_pendentes = len(df_pending)
        
        # -------------------------------------------------------------
        # METRIC CARDS (st.columns)
        # -------------------------------------------------------------
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="🟢 Total Pago",
                value=f"R$ {total_pago:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                help="Soma de todos os lançamentos que contêm uma data válida de Efetivação."
            )
            
        with col2:
            st.metric(
                label="🟡 Total Pendente (A Pagar)",
                value=f"R$ {total_pendente:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                help="Soma de todos os lançamentos com coluna Efetivação vazia ou contendo '-'."
            )
            
        with col3:
            st.metric(
                label="📅 Contas a Pagar",
                value=f"{qtd_pendentes} contas",
                help="Quantidade de lançamentos com pagamento pendente."
            )
            
        st.markdown("<br/>", unsafe_allow_html=True)
        
        # -------------------------------------------------------------
        # CHARTS VISUALIZATIONS SECTION (PREMIUM WOW FACTOR)
        # -------------------------------------------------------------
        # Add visual summaries to delight the user and provide maximum value
        st.markdown("### 📊 Visão Geral das Despesas")
        chart_col1, chart_col2 = st.columns([1, 1])
        
        with chart_col1:
            # Paid vs Pending stacked or comparison (Plotly Bar Chart)
            status_totals = df_filtered.groupby('Status')['Valor_Clean'].sum().reset_index()
            if not status_totals.empty:
                fig_bar = px.bar(
                    status_totals,
                    x='Status',
                    y='Valor_Clean',
                    color='Status',
                    title="Comparativo: Pago vs Pendente (R$)",
                    labels={'Valor_Clean': 'Valor (R$)'},
                    color_discrete_map={'Paga': '#10B981', 'Pendente': '#F59E0B'}
                )
                fig_bar.update_layout(
                    margin=dict(t=40, b=10, l=10, r=10),
                    height=300,
                    showlegend=False,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="Plus Jakarta Sans", size=12)
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Sem dados suficientes para exibir comparativo.")
                
        with chart_col2:
            # Lote Pending Totals (Plotly Bar Chart)
            lote_totals = pd.DataFrame([
                {'Lote': 'Dia 15', 'Valor_Clean': df_pending[df_pending['Lote_Tipo'] == 'Dia 15']['Valor_Clean'].sum()},
                {'Lote': 'Dia 30', 'Valor_Clean': df_pending[df_pending['Lote_Tipo'] == 'Dia 30']['Valor_Clean'].sum()}
            ])
            
            if lote_totals['Valor_Clean'].sum() > 0:
                fig_lote = px.bar(
                    lote_totals,
                    x='Lote',
                    y='Valor_Clean',
                    color='Lote',
                    title="Previsão de Saída por Lote Salário (R$)",
                    labels={'Valor_Clean': 'Valor Pendente (R$)', 'Lote': 'Lote Salário'},
                    color_discrete_map={'Dia 15': '#3B82F6', 'Dia 30': '#8B5CF6'}
                )
                fig_lote.update_layout(
                    margin=dict(t=40, b=10, l=10, r=10),
                    height=300,
                    showlegend=False,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="Plus Jakarta Sans", size=12)
                )
                fig_lote.update_traces(
                    texttemplate='R$ %{y:,.2f}',
                    textposition='outside'
                )
                st.plotly_chart(fig_lote, use_container_width=True)
            else:
                st.info("Nenhuma despesa pendente no mês para exibir a previsão por lote.")
                
        st.markdown("<br/>", unsafe_allow_html=True)
        
        # -------------------------------------------------------------
        # TABLE OF PENDING BILLS: SPLIT IN TWO PAYDAY TABS (Dia 15 & Dia 30)
        # -------------------------------------------------------------
        st.markdown("### 📋 Próximas Contas a Pagar")
        
        # Helper function to render a unified, sorted hybrid table for a given lote DataFrame
        def render_pending_table(df_lote_pending, title):
            if len(df_lote_pending) > 0:
                # Calculate sum total
                total_lote = df_lote_pending['Valor_Clean'].sum()
                
                # Display sum in a nice highlighted box
                st.markdown(
                    f"<div style='background-color: rgba(59, 130, 246, 0.05); padding: 12px 18px; border-radius: 12px; margin-bottom: 1.2rem; border: 1px solid rgba(59, 130, 246, 0.1);'>"
                    f"💰 Total Provisão do Lote: <span style='font-size:1.3rem; font-weight:700; color: #3B82F6;'>R$ {total_lote:,.2f}</span>"
                    f"</div>".replace(',', 'X').replace('.', ',').replace('X', '.'),
                    unsafe_allow_html=True
                )
                
                df_pending_processed = df_lote_pending.copy()
                
                # Helper to check if a record has a valid credit card
                def has_card(val):
                    if pd.isna(val):
                        return False
                    val_str = str(val).strip()
                    return val_str not in ['', '-', 'nan', 'None']
                
                # Ensure Card column exists and is stripped
                if 'Cartão' not in df_pending_processed.columns:
                    df_pending_processed['Cartão'] = '-'
                else:
                    df_pending_processed['Cartão'] = df_pending_processed['Cartão'].fillna('-').astype(str).str.strip()
                    
                df_pending_processed['Has_Card'] = df_pending_processed['Cartão'].apply(has_card)
                
                # Split into card and non-card dataframes
                df_with_card = df_pending_processed[df_pending_processed['Has_Card']]
                df_no_card = df_pending_processed[~df_pending_processed['Has_Card']]
                
                rows_to_combine = []
                
                # 1. Group records that have a credit card
                if len(df_with_card) > 0:
                    df_card_grouped = df_with_card.groupby('Cartão').agg(
                        Total_Valor=('Valor_Clean', 'sum'),
                        Min_Vencimento=('Vencimento_Parsed', 'min'),
                        Qtd_Contas=('Valor_Clean', 'count')
                    ).reset_index()
                    
                    # Build rows for each grouped credit card
                    for _, row in df_card_grouped.iterrows():
                        card_name = row['Cartão']
                        rows_to_combine.append({
                            'Descrição': f"💳 Fatura {card_name} ({row['Qtd_Contas']} itens)",
                            'Valor_Clean': row['Total_Valor'],
                            'Vencimento_Parsed': row['Min_Vencimento'],
                            'Categoria': "Cartão de Crédito",
                            'Conta': "-",
                            'Cartão': card_name
                        })
                
                # 2. Add individual records that have no credit card
                if len(df_no_card) > 0:
                    for _, row in df_no_card.iterrows():
                        rows_to_combine.append({
                            'Descrição': row['Descrição'],
                            'Valor_Clean': row['Valor_Clean'],
                            'Vencimento_Parsed': row['Vencimento_Parsed'],
                            'Categoria': row['Categoria'],
                            'Conta': row['Conta'],
                            'Cartão': '-'
                        })
                        
                # Create the combined DataFrame
                df_combined = pd.DataFrame(rows_to_combine)
                
                if not df_combined.empty:
                    # Sort combined by Vencimento_Parsed (due date) ascending
                    df_combined = df_combined.sort_values(by='Vencimento_Parsed', ascending=True)
                    
                    # Rename columns for visual presentation
                    df_display = df_combined[['Descrição', 'Valor_Clean', 'Vencimento_Parsed', 'Categoria', 'Conta', 'Cartão']].copy()
                    df_display.columns = ['Descrição', 'Valor (R$)', 'Vencimento', 'Categoria', 'Conta', 'Cartão']
                    
                    # Render the hybrid table
                    st.dataframe(
                        df_display,
                        column_config={
                            "Descrição": st.column_config.TextColumn(
                                "Descrição",
                                help="Nome da conta individual ou fatura de cartão consolidada",
                                width="medium"
                            ),
                            "Valor (R$)": st.column_config.NumberColumn(
                                "Valor (R$)",
                                help="Valor total da conta ou fatura",
                                format="R$ %.2f",
                                width="small"
                            ),
                            "Vencimento": st.column_config.DateColumn(
                                "Vencimento",
                                help="Vencimento individual ou data do primeiro vencimento do cartão",
                                format="DD/MM/YYYY",
                                width="medium"
                            ),
                            "Categoria": st.column_config.TextColumn(
                                "Categoria",
                                width="small"
                            ),
                            "Conta": st.column_config.TextColumn(
                                "Conta",
                                width="small"
                            ),
                            "Cartão": st.column_config.TextColumn(
                                "Cartão",
                                help="Cartão vinculado à despesa",
                                width="small"
                            )
                        },
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Local expander for individual detailed pending bills inside this lote
                    with st.expander(f"🔍 Detalhar Itens Pendentes do {title} (Individual)"):
                        st.markdown("Confira a lista completa e de cada conta individual deste lote:")
                        df_pending_sorted = df_pending_processed.sort_values(by='Vencimento_Parsed', ascending=True)
                        df_pending_display = df_pending_sorted[['Descrição', 'Valor_Clean', 'Vencimento_Parsed', 'Categoria', 'Conta', 'Cartão']].copy()
                        df_pending_display.columns = ['Descrição', 'Valor (R$)', 'Vencimento', 'Categoria', 'Conta', 'Cartão']
                        
                        st.dataframe(
                            df_pending_display,
                            column_config={
                                "Descrição": st.column_config.TextColumn("Descrição", width="medium"),
                                "Valor (R$)": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", width="small"),
                                "Vencimento": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY", width="medium"),
                                "Categoria": st.column_config.TextColumn("Categoria", width="small"),
                                "Conta": st.column_config.TextColumn("Conta", width="small"),
                                "Cartão": st.column_config.TextColumn("Cartão", width="small")
                            },
                            use_container_width=True,
                            hide_index=True
                        )
                else:
                    st.success(f"🎉 Nenhuma conta pendente encontrada para este lote.")
            else:
                st.success(f"🎉 Parabéns! Nenhuma conta pendente encontrada para este lote.")

        # Split pending into Lote Dia 15 and Lote Dia 30 using Payday Lote Rules
        df_pending_15 = df_pending[df_pending['Lote_Tipo'] == 'Dia 15']
        df_pending_30 = df_pending[df_pending['Lote_Tipo'] == 'Dia 30']
        
        # Create Streamlit tabs
        tab15, tab30 = st.tabs(["💰 Lote Salário Dia 15", "💰 Lote Salário Dia 30"])
        
        with tab15:
            st.markdown("#### Lote de Contas - Salário do Dia 15")
            render_pending_table(df_pending_15, "Lote Salário Dia 15")
            
        with tab30:
            st.markdown("#### Lote de Contas - Salário do Dia 30")
            st.caption("ℹ️ *Nota: Este lote inclui as contas que vencem nos dias 29 a 31 do mês atual, bem como as contas de 1 a 14 do próximo mês que são provisionadas antecipadamente.*")
            render_pending_table(df_pending_30, "Lote Salário Dia 30")
            
        # -------------------------------------------------------------
        # EXPANDABLE TAB FOR ALL REGISTERED TRANSACTIONS
        # -------------------------------------------------------------
        with st.expander("🔍 Visualizar Todos os Registros (Base Completa)"):
            st.markdown("Aqui você pode verificar a planilha original completa com todas as contas:")
            
            # Format and display the entire table
            df_all_display = df_cleaned.copy()
            
            # Use appropriate color indicators for statuses
            st.dataframe(
                df_all_display[['Descrição', 'Valor_Clean', 'Vencimento_Parsed', 'Status', 'Efetivação', 'Categoria', 'Conta']],
                column_config={
                    "Descrição": "Descrição",
                    "Valor_Clean": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                    "Vencimento_Parsed": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
                    "Status": st.column_config.TextColumn("Status"),
                    "Efetivação": "Efetivação",
                    "Categoria": "Categoria",
                    "Conta": "Conta"
                },
                use_container_width=True,
                hide_index=True
            )
            
    except Exception as e:
        st.error(f"### 🛑 Erro ao processar os dados")
        st.markdown(f"""
            <div class="custom-card">
                <strong>Mensagem do Erro:</strong><br/>
                {str(e)}
            </div>
            <p>Verifique se o seu arquivo CSV segue exatamente a estrutura de colunas exigida: 
            <code>Descrição, Valor, Vencimento, Efetivação, Categoria, Conta</code></p>
        """, unsafe_allow_html=True)
else:
    st.info("👋 Aguardando carregamento de dados. Use a barra lateral esquerda para conectar ao Google Drive ou ver dados de demonstração.")
