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
        
        /* Adjust page top padding to prevent Streamlit's floating top bar from overlapping the title */
        .block-container {
            padding-top: 3.5rem !important;
            padding-bottom: 1.5rem !important;
        }
        
        /* Metric Card Container Styling (Compact Premium Dark Glassmorphism) */
        div[data-testid="stMetric"], .metric-card {
            background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 12px !important;
            padding: 12px 14px !important;
            box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease-in-out;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            min-height: 130px;
        }
        
        div[data-testid="stMetric"]:hover, .metric-card:hover {
            transform: translateY(-2px);
            border-color: rgba(59, 130, 246, 0.4) !important;
            box-shadow: 0 8px 30px 0 rgba(59, 130, 246, 0.15);
        }
        
        /* Compact typography for metric labels and values */
        div[data-testid="stMetricLabel"], .metric-card-label {
            font-size: 0.82rem !important;
            font-weight: 600 !important;
            color: #94A3B8 !important;
            margin-bottom: 4px;
        }
        
        div[data-testid="stMetricValue"], .metric-card-value {
            font-size: 1.4rem !important;
            font-weight: 700 !important;
            color: #F1F5F9 !important;
            margin-bottom: 6px;
            line-height: 1.2;
        }
        
        .metric-card-sub {
            font-size: 0.85rem !important;
            color: #94A3B8 !important;
            display: flex;
            flex-direction: column !important;
            gap: 4px;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            padding-top: 6px;
            margin-top: auto;
        }
        
        .metric-card-sub span {
            white-space: nowrap;
        }
        
        /* Header gradient styling (centered and compact) */
        .main-header {
            color: #FFFFFF;
            font-weight: 800;
            font-size: 1.6rem;
            text-align: center;
            margin-bottom: 0.5rem;
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
        
        /* Compact cards padding and font sizes on mobile */
        div[data-testid="stMetric"] {
            padding: 8px 8px !important;
            border-radius: 8px !important;
        }
        
        div[data-testid="stMetricLabel"] {
            font-size: 0.7rem !important;
            white-space: nowrap !important;
            text-overflow: ellipsis !important;
            overflow: hidden !important;
        }
        
        div[data-testid="stMetricValue"] {
            font-size: 0.95rem !important;
        }
        
        /* Compact header size for mobile cellular */
        .main-header {
            font-size: 1.35rem;
            margin-bottom: 0.3rem;
        }
        
        /* Mobile styles for custom metric cards */
        @media (max-width: 768px) {
            .metric-card {
                padding: 8px 8px !important;
                border-radius: 8px !important;
                min-height: 120px;
            }
            .metric-card-label {
                font-size: 0.7rem !important;
            }
            .metric-card-value {
                font-size: 0.95rem !important;
            }
            .metric-card-sub {
                font-size: 0.78rem !important;
                gap: 2px;
                padding-top: 4px;
            }
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
    
    # Rule 3: Convert 'Vencimento' to datetime robustly (format='mixed' and dayfirst=True ensures DD/MM/YYYY takes precedence)
    df['Vencimento_Parsed'] = pd.to_datetime(df['Vencimento'], format='mixed', dayfirst=True, errors='coerce')
    
    # Check for invalid dates in 'Vencimento'
    invalid_vencimento = df['Vencimento_Parsed'].isna() & df['Vencimento'].notna() & (df['Vencimento'].astype(str).str.strip() != '')
    if invalid_vencimento.any():
        st.sidebar.warning(
            f"Detectadas {invalid_vencimento.sum()} linhas com datas de Vencimento inválidas. "
            "Verifique se estão no formato brasileiro DD/MM/AAAA."
        )

    # Rules 1 & 2: Process payment status based on 'Efetivação'
    # "Pendente/A Pagar" if empty (NaN), contains '-', en-dash '–', em-dash '—' or is empty/nan
    efetivacao_clean = df['Efetivação'].astype(str).str.strip()
    is_pending = (
        df['Efetivação'].isna() | 
        (efetivacao_clean == '-') | 
        (efetivacao_clean == '–') | 
        (efetivacao_clean == '—') | 
        (efetivacao_clean == '') | 
        (efetivacao_clean.str.lower() == 'nan')
    )
    
    df['Status'] = np.where(is_pending, 'Pendente', 'Paga')
    
    # Convert 'Efetivação' to datetime for analytical metrics robustly if needed
    df['Efetivação_Parsed'] = pd.to_datetime(df['Efetivação'], format='mixed', dayfirst=True, errors='coerce')
    
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

DRIVE_EXPENSES_FILE_ID = "19-Q3oZQYA0KdAj81mSgPCZph9avgzH_2"
DRIVE_REVENUES_FILE_ID = "1KWzAuIoP0JuOgrROL8PGnsjnTj68JjrW"

df_raw_expenses = None
df_raw_revenues = None
error_encountered = False
error_details = ""

# Minimal collapsed sidebar with a simple status & refresh option
st.sidebar.markdown('<div class="sidebar-title">🔄 Operações</div>', unsafe_allow_html=True)
st.sidebar.info("Conectado automaticamente ao Google Drive.")
if st.sidebar.button("🔌 Sincronizar Agora", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# Run the real-time fetch on start directly from Google Drive
try:
    with st.spinner("Carregando suas finanças diretamente do Google Drive..."):
        df_raw_expenses = load_data_from_drive(CREDENTIALS_FILE, DRIVE_EXPENSES_FILE_ID)
        df_raw_revenues = load_data_from_drive(CREDENTIALS_FILE, DRIVE_REVENUES_FILE_ID)
except Exception as e:
    error_encountered = True
    error_details = str(e)


# =====================================================================
# 5. MAIN PAGE RENDERING
# =====================================================================

# Title Section
st.markdown('<div class="main-header">Controle financeiro</div>', unsafe_allow_html=True)

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
    

elif df_raw_expenses is not None and df_raw_revenues is not None:
    try:
        # Process and clean data using Pandas rules
        df_cleaned_expenses = process_financial_data(df_raw_expenses)
        df_cleaned_revenues = process_financial_data(df_raw_revenues)
        
        # Portuguese months dictionary
        MESES = {
            1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
            5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
            9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
        }
        
        # Extract unique Year-Months from 'Lote_Ano' and 'Lote_Mes'
        df_cleaned_expenses['Lote_Period'] = df_cleaned_expenses.apply(
            lambda r: pd.Period(year=int(r['Lote_Ano']), month=int(r['Lote_Mes']), freq='M')
            if pd.notna(r['Lote_Mes']) and pd.notna(r['Lote_Ano']) else pd.NaT,
            axis=1
        )
        df_cleaned_revenues['Lote_Period'] = df_cleaned_revenues.apply(
            lambda r: pd.Period(year=int(r['Lote_Ano']), month=int(r['Lote_Mes']), freq='M')
            if pd.notna(r['Lote_Mes']) and pd.notna(r['Lote_Ano']) else pd.NaT,
            axis=1
        )
        
        # Combine and sort all unique periods
        all_periods = set(df_cleaned_expenses['Lote_Period'].dropna().unique()) | set(df_cleaned_revenues['Lote_Period'].dropna().unique())
        unique_periods = sorted(list(all_periods))
        
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
            
        # Obter parâmetros da URL para seleção de período
        params = st.query_params
        if "mes" in params and "ano" in params:
            constructed_month = f"{params['mes']}/{params['ano']}"
            if constructed_month in period_options:
                st.session_state.selected_month = constructed_month
        elif 'selected_month' not in st.session_state:
            st.session_state.selected_month = period_options[default_index]
            
        if 'chart_offset' not in st.session_state:
            st.session_state.chart_offset = 0
            
        # Find current index
        try:
            current_index = period_options.index(st.session_state.selected_month)
        except ValueError:
            current_index = default_index
            st.session_state.selected_month = period_options[default_index]
            
        # Create available months list format: "📅 Mês / Ano"
        lista_meses = [f"📅 {p.split('/')[0]} / {p.split('/')[1]}" for p in period_options]
        indice_atual = current_index
        
        # Render a single clean, compact native dropdown selector occupying full width
        escolha = st.selectbox(
            label="Selecione o Mês de Referência",
            options=lista_meses,
            index=indice_atual,
            label_visibility="collapsed"
        )
        
        # Parse choice back to Mês/Ano format
        escolha_limpa = escolha.replace("📅 ", "").replace(" / ", "/")
        
        # If selection changed, update session state and query params, then rerun
        if escolha_limpa != st.session_state.selected_month:
            st.session_state.selected_month = escolha_limpa
            st.session_state.chart_offset = 0
            mes_sel, ano_sel = escolha_limpa.split('/')
            st.query_params["mes"] = mes_sel
            st.query_params["ano"] = ano_sel
            st.rerun()
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Parse selected month & year to filter the dataframe
        sel_month_name, sel_year_str = st.session_state.selected_month.split('/')
        sel_year = int(sel_year_str)
        sel_month_num = [k for k, v in MESES.items() if v == sel_month_name][0]
        
        # Filtered DataFrame for the monthly dashboard view (using Payday Lotes)
        df_filtered = df_cleaned_expenses[
            (df_cleaned_expenses['Lote_Mes'] == sel_month_num) &
            (df_cleaned_expenses['Lote_Ano'] == sel_year)
        ]
        
        df_filtered_revenues = df_cleaned_revenues[
            (df_cleaned_revenues['Lote_Mes'] == sel_month_num) &
            (df_cleaned_revenues['Lote_Ano'] == sel_year)
        ]
        
        # -------------------------------------------------------------
        # CALCULATE METRICS (using filtered monthly data)
        # -------------------------------------------------------------
        df_paid = df_filtered[df_filtered['Status'] == 'Paga']
        df_pending = df_filtered[df_filtered['Status'] == 'Pendente']
        
        total_pago = df_paid['Valor_Clean'].sum()
        total_pendente = df_pending['Valor_Clean'].sum()
        # Calculate grouped pending count (treating each unique credit card as 1 single bill)
        if not df_pending.empty:
            if 'Cartão' in df_pending.columns:
                df_pending_temp = df_pending.copy()
                df_pending_temp['Cartão'] = df_pending_temp['Cartão'].fillna('-').astype(str).str.strip()
                is_card = ~df_pending_temp['Cartão'].isin(['', '-', 'nan', 'None'])
                df_cards = df_pending_temp[is_card]
                df_no_cards = df_pending_temp[~is_card]
                qtd_pendentes = df_cards['Cartão'].nunique() + len(df_no_cards)
            else:
                qtd_pendentes = len(df_pending)
        else:
            qtd_pendentes = 0
        
        # -------------------------------------------------------------
        # METRIC CARDS (st.columns with Custom Premium HTML Cards)
        # -------------------------------------------------------------
        # Calculate sub-totals and sub-counts for pending lots (Dia 15 and Dia 30)
        df_pending_15 = df_pending[df_pending['Lote_Tipo'] == 'Dia 15']
        df_pending_30 = df_pending[df_pending['Lote_Tipo'] == 'Dia 30']
        
        total_pendente_15 = df_pending_15['Valor_Clean'].sum()
        total_pendente_30 = df_pending_30['Valor_Clean'].sum()
        
        def get_pending_count(df_sub_pending):
            if not df_sub_pending.empty:
                if 'Cartão' in df_sub_pending.columns:
                    df_temp = df_sub_pending.copy()
                    df_temp['Cartão'] = df_temp['Cartão'].fillna('-').astype(str).str.strip()
                    is_card = ~df_temp['Cartão'].isin(['', '-', 'nan', 'None'])
                    df_cards = df_temp[is_card]
                    df_no_cards = df_temp[~is_card]
                    return df_cards['Cartão'].nunique() + len(df_no_cards)
                else:
                    return len(df_sub_pending)
            return 0
            
        qtd_pendentes_15 = get_pending_count(df_pending_15)
        qtd_pendentes_30 = get_pending_count(df_pending_30)
        
        # Formatting values
        total_pendente_fmt = f"R$ {total_pendente:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        total_pendente_15_fmt = f"R$ {total_pendente_15:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        total_pendente_30_fmt = f"R$ {total_pendente_30:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        
        col1, col2 = st.columns(2, gap="medium")
        
        with col1:
            col1.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-card-label" title="Soma de todos os lançamentos com coluna Efetivação vazia ou contendo '-'.">🟡 Total Pendente (A Pagar)</div>
                    <div class="metric-card-value">{total_pendente_fmt}</div>
                    <div class="metric-card-sub">
                        <span>Dia 15: <strong>{total_pendente_15_fmt}</strong></span>
                        <span>Dia 30: <strong>{total_pendente_30_fmt}</strong></span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        with col2:
            contas_word = "conta" if qtd_pendentes == 1 else "contas"
            contas_word_15 = "item" if qtd_pendentes_15 == 1 else "itens"
            contas_word_30 = "item" if qtd_pendentes_30 == 1 else "itens"
            
            col2.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-card-label" title="Quantidade de contas pendentes (com faturas de cartão agrupadas de forma consolidada).">📅 Contas a Pagar</div>
                    <div class="metric-card-value">{qtd_pendentes} {contas_word}</div>
                    <div class="metric-card-sub">
                        <span>Dia 15: <strong>{qtd_pendentes_15} {contas_word_15}</strong></span>
                        <span>Dia 30: <strong>{qtd_pendentes_30} {contas_word_30}</strong></span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
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
                total_formatted = f"R$ {total_lote:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                
                # Display sum in a nice highlighted box
                st.markdown(
                    f"<div style='background-color: rgba(59, 130, 246, 0.05); padding: 12px 18px; border-radius: 12px; margin-bottom: 1.2rem; border: 1px solid rgba(59, 130, 246, 0.1);'>"
                    f"Total de despesas: <span style='font-size:1.3rem; font-weight:700; color: #3B82F6;'>{total_formatted}</span>"
                    f"</div>",
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
                    

                else:
                    st.success(f"🎉 Nenhuma conta pendente encontrada para este lote.")
            else:
                st.success(f"🎉 Parabéns! Nenhuma conta pendente encontrada para este lote.")

        # Split pending into Lote Dia 15 and Lote Dia 30 using Payday Lote Rules
        df_pending_15 = df_pending[df_pending['Lote_Tipo'] == 'Dia 15']
        df_pending_30 = df_pending[df_pending['Lote_Tipo'] == 'Dia 30']
        
        # Create Streamlit tabs
        tab15, tab30 = st.tabs(["💰 Vale (Dia 15)", "💰 Pagamento (Dia 30)"])
        
        with tab15:
            render_pending_table(df_pending_15, "Vale (Dia 15)")
            
        with tab30:
            render_pending_table(df_pending_30, "Pagamento (Dia 30)")
            
        st.markdown("<br/><br/>", unsafe_allow_html=True)
        
        # -------------------------------------------------------------
        # CHARTS VISUALIZATIONS SECTION (PREMIUM WOW FACTOR)
        # -------------------------------------------------------------
        st.markdown("### 📊 Visão Geral")
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
                    title="Despesas: Pago vs Pendente (R$)",
                    labels={'Valor_Clean': 'Valor (R$)'},
                    color_discrete_map={'Paga': '#10B981', 'Pendente': '#F59E0B'}
                )
                fig_bar.update_layout(
                    margin=dict(t=40, b=10, l=10, r=10),
                    height=300,
                    showlegend=False,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="Plus Jakarta Sans", size=12),
                    xaxis=dict(fixedrange=True),
                    yaxis=dict(fixedrange=True),
                    dragmode=False
                )
                st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Sem dados suficientes para exibir comparativo.")
                
        with chart_col2:
            # Lote Pending Totals (Plotly Bar Chart)
            lote_totals = pd.DataFrame([
                {'Lote': 'Vale (Dia 15)', 'Valor_Clean': df_pending[df_pending['Lote_Tipo'] == 'Dia 15']['Valor_Clean'].sum()},
                {'Lote': 'Pagamento (Dia 30)', 'Valor_Clean': df_pending[df_pending['Lote_Tipo'] == 'Dia 30']['Valor_Clean'].sum()}
            ])
            
            if lote_totals['Valor_Clean'].sum() > 0:
                fig_lote = px.bar(
                    lote_totals,
                    x='Lote',
                    y='Valor_Clean',
                    color='Lote',
                    title="Previsão de Saída: Vale vs Pagamento (R$)",
                    labels={'Valor_Clean': 'Valor Pendente (R$)', 'Lote': 'Período'},
                    color_discrete_map={'Vale (Dia 15)': '#3B82F6', 'Pagamento (Dia 30)': '#8B5CF6'}
                )
                fig_lote.update_layout(
                    margin=dict(t=40, b=10, l=10, r=10),
                    height=300,
                    showlegend=False,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="Plus Jakarta Sans", size=12),
                    xaxis=dict(fixedrange=True),
                    yaxis=dict(fixedrange=True),
                    dragmode=False
                )
                fig_lote.update_traces(
                    texttemplate='R$ %{y:,.2f}',
                    textposition='outside'
                )
                st.plotly_chart(fig_lote, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Nenhuma despesa pendente no mês para exibir a previsão por lote.")
                
        # -------------------------------------------------------------
        # FLOW OF LOTS SECTION: REVENUES VS EXPENSES (PREMIUM WOW FACTOR)
        # -------------------------------------------------------------
        st.markdown("<br/>", unsafe_allow_html=True)
        
        # Calculate start period using session state offset
        start_period = pd.Period(year=sel_year, month=sel_month_num, freq='M') + st.session_state.chart_offset
        projection_periods = [start_period + i for i in range(3)]
        
        # Format a dynamic title for the 3-month window
        m_start = MESES[projection_periods[0].month]
        y_start = projection_periods[0].year
        m_end = MESES[projection_periods[-1].month]
        y_end = projection_periods[-1].year
        chart_title = f"Previsão de Saldo Pendente: {m_start}/{y_start} a {m_end}/{y_end} (R$)"
        
        # Navigation header & buttons (Premium layout)
        col_hdr, col_btn = st.columns([3, 1])
        with col_hdr:
            st.markdown(f"### 📊 {chart_title}")
        with col_btn:
            btn_rec, btn_av = st.columns(2)
            with btn_rec:
                if st.button("⬅️ Recuar", key="btn_chart_rec", use_container_width=True):
                    st.session_state.chart_offset -= 1
                    st.rerun()
            with btn_av:
                if st.button("Avançar ➡️", key="btn_chart_av", use_container_width=True):
                    st.session_state.chart_offset += 1
                    st.rerun()
                    
        compare_rows = []
        for p in projection_periods:
            period_name = f"{MESES[p.month]}/{str(p.year)[2:]}" # e.g. "Maio/26" for a cleaner, compact axis
            
            # Filter revenues for this period
            df_rev_p = df_cleaned_revenues[
                (df_cleaned_revenues['Lote_Mes'] == p.month) &
                (df_cleaned_revenues['Lote_Ano'] == p.year)
            ]
            pending_rev = df_rev_p[df_rev_p['Status'] == 'Pendente']['Valor_Clean'].sum()
            
            # Filter expenses for this period
            df_exp_p = df_cleaned_expenses[
                (df_cleaned_expenses['Lote_Mes'] == p.month) &
                (df_cleaned_expenses['Lote_Ano'] == p.year)
            ]
            pending_exp = df_exp_p[df_exp_p['Status'] == 'Pendente']['Valor_Clean'].sum()
            
            compare_rows.append({"Mês": period_name, "Tipo": "Receitas Pendentes", "Valor": pending_rev})
            compare_rows.append({"Mês": period_name, "Tipo": "Despesas Pendentes", "Valor": pending_exp})
            
        compare_data = pd.DataFrame(compare_rows)
        
        if compare_data["Valor"].sum() > 0:
            fig_compare = px.bar(
                compare_data,
                x="Mês",
                y="Valor",
                color="Tipo",
                barmode="group",
                title=None,
                labels={"Valor": "Total Pendente (R$)", "Mês": "Mês de Referência"},
                color_discrete_map={"Receitas Pendentes": "#10B981", "Despesas Pendentes": "#F59E0B"}
            )
            fig_compare.update_layout(
                margin=dict(t=15, b=10, l=10, r=10),
                height=350,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Plus Jakarta Sans", size=12),
                xaxis=dict(fixedrange=True),
                yaxis=dict(fixedrange=True),
                dragmode=False,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            fig_compare.update_traces(
                texttemplate='R$ %{y:,.2f}',
                textposition='outside'
            )
            st.plotly_chart(fig_compare, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Sem dados suficientes de despesas ou receitas pendentes para exibir o fluxo neste período.")
            
        # -------------------------------------------------------------
        # DIAGNOSTIC PANEL (DEBUG EXPANDER)
        # -------------------------------------------------------------
        st.markdown("<br/>", unsafe_allow_html=True)
        with st.expander("🔍 Painel de Diagnóstico (Debug)"):
            st.write(f"**Total de linhas carregadas do arquivo de Despesas:** {len(df_cleaned_expenses)}")
            if 'Cartão' in df_cleaned_expenses.columns:
                unique_cards = df_cleaned_expenses['Cartão'].unique().tolist()
                st.write(f"**Cartões detectados no arquivo:** {unique_cards}")
                
                # Filter for BB card rows in the raw cleaned dataset
                df_bb_raw = df_cleaned_expenses[df_cleaned_expenses['Cartão'].astype(str).str.contains('BB', na=False, case=False)]
                st.write(f"**Total de linhas cruas do cartão 'BB' no arquivo:** {len(df_bb_raw)}")
                st.dataframe(df_bb_raw[['Descrição', 'Valor', 'Vencimento', 'Efetivação', 'Lote_Tipo', 'Lote_Mes', 'Lote_Ano']])
            else:
                st.warning("Coluna 'Cartão' não encontrada nas despesas cruas.")
            

            
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
