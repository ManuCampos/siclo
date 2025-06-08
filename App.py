import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import io
import re
import requests

# Configuração da página
st.set_page_config(
    page_title="Projeto Predição de Editais - CIC2025",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para interface profissional
st.markdown("""
<style>
    /* Tema principal */
    .main-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-weight: 600;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #3b82f6;
        margin: 0.5rem 0;
    }
    
    .filter-section {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .alert-info {
        background: #dbeafe;
        border: 1px solid #3b82f6;
        color: #1e40af;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .alert-success {
        background: #dcfce7;
        border: 1px solid #16a34a;
        color: #15803d;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .alert-warning {
        background: #fef3c7;
        border: 1px solid #f59e0b;
        color: #92400e;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .sidebar .sidebar-content {
        background: #f1f5f9;
    }
    
    /* Estilo para métricas */
    .metric-container {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        margin: 1rem 0;
    }
    
    /* Botões personalizados */
    .stButton > button {
        background: linear-gradient(90deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
    }
    
    /* Estilo para selectbox */
    .stSelectbox > div > div {
        border-radius: 8px;
    }
    
    /* Tabelas */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Loading spinner personalizado */
    .loading-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 2rem;
    }
    
    /* Botão de exportação customizado */
    .export-button-container {
        display: flex;
        justify-content: flex-end;
        margin: 1rem 0;
        padding: 0.5rem;
    }
    
    /* Seção de filtros avançados */
    .advanced-search {
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# URL do SharePoint (pode precisar de autenticação)
SHAREPOINT_URL = "https://tcerj365-my.sharepoint.com/:x:/g/personal/emanuellipc_tcerj_tc_br/EXQxKC-8-uNLu-RCyhK6sjwB4pljoEYgoup6g-mJ5iHlwA?e=DDbJpE"
# Tentativa de conversão para download direto
SHAREPOINT_CSV_URL = "https://tcerj365-my.sharepoint.com/:x:/g/personal/emanuellipc_tcerj_tc_br/EXQxKC-8-uNLu-RCyhK6sjwB4pljoEYgoup6g-mJ5iHlwA?e=DDbJpE&download=1"

@st.cache_data(ttl=300)  # Cache por 5 minutos
def load_data_from_sharepoint():
    """Carrega dados diretamente do SharePoint"""
    try:
        # Primeira tentativa - URL com download=1
        try:
            response = requests.get(SHAREPOINT_CSV_URL, timeout=30)
            response.raise_for_status()
        except:
            # Segunda tentativa - URL original
            response = requests.get(SHAREPOINT_URL, timeout=30)
            response.raise_for_status()
        
        # Primeiro, tenta o método padrão mais robusto
        try:
            df = pd.read_csv(
                io.StringIO(response.text),
                encoding='utf-8',
                sep=',',
                quotechar='"',
                escapechar='\\',
                on_bad_lines='skip',  # Pula linhas problemáticas
                engine='python',  # Engine mais tolerante
                dtype=str,  # Carrega tudo como string primeiro
                low_memory=False
            )
        except Exception as e1:
            # Método alternativo - tenta com delimitador automático
            try:
                df = pd.read_csv(
                    io.StringIO(response.text),
                    sep=None,  # Detecta automaticamente o delimitador
                    engine='python',
                    encoding='utf-8',
                    on_bad_lines='skip',
                    dtype=str
                )
            except Exception as e2:
                # Último recurso - verifica se é HTML (página de login)
                if "<html" in response.text.lower() or "sign in" in response.text.lower():
                    return None, "SharePoint requer autenticação - use upload manual ou configure permissões públicas"
                
                return None, f"Erro de parsing: {str(e1)}. Tentativa alternativa: {str(e2)}"
        
        # Remove linhas completamente vazias
        df = df.dropna(how='all')
        
        # Remove colunas que são completamente vazias ou têm nomes inválidos
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df = df.dropna(axis=1, how='all')
        
        # Conversões de tipos mais seguras
        if 'data realizacao licitacao' in df.columns:
            df['data realizacao licitacao'] = pd.to_datetime(df['data realizacao licitacao'], errors='coerce')
        
        if 'ano' in df.columns:
            df['ano'] = pd.to_numeric(df['ano'], errors='coerce')
        
        if 'Valor Estimado' in df.columns:
            # Remove caracteres não numéricos exceto pontos e vírgulas
            df['Valor Estimado'] = df['Valor Estimado'].astype(str).str.replace(r'[^\d.,]', '', regex=True)
            df['Valor Estimado'] = df['Valor Estimado'].str.replace(',', '.', regex=False)
            df['Valor Estimado'] = pd.to_numeric(df['Valor Estimado'], errors='coerce')
        
        if 'pontuacao' in df.columns:
            df['pontuacao'] = df['pontuacao'].astype(str).str.replace(',', '.', regex=False)
            df['pontuacao'] = pd.to_numeric(df['pontuacao'], errors='coerce')
            
        if 'pontuacao_final' in df.columns:
            df['pontuacao_final'] = df['pontuacao_final'].astype(str).str.replace(',', '.', regex=False)
            df['pontuacao_final'] = pd.to_numeric(df['pontuacao_final'], errors='coerce')
        
        # Processamento da coluna observacoes - preenche valores em branco
        if 'observacoes' in df.columns:
            df['observacoes'] = df['observacoes'].apply(
                lambda x: x if pd.notna(x) and str(x).strip() != '' else 'Classificação baseada em Termos Chave'
            )
        
        # Renomeação de colunas específicas
        column_renames = {
            'Nova Classificação': 'Nova Predição',
            'observacoes': 'Observações'
        }
        
        for old_name, new_name in column_renames.items():
            if old_name in df.columns:
                df = df.rename(columns={old_name: new_name})
        
        # Remoção de duplicatas ignorando a coluna 'classificacao_final'
        columns_for_dedup = [col for col in df.columns if col != 'classificacao_final']
        if columns_for_dedup:
            df = df.drop_duplicates(subset=columns_for_dedup, keep='first')
        
        # Processamento da coluna observacoes - preenche valores em branco
        if 'observacoes' in df.columns:
            df['observacoes'] = df['observacoes'].apply(
                lambda x: x if pd.notna(x) and str(x).strip() != '' else 'Classificação baseada em Termos Chave'
            )
        
        # Validação final - se o dataframe está vazio ou muito pequeno
        if len(df) == 0:
            return None, "Nenhum dado válido encontrado na planilha"
        
        if len(df.columns) < 5:
            return None, "Estrutura de dados incompleta - muito poucas colunas"
            
        return df, None
        
    except requests.exceptions.RequestException as e:
        if "403" in str(e) or "401" in str(e):
            return None, "Acesso negado - SharePoint requer permissões ou autenticação"
        return None, f"Erro de conexão: {str(e)}"
    except pd.errors.EmptyDataError:
        return None, "Planilha está vazia ou não contém dados válidos"
    except pd.errors.ParserError as e:
        return None, f"Erro de formatação dos dados: {str(e)}"
    except Exception as e:
        return None, f"Erro inesperado: {str(e)}"

def extract_unique_categories(df, column_name):
    """Extrai categorias únicas de uma coluna multi-label (separadas por ; ou ,)"""
    if column_name not in df.columns:
        return []
    
    unique_categories = set()
    for value in df[column_name].dropna():
        if pd.isna(value):
            continue
        
        value_str = str(value).strip()
        if not value_str:
            continue
            
        # Separadores possíveis: ; ou ,
        if ';' in value_str:
            categories = [cat.strip() for cat in value_str.split(';') if cat.strip()]
        elif ',' in value_str:
            categories = [cat.strip() for cat in value_str.split(',') if cat.strip()]
        else:
            categories = [value_str]
        
        unique_categories.update(categories)
    
    # Remover valores vazios e limitar a 14 categorias
    unique_categories = [cat for cat in unique_categories if cat and cat != 'nan']
    return sorted(list(unique_categories))[:14]

def create_overview_metrics(df):
    """Cria métricas de visão geral com dados fixos da base completa"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📋 Total de Editais",
            value="52.429",
            delta=None
        )
    
    with col2:
        st.metric(
            label="💰 Valor Total Estimado",
            value="R$ 244 Bilhões",
            delta=None
        )
    
    with col3:
        st.metric(
            label="🏷️ Categorias Únicas",
            value="14",
            delta=None
        )
    
    with col4:
        st.metric(
            label="🏢 Unidades Únicas",
            value="729",
            delta=None
        )

def apply_advanced_search(df, search_params):
    """Aplica busca avançada com operadores lógicos - versão aprimorada"""
    if not search_params or not any(search_params.values()):
        return df
    
    search_columns = ['objeto', 'unidade', 'observacoes', 'todos_termos', 'descricao situacao edital', 'objeto_processada']
    search_columns = [col for col in search_columns if col in df.columns]
    
    if not search_columns:
        return df
    
    # CORREÇÃO: Reset do índice para evitar problemas com filtros sucessivos
    df_search = df.reset_index(drop=True)
    
    # Inicializa máscara como True (todos os registros)
    final_mask = pd.Series(True, index=df_search.index)
    
    # Termos que deve conter (AND)
    if search_params.get('contains_and'):
        search_text = search_params['contains_and'].strip()
        
        if ';' in search_text:
            # Se tem ponto e vírgula, cada termo é independente (TODOS devem estar presentes)
            terms = [term.strip().lower() for term in search_text.split(';') if term.strip()]
            for term in terms:
                term_mask = pd.Series(False, index=df_search.index)
                for col in search_columns:
                    term_mask |= df_search[col].fillna('').astype(str).str.lower().str.contains(term, na=False, regex=False)
                final_mask &= term_mask
        else:
            # Se não tem ponto e vírgula, trata como frase única
            search_phrase = search_text.lower()
            phrase_mask = pd.Series(False, index=df_search.index)
            for col in search_columns:
                phrase_mask |= df_search[col].fillna('').astype(str).str.lower().str.contains(search_phrase, na=False, regex=False)
            final_mask &= phrase_mask
    
    # Termos que deve conter (OR)
    if search_params.get('contains_or'):
        search_text = search_params['contains_or'].strip()
        
        if ';' in search_text:
            # Se tem ponto e vírgula, cada termo é independente (QUALQUER um pode estar presente)
            terms = [term.strip().lower() for term in search_text.split(';') if term.strip()]
            if terms:
                or_mask = pd.Series(False, index=df_search.index)
                for term in terms:
                    term_mask = pd.Series(False, index=df_search.index)
                    for col in search_columns:
                        term_mask |= df_search[col].fillna('').astype(str).str.lower().str.contains(term, na=False, regex=False)
                    or_mask |= term_mask
                final_mask &= or_mask
        else:
            # Se não tem ponto e vírgula, trata como frase única
            search_phrase = search_text.lower()
            phrase_mask = pd.Series(False, index=df_search.index)
            for col in search_columns:
                phrase_mask |= df_search[col].fillna('').astype(str).str.lower().str.contains(search_phrase, na=False, regex=False)
            final_mask &= phrase_mask
    
    # Termos que NÃO deve conter
    if search_params.get('not_contains'):
        search_text = search_params['not_contains'].strip()
        
        if ';' in search_text:
            # Se tem ponto e vírgula, cada termo é independente
            terms = [term.strip().lower() for term in search_text.split(';') if term.strip()]
            for term in terms:
                term_mask = pd.Series(False, index=df_search.index)
                for col in search_columns:
                    term_mask |= df_search[col].fillna('').astype(str).str.lower().str.contains(term, na=False, regex=False)
                final_mask &= ~term_mask
        else:
            # Se não tem ponto e vírgula, trata como frase única
            search_phrase = search_text.lower()
            phrase_mask = pd.Series(False, index=df_search.index)
            for col in search_columns:
                phrase_mask |= df_search[col].fillna('').astype(str).str.lower().str.contains(search_phrase, na=False, regex=False)
            final_mask &= ~phrase_mask
    
    # CORREÇÃO: Retornar o DataFrame original com os índices filtrados
    filtered_indices = df_search.index[final_mask]
    return df.iloc[filtered_indices].reset_index(drop=True)

def apply_nova_predicao_filter(df, selected_category):
    """Aplica filtro de containment para Nova Predição"""
    if selected_category == 'Todas' or 'Nova Predição' not in df.columns:
        return df
    
    # Reset do índice para trabalhar com dados limpos
    df_clean = df.reset_index(drop=True)
    
    # Máscara para filtrar registros que CONTÊM a categoria selecionada
    mask = pd.Series(False, index=df_clean.index)
    
    for idx, value in df_clean['Nova Predição'].items():
        if pd.isna(value):
            continue
            
        value_str = str(value).strip().upper()
        selected_cat_upper = selected_category.upper()
        
        if not value_str:
            continue
        
        # Verifica se contém a categoria (busca parcial/containment)
        if selected_cat_upper in value_str:
            mask.iloc[idx] = True
    
    return df_clean[mask].reset_index(drop=True)

def apply_filters(df, search_params, filters):
    """Aplica os filtros ao dataframe com tratamento melhorado de erros - VERSÃO CORRIGIDA"""
    # CORREÇÃO: Sempre começar com uma cópia limpa dos dados originais
    filtered_df = df.copy().reset_index(drop=True)
    
    # Aplicar busca avançada primeiro (trabalha com dados limpos)
    filtered_df = apply_advanced_search(filtered_df, search_params)
    
    # Aplicar filtros específicos sequencialmente
    for column, value in filters.items():
        if value not in ['Todas', 'Todos']:
            # Filtro especial para Nova Predição - busca por containment
            if column == 'Nova Predição':
                filtered_df = apply_nova_predicao_filter(filtered_df, value)
            else:
                # Filtro exato para outras colunas
                filtered_df = filtered_df[
                    filtered_df[column].fillna('').astype(str) == str(value)
                ]
                filtered_df = filtered_df.reset_index(drop=True)
    
    return filtered_df

def create_charts(df):
    """Cria gráficos de análise"""
    col1, col2 = st.columns(2)
    
    with col1:
        if 'unidade' in df.columns and len(df) > 0:
            # Gráfico de quantidade de editais por coordenadoria
            unidade_counts = df['unidade'].value_counts().head(10)
            
            if len(unidade_counts) > 0:
                fig_bar = px.bar(
                    x=unidade_counts.values,
                    y=unidade_counts.index,
                    orientation='h',
                    title="📊 Quantidade de Editais por Coordenadoria",
                    labels={'x': 'Quantidade', 'y': 'Coordenadoria'},
                    color=unidade_counts.values,
                    color_continuous_scale='Blues'
                )
                fig_bar.update_layout(
                    height=400,
                    showlegend=False,
                    yaxis={'categoryorder': 'total ascending'}
                )
                st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        if 'unidade' in df.columns and 'Valor Estimado' in df.columns and len(df) > 0:
            # Gráfico das maiores coordenadorias por Valor Estimado
            unidade_valores = df.groupby('unidade')['Valor Estimado'].sum().sort_values(ascending=False).head(8)
            
            if len(unidade_valores) > 0:
                fig_pie = px.pie(
                    values=unidade_valores.values,
                    names=unidade_valores.index,
                    title="💰 Maiores Coordenadorias por Valor Estimado"
                )
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
    
    # Gráfico temporal se houver dados de data
    if 'ano' in df.columns and len(df) > 0:
        st.markdown("### 📈 Evolução Temporal")
        temporal_data = df['ano'].value_counts().sort_index()
        
        if len(temporal_data) > 0:
            fig_line = px.line(
                x=temporal_data.index,
                y=temporal_data.values,
                title="Editais por Ano",
                labels={'x': 'Ano', 'y': 'Quantidade de Editais'},
                markers=True
            )
            fig_line.update_layout(height=400)
            st.plotly_chart(fig_line, use_container_width=True)

def create_export_button(df, columns_to_show):
    """Cria botão de exportação automática"""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col3:  # Posiciona no lado direito
        export_format = st.selectbox(
            "Formato:",
            ["CSV", "XLSX"],
            key="export_format"
        )
        
        if st.button("📥 Exportar Filtrados", type="primary"):
            export_data = df[columns_to_show] if columns_to_show else df
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if export_format == "CSV":
                csv_data = export_data.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name=f"editais_filtrados_{timestamp}.csv",
                    mime="text/csv",
                    type="primary"
                )
                st.success("✅ Arquivo CSV preparado para download!")
                
            else:  # XLSX
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    export_data.to_excel(writer, index=False, sheet_name='Editais_Filtrados')
                
                st.download_button(
                    label="📥 Download XLSX",
                    data=output.getvalue(),
                    file_name=f"editais_filtrados_{timestamp}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )
                st.success("✅ Arquivo XLSX preparado para download!")

def display_data_table(df):
    """Exibe a tabela de dados com opções de visualização"""
    st.markdown("### 📋 Dados dos Editais")
    
    # Definir colunas padrão na ordem especificada
    default_columns = [
        'Nova Predição',
        'Predição Antiga',
        'Ano',
        'Mês',
        'Ente',
        'Unidade',
        'Objeto',
        'Valor Estimado',
        'observacoes'
    ]
    
    # Filtrar apenas as colunas que existem no DataFrame
    default_columns = [col for col in default_columns if col in df.columns]
    
    # Obter todas as colunas do DataFrame
    all_columns = list(df.columns)
    
    # Opções de visualização
    col1, col2 = st.columns([3, 1])
    
    with col1:
        columns_to_show = st.multiselect(
            "📊 Selecionar colunas para exibir",
            options=all_columns,
            default=default_columns,
            help="Selecione as colunas que deseja visualizar"
        )
    
    with col2:
        rows_per_page = st.selectbox(
            "📄 Linhas por página",
            [10, 25, 50, 100],
            index=1
        )
    
    # Flag para mostrar apenas alterações de classificação
    show_only_changes = st.checkbox(
        "📊 Exibir apenas editais com classificações alteradas",
        help="Mostra apenas editais onde Nova Predição ≠ Predição Antiga"
    )
    
    # Aplicar filtro de alterações se solicitado
    display_df = df.copy()
    if show_only_changes and 'Nova Predição' in df.columns and 'Predição Antiga' in df.columns:
        display_df = df[df['Nova Predição'].fillna('') != df['Predição Antiga'].fillna('')]
        if len(display_df) == 0:
            st.warning("⚠️ Nenhum edital com classificação alterada encontrado nos dados filtrados.")
            return
        else:
            st.info(f"📋 Mostrando {len(display_df):,} editais com classificações alteradas de {len(df):,} totais ({(len(display_df)/len(df)*100):.1f}%)")
    
    if columns_to_show and len(display_df) > 0:
        # Paginação
        total_rows = len(display_df)
        total_pages = (total_rows - 1) // rows_per_page + 1
        
        if total_pages > 1:
            page = st.number_input(
                f"Página (1 de {total_pages})",
                min_value=1,
                max_value=total_pages,
                value=1
            ) - 1
        else:
            page = 0
        
        start_idx = page * rows_per_page
        end_idx = start_idx + rows_per_page
        
        # Exibir dados
        page_df = display_df[columns_to_show].iloc[start_idx:end_idx].copy()
        
        # Formatação condicional para valores monetários
        if 'Valor Estimado' in page_df.columns:
            page_df['Valor Estimado'] = page_df['Valor Estimado'].apply(
                lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if pd.notna(x) else 'N/A'
            )
        
        # Formatação para pontuações
        for col in ['pontuacao', 'pontuacao_final']:
            if col in page_df.columns:
                page_df[col] = page_df[col].apply(
                    lambda x: f"{x:.2f}" if pd.notna(x) else 'N/A'
                )
        
        # Preenchimento automático para observações em branco
        if 'Observações' in page_df.columns:
            page_df['Observações'] = page_df['Observações'].apply(
                lambda x: x if pd.notna(x) and str(x).strip() != '' else 'Classificação baseada em Termos Chave'
            )
        
        st.dataframe(
            page_df,
            use_container_width=True,
            height=400
        )
        
        # Informações da paginação
        st.info(f"Exibindo {start_idx + 1}-{min(end_idx, total_rows)} de {total_rows} registros")
        
        # Botão de exportação reposicionado (lado inferior direito)
        create_export_button(display_df, columns_to_show)

def show_help_tab():
    """Mostra a aba de ajuda e instruções"""
    st.markdown("""
    # 📚 Como Usar o Projeto Predição de Editais - CIC2025
    
    ## 🚀 Início Rápido
    
    ### 1. Escopo da Base de Dados
    - **52.429 editais** analisados e classificados
    - **R$ 244 bilhões** em valor total estimado
    - **729 coordenadorias/unidades** organizacionais mapeadas
    - **14 categorias originais** + **2 novas categorias** criadas
    - Sistema carrega amostras para consulta interativa
    
    ### 2. Dados Automáticos
    - Os dados são carregados automaticamente do SharePoint TCERJ
    - Sistema atualiza a cada 5 minutos para manter dados frescos
    - Não é necessário fazer upload manual (se configurado corretamente)
    
    ### 3. Navegação
    O sistema possui **3 abas principais**:
    - **📊 Análise de Dados**: Visualização principal com filtros e tabelas
    - **📈 Dashboard**: Gráficos e estatísticas detalhadas
    - **📚 Ajuda**: Esta seção com instruções
    
    ## 🔍 Funcionalidades de Pesquisa Avançada
    
    ### Busca Avançada com Operadores Lógicos
    A seção "🔍 Busca Avançada" permite diferentes tipos de filtros com **duas modalidades de busca**:
    
    #### 🔤 **Modalidades de Busca:**
    
    **1. Busca por Frase Completa (SEM ponto e vírgula)**
    - Digite termos **sem ponto e vírgula (;)** para buscar a frase exata
    - **Exemplo**: "bens permanentes" → encontra registros que contenham exatamente esta sequência
    - **Exemplo**: "material de escritório" → busca esta frase completa
    - **Uso**: Ideal para termos compostos que devem aparecer juntos
    
    **2. Busca por Termos Separados (COM ponto e vírgula)**
    - Use **ponto e vírgula (;)** para separar termos que podem aparecer em qualquer lugar
    - **Exemplo**: "bens; permanentes" → encontra registros que contenham "bens" E "permanentes" separadamente
    - **Exemplo**: "material; escritório" → busca por ambos os termos em qualquer posição
    - **Uso**: Ideal para buscar conceitos relacionados que podem estar em partes diferentes do texto
    
    #### 📝 **Tipos de Filtros:**
    
    #### 1. **Contém TODOS os termos (E)**
    - **Frase**: "educação infantil" → registros com esta frase exata
    - **Termos**: "educação; construção" → registros que contenham **tanto** "educação" **quanto** "construção"
    - **Uso prático**: Encontrar editais que atendam múltiplos critérios simultaneamente
    
    #### 2. **Contém ALGUM termo (OU)**
    - **Frase**: "centro de saúde" → registros com esta frase específica
    - **Termos**: "hospital; posto; upa" → registros com **qualquer um** desses termos
    - **Uso prático**: Buscar variações de um mesmo conceito
    
    #### 3. **NÃO contém (Filtro Negativo)**
    - **Frase**: "serviços terceirizados" → exclui registros com esta frase exata
    - **Termos**: "consultoria; terceirizado" → exclui registros com qualquer um desses termos
    - **Uso prático**: Refinar resultados removendo categorias indesejadas
    
    ## 📂 Filtro "Nova Predição" com Busca por Containment
    
    ### Funcionalidade Especial para Categorias
    O filtro "📂 Nova Predição" utiliza **busca por containment** (contém):
    
    #### Como Funciona
    - **Busca Parcial**: Não precisa coincidir exatamente - funciona com ocorrências parciais
    - **Categoria Única**: Se um edital tem apenas "EDUCAÇÃO", será encontrado ao selecionar "EDUCAÇÃO"
    - **Categorias Múltiplas**: Se um edital tem "EDUCAÇÃO; SAÚDE", será encontrado ao selecionar **qualquer uma** das categorias
    - **Aplicação Sequencial**: Os filtros são aplicados um após o outro, mantendo a consistência
    
    #### Exemplos Práticos
    - **Selecionando "EDUCAÇÃO"** encontra:
      - ✅ Editais com classificação: "EDUCAÇÃO"
      - ✅ Editais com classificação: "EDUCAÇÃO; SAÚDE"
      - ✅ Editais com classificação: "INFRAESTRUTURA; EDUCAÇÃO; TRANSPORTE"
    
    ## 🔄 Sistema de Filtros Corrigido
    
    ### Aplicação Sequencial
    - **Múltiplas aplicações**: Os filtros agora podem ser aplicados múltiplas vezes
    - **Ordem de aplicação**: Busca avançada primeiro, depois filtros específicos
    - **Consistência**: Cada filtro mantém o estado anterior
    - **Reset de índices**: Cada etapa reseta os índices para evitar erros
    
    ### Filtros Disponíveis
    1. **Nova Predição**: Busca por containment (contém)
    2. **Predição Antiga**: Busca exata
    3. **Ano**: Busca exata
    4. **Unidade**: Busca exata
    
    ## 📥 Sistema de Exportação Aprimorado
    
    ### Localização e Funcionalidade
    - **Posicionamento**: Botão azul no **lado inferior direito** da tabela
    - **Exportação Automática**: Clique único inicia o download automaticamente
    - **Sem Confirmações**: Processo otimizado sem etapas extras
    
    ### Opções de Formato
    - **CSV**: Formato universal para análise em Excel, Python, R
    - **XLSX**: Formato Excel nativo com formatação preservada
    
    ### Dados Exportados
    - **Apenas dados filtrados** são exportados (respeita todos os filtros aplicados)
    - **Colunas selecionadas** na interface são mantidas na exportação
    - **Formatação preservada** para valores monetários e datas
    - **Nome automático** com timestamp: `editais_filtrados_YYYYMMDD_HHMMSS`
    
    ## 💡 Dicas de Uso Avançado
    
    ### Para Gestores CIC
    1. **Análise Comparativa**: Use filtros de containment para categorias complexas
    2. **Busca Estratégica**: Combine operadores E/OU para análises precisas
    3. **Exportação Seletiva**: Filtre dados específicos antes de exportar
    4. **Monitoramento**: Use filtros negativos para excluir categorias não relevantes
    
    ### Para Analistas
    1. **Pesquisa Complexa**: Combine múltiplos operadores para análises detalhadas
    2. **Validação de Dados**: Use exportação para validação externa
    3. **Análise Temporal**: Combine filtros de ano com categorias específicas
    4. **Comparação Metodológica**: Explore divergências entre predições
    
    ### Fluxo de Trabalho Recomendado
    1. **Definir Objetivo**: O que você quer analisar?
    2. **Aplicar Filtros Básicos**: Unidade, ano, modalidade
    3. **Refinar com Busca Avançada**: Use operadores lógicos
    4. **Aplicar Filtro de Predição**: Use containment para categorias
    5. **Validar Resultados**: Verifique se os dados fazem sentido
    6. **Exportar para Análise**: Use formato apropriado (CSV/XLSX)
    
    ## 🔧 Solução de Problemas
    
    ### Busca Avançada
    - **Sem resultados**: Verifique se os operadores estão corretos
    - **Muitos resultados**: Use filtros negativos para refinar
    - **Termos não encontrados**: Verifique ortografia e use sinônimos
    
    ### Filtros de Predição
    - **Categoria não aparece**: Verificar se existe na base de dados
    - **Resultados inesperados**: Lembrar que busca é por containment (contém)
    - **Filtros não aplicam**: Verificar se há dados para filtrar
    
    ### Exportação
    - **Download não inicia**: Aguardar processamento e tentar novamente
    - **Arquivo muito grande**: Aplicar mais filtros para reduzir volume
    - **Problemas de formatação**: Preferir XLSX para manter formatação
    
    ---
    
    > 💼 **Projeto Predição de Editais - CIC2025 | TCERJ**  
    > **🔍 Novidades:** Busca Avançada | Filtros Containment | Aplicação Sequencial  
    > Coordenadoria de Informações Estratégicas
    """)

def main():
    """Função principal da aplicação"""
    
    # Header principal
    st.markdown("""
    <div class="main-header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1>📊 Projeto Predição de Editais - CIC2025</h1>
                <p style="color: #e2e8f0; margin: 0.5rem 0 0 0;">
                    Ferramenta de Consulta de Editais - Versão Avançada (Corrigida)
                </p>
            </div>
            <div style="margin-left: 2rem;">
                <img src="https://tcerj365-my.sharepoint.com/:i:/g/personal/emanuellipc_tcerj_tc_br/EU_4T9vkz1BEmtF4qGFPdekB71dUQ1f_isaIoampssa5WQ?e=33qdcT" 
                     alt="CIC TCERJ Logo" 
                     style="height: 80px; width: auto; max-width: 150px; object-fit: contain;"
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                <!-- Fallback caso a imagem não carregue -->
                <div style="width: 120px; height: 80px; background: rgba(255,255,255,0.1); border-radius: 8px; display: none; align-items: center; justify-content: center; color: white; font-size: 0.8rem;">
                    LOGO<br>CIC TCERJ
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Estatísticas gerais da base completa
    st.markdown("""
    <div class="alert-info">
        <h4>📈 Escopo da Base de Dados Completa</h4>
        <div style="display: flex; justify-content: space-around; text-align: center; margin: 1rem 0;">
            <div>
                <strong style="font-size: 1.5rem; color: #1e40af;">52.429</strong><br>
                <span style="color: #64748b;">Editais Analisados</span>
            </div>
            <div>
                <strong style="font-size: 1.5rem; color: #1e40af;">R$ 244 Bilhões</strong><br>
                <span style="color: #64748b;">Valor Total Estimado</span>
            </div>
            <div>
                <strong style="font-size: 1.5rem; color: #1e40af;">729</strong><br>
                <span style="color: #64748b;">Unidades Mapeadas</span>
            </div>
            <div>
                <strong style="font-size: 1.5rem; color: #1e40af;">14</strong><br>
                <span style="color: #64748b;">Categorias</span>
            </div>
            <div>
                <strong style="font-size: 1.5rem; color: #1e40af;">2</strong><br>
                <span style="color: #64748b;">Novas Categorias</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Carregamento dos dados do SharePoint
    with st.spinner("🔄 Carregando dados do SharePoint TCERJ..."):
        df, error = load_data_from_sharepoint()
        
        # Add reload button
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🔄 Recarregar Dados"):
                st.cache_data.clear()
                st.rerun()
        
        with col2:
            st.markdown("*Atualização automática a cada 5min*")

    # Show connection status in sidebar
    st.sidebar.markdown("### 🔗 Status da Conexão")
    st.sidebar.markdown(f"**URL da Planilha:** [Link TCERJ]({SHAREPOINT_URL})")

    # Se houve erro, mostrar diagnóstico
    if error:
        st.error(f"❌ {error}")
        
        # Instruções específicas baseadas no tipo de erro
        if "conexão" in error.lower() or "timeout" in error.lower():
            st.markdown("""
            <div class="alert-warning">
                <h4>🌐 Problema de Conectividade</h4>
                <p><strong>Soluções alternativas:</strong></p>
                <ul>
                    <li>Mude para "📄 Upload de Arquivo CSV" acima</li>
                    <li>Baixe a planilha como CSV e faça upload manual</li>
                    <li>Verifique sua conexão com a internet</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
        elif "permission" in error.lower() or "403" in error.lower() or "autenticação" in error.lower():
            st.markdown("""
            <div class="alert-warning">
                <h4>🔒 Problema de Permissão do SharePoint TCERJ</h4>
                <p><strong>O SharePoint corporativo requer configurações especiais:</strong></p>
                <h5>Opção 1: Configurar Acesso Público (Recomendado)</h5>
                <ol>
                    <li>Abra a planilha no SharePoint</li>
                    <li>Clique em "Compartilhar" no canto superior direito</li>
                    <li>Clique em "Qualquer pessoa com o link pode visualizar"</li>
                    <li>Defina permissão como "Visualizar" apenas</li>
                    <li>Copie o novo link público gerado</li>
                    <li>Atualize o código com o novo link</li>
                </ol>
                <h5>Opção 2: Usar Upload Manual</h5>
                <ol>
                    <li>Baixe a planilha como Excel (.xlsx)</li>
                    <li>Abra no Excel e salve como CSV (UTF-8)</li>
                    <li>Use a opção "📄 Upload de Arquivo CSV" acima</li>
                </ol>
                <h5>Opção 3: Exportar para Serviço Público</h5>
                <ul>
                    <li>Exporte para Google Sheets público</li>
                    <li>Ou coloque o arquivo em repositório GitHub</li>
                    <li>Use um desses serviços no lugar do SharePoint corporativo</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
        else:
            st.markdown("""
            <div class="alert-warning">
                <h4>⚠️ Problema de Formatação dos Dados</h4>
                <p><strong>Soluções recomendadas:</strong></p>
                <ol>
                    <li><strong>Limpar dados no Google Sheets:</strong>
                        <ul>
                            <li>Abra a planilha original</li>
                            <li>Selecione todos os dados (Ctrl+A)</li>
                            <li>Copie para uma nova planilha</li>
                            <li>Use "Colar especial" → "Valores apenas"</li>
                            <li>Baixe como CSV e faça upload aqui</li>
                        </ul>
                    </li>
                    <li><strong>Usar Excel para limpeza:</strong>
                        <ul>
                            <li>Abra o arquivo no Excel</li>
                            <li>Use "Localizar e Substituir" para remover caracteres estranhos</li>
                            <li>Salve como CSV (UTF-8)</li>
                        </ul>
                    </li>
                    <li><strong>Hospedagem alternativa:</strong>
                        <ul>
                            <li>Coloque o CSV limpo no GitHub</li>
                            <li>Use a URL raw no código</li>
                        </ul>
                    </li>
                </ol>
            </div>
            """, unsafe_allow_html=True)
        
        return
    
    # Se os dados foram carregados com sucesso
    if df is not None and len(df) > 0:
        st.markdown(f"""
        <div class="alert-success">
            ✅ <strong>Dados carregados com sucesso!</strong><br>
            📋 52.429 editais encontrados | 8.574 editais em mais de uma categoria (16,35%) | 43.855 editais em apenas uma categoria (83,65%) | 🕐 {datetime.now().strftime('%H:%M:%S')}
        </div>
        """, unsafe_allow_html=True)
        
        # Conversões de tipos mais seguras
        if 'data realizacao licitacao' in df.columns:
            df['data realizacao licitacao'] = pd.to_datetime(df['data realizacao licitacao'], errors='coerce')
        
        if 'ano' in df.columns:
            df['ano'] = pd.to_numeric(df['ano'], errors='coerce')
        
        if 'Valor Estimado' in df.columns:
            # Limpeza de valores monetários
            df['Valor Estimado'] = df['Valor Estimado'].astype(str).str.replace(r'[^\d.,]', '', regex=True)
            df['Valor Estimado'] = df['Valor Estimado'].str.replace(',', '.', regex=False)
            df['Valor Estimado'] = pd.to_numeric(df['Valor Estimado'], errors='coerce')
        
        if 'pontuacao' in df.columns:
            df['pontuacao'] = df['pontuacao'].astype(str).str.replace(',', '.', regex=False)
            df['pontuacao'] = pd.to_numeric(df['pontuacao'], errors='coerce')
            
        if 'pontuacao_final' in df.columns:
            df['pontuacao_final'] = df['pontuacao_final'].astype(str).str.replace(',', '.', regex=False)
            df['pontuacao_final'] = pd.to_numeric(df['pontuacao_final'], errors='coerce')
        
        # Processamento da coluna observacoes - preenche valores em branco
        if 'observacoes' in df.columns:
            df['observacoes'] = df['observacoes'].apply(
                lambda x: x if pd.notna(x) and str(x).strip() != '' else 'Classificação baseada em Termos Chave'
            )
        
        # Renomeação de colunas específicas
        column_renames = {
            'classificacao_final - Copiar': 'Predição CIC',
            'predicao classificacao': 'Predição STI',
            'classificacao_final': 'Nova Predição',
            'observacoes': 'Observações'
        }
        
        for old_name, new_name in column_renames.items():
            if old_name in df.columns:
                df = df.rename(columns={old_name: new_name})
        
        # Remoção de duplicatas ignorando a coluna 'classificacao_final'
        columns_for_dedup = [col for col in df.columns if col != 'classificacao_final']
        if columns_for_dedup:
            df = df.drop_duplicates(subset=columns_for_dedup, keep='first')
        
        # Informações dos dados na sidebar
        st.sidebar.markdown("### 📊 Informações dos Dados")
        
        # Status da conexão com ícone verde - simplificado sem verificação de data_source
        st.sidebar.markdown("**Fonte:** 🔗 SharePoint TCERJ (Automático) 🟢")

        # Informações estatísticas fixas da base completa
        st.sidebar.markdown("**Total de Editais:** 52.429")
        st.sidebar.markdown("**Total de Categorias:** 14") 
        st.sidebar.markdown("**Total Estimado:** R$ 244 bilhões")
        
        # **SEÇÃO DE BUSCA AVANÇADA**
        st.sidebar.markdown("### 🔍 Busca Avançada")

        with st.sidebar.expander("🔎 Filtros de Texto Avançados", expanded=False):
            search_params = {}
            
            # Initialize session state keys if they don't exist
            if "limpar_filtros_texto" not in st.session_state:
                st.session_state["limpar_filtros_texto"] = False
            if "search_and" not in st.session_state:
                st.session_state["search_and"] = ""
            if "search_or" not in st.session_state:
                st.session_state["search_or"] = ""
            if "search_not" not in st.session_state:
                st.session_state["search_not"] = ""

            # Check if reset flag is active and clear filters if needed
            if st.session_state["limpar_filtros_texto"]:
                st.session_state["search_and"] = ""
                st.session_state["search_or"] = ""
                st.session_state["search_not"] = ""
                st.session_state["limpar_filtros_texto"] = False
                st.rerun()

            # Reset button - must be before the input widgets
            if st.button("🔄 Limpar Filtros de Texto", 
                         use_container_width=True,
                         help="Remove todos os filtros de texto aplicados"):
                st.session_state["limpar_filtros_texto"] = True
                st.rerun()
            
            # Now create the input widgets
            search_params['contains_and'] = st.text_input(
                "🔗 Deve conter TODOS os termos (E)",
                placeholder="frase completa OU termo1; termo2; termo3",
                help="SEM ';' = busca frase completa. COM ';' = todos os termos devem estar presentes",
                key="search_and"
            )
            
            search_params['contains_or'] = st.text_input(
                "🔀 Deve conter ALGUM termo (OU)",
                placeholder="frase completa OU termo1; termo2; termo3",
                help="SEM ';' = busca frase completa. COM ';' = pelo menos um termo deve estar presente",
                key="search_or"
            )
            
            search_params['not_contains'] = st.text_input(
                "❌ NÃO deve conter",
                placeholder="frase completa OU termo1; termo2",
                help="SEM ';' = exclui frase completa. COM ';' = exclui qualquer um dos termos",
                key="search_not"
            )

            # Exemplos e indicador de filtros ativos permanecem os mesmos
            st.markdown("""
            **💡 Exemplos:**
            - **FRASE**: "bens permanentes" → busca exata
            - **TERMOS**: "bens; permanentes" → ambos separados
            - **NEGATIVO**: "consultoria; terceirizado" → exclui ambos
            """)
    
            # Indicador de filtros ativos
            active_searches = [key for key, value in search_params.items() if value and value.strip()]
            if active_searches:
                st.success(f"🔍 {len(active_searches)} filtro(s) de busca ativo(s)")
            else:
                st.info("🔍 Nenhum filtro de busca ativo")
        
        # **CRIAÇÃO DOS FILTROS ESPECÍFICOS**
        st.sidebar.markdown("### 🎛️ Filtros Específicos")

        # Lista predefinida de classificações
        CLASSIFICACOES = [
            'EDUCAÇÃO',
            'SAÚDE',
            'TECNOLOGIA DA INFORMAÇÃO',
            'SANEAMENTO',
            'MOBILIDADE',
            'SEGURANÇA PÚBLICA',
            'DESENVOLVIMENTO',
            'OBRAS',
            'GOVERNANÇA',
            'PESSOAL',
            'DESESTATIZAÇÃO',
            'OUTROS',
            'RECEITA',
            'PREVIDÊNCIA'
        ]

        filters = {}

        # Nova Predição (primeiro filtro) - CORRIGIDO
        nova_predicao = st.sidebar.selectbox(
            "📂 Nova Predição (contém)",
            options=['Todas'] + CLASSIFICACOES,
            key='nova_predicao',
            help="Busca por containment - encontra editais que CONTÊM a categoria selecionada"
        )
        if nova_predicao != 'Todas':
            filters['Nova Predição'] = nova_predicao

        # Predição Antiga
        if 'Predição Antiga' in df.columns:
            predicao_antiga = st.sidebar.selectbox(
                "🔄 Predição Antiga",
                options=['Todas'] + sorted(df['Predição Antiga'].dropna().unique().tolist()),
                key='predicao_antiga'
            )
            if predicao_antiga != 'Todas':
                filters['Predição Antiga'] = predicao_antiga

        # Ano
        if 'Ano' in df.columns:
            ano = st.sidebar.selectbox(
                "📅 Ano",
                options=['Todos'] + sorted([str(int(ano)) for ano in df['Ano'].dropna().unique()]),
                key='ano'
            )
            if ano != 'Todos':
                filters['Ano'] = ano

        # Unidade
        if 'Unidade' in df.columns:
            unidades = ['Todas'] + sorted(df['Unidade'].unique().tolist())
            unidade = st.sidebar.selectbox(
                "🏢 Unidade",
                options=unidades,
                key='unidade'
            )
            if unidade != 'Todas':
                filters['Unidade'] = unidade
        
        # Indicador de filtros específicos ativos
        active_specific_filters = []
        if nova_predicao != 'Todas':
            active_specific_filters.append("Nova Predição")
        if 'Predição Antiga' in df.columns and predicao_antiga != 'Todas':
            active_specific_filters.append("Predição Antiga")
        if 'Ano' in df.columns and ano != 'Todos':
            active_specific_filters.append("Ano")
        if 'Unidade' in df.columns and unidade != 'Todas':
            active_specific_filters.append("Unidade")
        
        if active_specific_filters:
            st.sidebar.success(f"🎛️ {len(active_specific_filters)} filtro(s) específico(s) ativo(s)")
        else:
            st.sidebar.info("🎛️ Nenhum filtro específico ativo")
        
        # Aplicação dos filtros - CORRIGIDA
        filtered_df = apply_filters(df, search_params, filters)
        
        # Criação das abas após o processamento dos filtros
        tab1, tab2, tab3 = st.tabs(["📊 Análise de Dados", "📈 Dashboard", "📚 Ajuda"])
        
        with tab1:
            # Métricas de visão geral
            st.markdown("### 📊 Dados Carregados para Análise")
            create_overview_metrics(filtered_df)
            
            # Informações adicionais sobre categorização
            st.markdown("### 📈 Análise de Categorização")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    label="📋 Editais em Múltiplas Categorias",
                    value="8.574",
                    delta="16,35%"
                )
            
            with col2:
                st.metric(
                    label="📄 Editais em Categoria Única",
                    value="43.855", 
                    delta="83,65%"
                )
            
            with col3:
                # Calcula % de mudança entre as predições
                if 'Nova Predição' in filtered_df.columns and 'Predição Antiga' in filtered_df.columns:
                    total_linhas = len(filtered_df)
                    if total_linhas > 0:
                        linhas_diferentes = len(filtered_df[filtered_df['Nova Predição'].fillna('') != filtered_df['Predição Antiga'].fillna('')])
                        percentual_mudanca = (linhas_diferentes / total_linhas) * 100
                        
                        st.metric(
                            label="🔄 Mudanças nas Predições",
                            value=f"{percentual_mudanca:.1f}%",
                            delta=f"{linhas_diferentes:,} casos"
                        )
                    else:
                        st.metric(
                            label="🔄 Mudanças nas Predições",
                            value="0%",
                            delta="0 casos"
                        )
            
            # Texto explicativo sobre as mudanças
            if 'Nova Predição' in filtered_df.columns and 'Predição Antiga' in filtered_df.columns:
                total_linhas = len(filtered_df)
                if total_linhas > 0:
                    linhas_diferentes = len(filtered_df[filtered_df['Nova Predição'].fillna('') != filtered_df['Predição Antiga'].fillna('')])
                    percentual_mudanca = (linhas_diferentes / total_linhas) * 100
                    
                    st.info(f"📊 **Foram identificadas mudanças em {percentual_mudanca:.1f}% dos casos, onde a Nova Predição difere da Predição Antiga.**")
            
            if len(filtered_df) == 0:
                st.warning("⚠️ Nenhum resultado encontrado com os filtros aplicados. Tente ajustar os critérios de busca.")
            else:
                # Exibir informações dos filtros aplicados
                active_search = any(search_params.values()) if search_params else False
                active_filters = any(
                    (isinstance(v, list) and v != ['Todas']) or 
                    (isinstance(v, str) and v not in ['Todas', 'Todos']) or
                    (isinstance(v, tuple))  # valor_range
                    for v in filters.values()
                )
                
                if active_search or active_filters:
                    filter_info = f"🔍 **Filtros aplicados** - Exibindo {len(filtered_df):,} de 52.429 editais"
                    
                    # Adiciona informação sobre busca avançada se aplicável
                    if active_search:
                        search_types = []
                        if search_params.get('contains_and'):
                            search_types.append("E")
                        if search_params.get('contains_or'):
                            search_types.append("OU")
                        if search_params.get('not_contains'):
                            search_types.append("NÃO")
                        if search_types:
                            filter_info += f" | 🔎 Busca avançada: {', '.join(search_types)}"
                    
                    # Adiciona informação sobre filtros específicos
                    if active_filters:
                        filter_types = []
                        if filters.get('Nova Predição'):
                            filter_types.append(f"Nova Predição: {filters['Nova Predição']}")
                        if filters.get('Predição Antiga'):
                            filter_types.append(f"Predição Antiga: {filters['Predição Antiga']}")
                        if filters.get('Ano'):
                            filter_types.append(f"Ano: {filters['Ano']}")
                        if filters.get('Unidade'):
                            filter_types.append(f"Unidade: {filters['Unidade']}")
                        if filter_types:
                            filter_info += f" | 🎛️ Filtros: {', '.join(filter_types)}"
                    
                    st.info(filter_info)
                
                # Tabela de dados
                display_data_table(filtered_df)
        
        with tab2:
            st.markdown("### 📊 Dashboard Analítico")
            
            if len(filtered_df) > 0:
                # Mostrar informação de filtros se aplicados
                active_search = any(search_params.values()) if search_params else False
                active_filters = any(
                    (isinstance(v, list) and v != ['Todas']) or 
                    (isinstance(v, str) and v not in ['Todas', 'Todos']) or
                    (isinstance(v, tuple))
                    for v in filters.values()
                )
                
                if active_search or active_filters:
                    filter_info = f"🔍 **Visualizando dados filtrados** - {len(filtered_df):,} de 52.429 editais"
                    
                    if active_search:
                        search_types = []
                        if search_params.get('contains_and'):
                            search_types.append("E")
                        if search_params.get('contains_or'):
                            search_types.append("OU")
                        if search_params.get('not_contains'):
                            search_types.append("NÃO")
                        if search_types:
                            filter_info += f" | 🔎 Busca avançada: {', '.join(search_types)}"
                    
                    st.info(filter_info)
                
                # Métricas principais
                st.markdown("### 📊 Dados Filtrados para Análise")
                create_overview_metrics(filtered_df)
                
                # Informações adicionais sobre categorização
                st.markdown("### 📈 Análise de Categorização")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        label="📋 Editais em Múltiplas Categorias",
                        value="8.574",
                        delta="16,35%"
                    )
                
                with col2:
                    st.metric(
                        label="📄 Editais em Categoria Única",
                        value="43.855", 
                        delta="83,65%"
                    )
                
                with col3:
                    # Calcula % de mudança entre as predições
                    if 'Nova Predição' in filtered_df.columns and 'Predição Antiga' in filtered_df.columns:
                        total_linhas = len(filtered_df)
                        if total_linhas > 0:
                            linhas_diferentes = len(filtered_df[filtered_df['Nova Predição'].fillna('') != filtered_df['Predição Antiga'].fillna('')])
                            percentual_mudanca = (linhas_diferentes / total_linhas) * 100
                            
                            st.metric(
                                label="🔄 Mudanças nas Predições",
                                value=f"{percentual_mudanca:.1f}%",
                                delta=f"{linhas_diferentes:,} casos"
                            )
                        else:
                            st.metric(
                                label="🔄 Mudanças nas Predições",
                                value="0%",
                                delta="0 casos"
                            )
                
                # Texto explicativo sobre as mudanças
                if 'Nova Predição' in filtered_df.columns and 'Predição Antiga' in filtered_df.columns:
                    total_linhas = len(filtered_df)
                    if total_linhas > 0:
                        linhas_diferentes = len(filtered_df[filtered_df['Nova Predição'].fillna('') != filtered_df['Predição Antiga'].fillna('')])
                        percentual_mudanca = (linhas_diferentes / total_linhas) * 100
                        
                        st.info(f"📊 **Foram identificadas mudanças em {percentual_mudanca:.1f}% dos casos, onde a Nova Predição difere da Predição Antiga.**")
                
                # Gráficos
                create_charts(filtered_df)
                
                # Estatísticas adicionais
                if 'Nova Predição' in filtered_df.columns:
                    st.markdown("### 📋 Análise Detalhada por Classificação")
                    
                    classification_stats = filtered_df.groupby('Nova Predição').agg({
                        'Valor Estimado': ['count', 'sum', 'mean'],
                        'pontuacao': 'mean' if 'pontuacao' in filtered_df.columns else 'count'
                    }).round(2)
                    
                    classification_stats.columns = ['Quantidade', 'Valor Total', 'Valor Médio', 'Pontuação Média']
                    
                    st.dataframe(
                        classification_stats.sort_values('Quantidade', ascending=False),
                        use_container_width=True
                    )
            else:
                st.warning("⚠️ Nenhum dado disponível para exibir no dashboard com os filtros aplicados.")
        
        with tab3:
            show_help_tab()
    
    else:
        st.markdown("""
        <div class="alert-info">
            <h3>👋 Bem-vindo ao Projeto Predição de Editais - CIC2025!</h3>
            <p><strong>📊 Nossa base completa contém:</strong></p>
            <ul style="margin: 1rem 0;">
                <li><strong>52.429 editais</strong> analisados e classificados</li>
                <li><strong>R$ 244 bilhões</strong> em valor total estimado</li>
                <li><strong>729 unidades</strong> organizacionais mapeadas</li>
                <li><strong>14 categorias</strong> originais + <strong>2 novas categorias</strong></li>
            </ul>
            
            <p><strong>🚀 Para começar sua consulta:</strong></p>
            <ol>
                <li>📁 Selecione uma fonte de dados acima</li>
                <li>🔍 Use os filtros avançados para encontrar informações específicas</li>
                <li>📊 Explore as visualizações no dashboard</li>
                <li>📥 Exporte os dados filtrados automaticamente</li>
            </ol>
            
            <p><strong>🆕 Novidades da versão corrigida:</strong></p>
            <ul>
                <li>🔍 <strong>Busca Avançada</strong> com operadores lógicos (E, OU, NÃO)</li>
                <li>📂 <strong>Filtros Containment</strong> para "Nova Predição"</li>
                <li>🔄 <strong>Aplicação Sequencial</strong> de filtros múltiplos</li>
                <li>📥 <strong>Exportação Automática</strong> em CSV/XLSX</li>
            </ul>
            
            <p><strong>💡 Dica:</strong> Acesse a aba "📚 Ajuda" para instruções detalhadas sobre todas as funcionalidades!</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

