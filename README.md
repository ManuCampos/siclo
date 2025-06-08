# 📊 Exportador de Categorias por Abas - Editais

Este aplicativo em **Streamlit** permite importar um arquivo CSV contendo uma coluna chamada `Nova Predição`, e exportar um arquivo Excel com uma aba para cada categoria identificada nessa coluna.

---

## 🚀 Como usar

### 1. Suba seu CSV
- A coluna `Nova Predição` deve conter valores separados por `;` ou `,` representando múltiplas categorias por linha (ex: `Educação; Saúde`).

### 2. Visualize os dados
- O app mostra uma prévia dos dados carregados.

### 3. Baixe a planilha final
- O botão permite exportar um Excel com uma aba para cada categoria encontrada.

---

## 🛠️ Como rodar localmente

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio

# Instale as dependências
pip install -r requirements.txt

# Rode o app
streamlit run ResultadosC3.py
```

---

## 📦 Estrutura do projeto

```
.
├── ResultadosC3.py         # Código principal do app Streamlit
├── requirements.txt        # Bibliotecas necessárias
└── README.md               # Instruções do projeto
```

---

## 🌐 Deploy

Você pode fazer o deploy gratuito pelo [Streamlit Cloud](https://streamlit.io/cloud). Basta conectar seu repositório do GitHub e apontar para `ResultadosC3.py`.

---

## ✉️ Contato

Desenvolvido por Manu Campos.  
Email: [seu-email@exemplo.com]  
