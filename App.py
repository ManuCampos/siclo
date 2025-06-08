import streamlit as st
import pandas as pd
import io
from datetime import datetime

# Função auxiliar para extrair categorias únicas da coluna
def extract_unique_categories(df, column_name):
    """Extrai categorias únicas de uma coluna multi-label (separadas por ; ou ,)"""
    if column_name not in df.columns:
        return []

    unique_categories = set()
    for value in df[column_name].dropna():
        value_str = str(value).strip()
        if not value_str:
            continue

        if ';' in value_str:
            categories = [cat.strip() for cat in value_str.split(';') if cat.strip()]
        elif ',' in value_str:
            categories = [cat.strip() for cat in value_str.split(',') if cat.strip()]
        else:
            categories = [value_str]

        unique_categories.update(categories)

    return sorted(list(unique_categories))[:14]

# Função principal para exportar as abas
def exportar_aba_por_categoria(df, coluna_categoria='Nova Predição'):
    """Exporta um arquivo Excel com uma aba por categoria encontrada"""
    categorias = extract_unique_categories(df, coluna_categoria)

    if not categorias:
        st.warning("⚠️ Nenhuma categoria encontrada para exportar.")
        return

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for categoria in categorias:
            aba_df = df[df[coluna_categoria].fillna('').str.contains(categoria, case=False, na=False)]
            if not aba_df.empty:
                aba_df.to_excel(writer, index=False, sheet_name=categoria[:31])  # Nome máximo da aba: 31 caracteres

    st.download_button(
        label="📥 Baixar Planilha com Abas por Categoria",
        data=output.getvalue(),
        file_name=f"editais_categorizados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )

# Interface principal
def main():
    st.set_page_config(page_title="Exportador de Categorias", layout="wide")
    st.title("📊 Exportador de Categorias por Abas - Editais")

    uploaded_file = st.file_uploader("📁 Envie um arquivo CSV contendo a coluna 'Nova Predição'")

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.success("✅ Arquivo carregado com sucesso!")

            if 'Nova Predição' in df.columns:
                st.markdown("### 🔍 Pré-visualização dos dados")
                st.dataframe(df.head())
                
                st.markdown("### 📤 Exportar planilha com abas")
                exportar_aba_por_categoria(df)
            else:
                st.error("❌ A coluna 'Nova Predição' não foi encontrada no arquivo enviado.")
        except Exception as e:
            st.error(f"❌ Erro ao ler o arquivo: {e}")

if __name__ == "__main__":
    main()
