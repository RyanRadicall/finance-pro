import streamlit as st
import pandas as pd
import plotly.express as px
import os
import hashlib

st.set_page_config(page_title="Finance PRO", layout="wide")

# =========================
# PADRÃO DE COLUNAS
# =========================
COLUNAS = ["Data","Descricao","Categoria","Tipo","Valor"]

# =========================
# ESTILO DARK
# =========================
st.markdown("""
<style>
body {background-color: #0E1117;}
[data-testid="metric-container"] {
    background-color: #1C1F26;
    padding: 15px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# LOGIN
# =========================
# =========================
# USUÁRIOS (BANCO)
# =========================
ARQUIVO_USERS = "usuarios.json"

import json

def carregar_usuarios():
    if os.path.exists(ARQUIVO_USERS):
        with open(ARQUIVO_USERS, "r") as f:
            return json.load(f)
    return {}

def salvar_usuarios(users):
    with open(ARQUIVO_USERS, "w") as f:
        json.dump(users, f)

usuarios = carregar_usuarios()

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

# =========================
# TELA DE LOGIN
# =========================
def tela_login():
    opcao = st.sidebar.selectbox("Acesso", ["Login", "Cadastrar", "Redefinir Senha"])

    # LOGIN
    if opcao == "Login":
        st.sidebar.subheader("🔐 Login")

        user = st.sidebar.text_input("Usuário")
        senha = st.sidebar.text_input("Senha", type="password")

        if st.sidebar.button("Entrar"):
            if user in usuarios and usuarios[user] == hash_senha(senha):
                st.session_state["logado"] = True
                st.session_state["usuario"] = user
            else:
                st.sidebar.error("Login inválido")

    # CADASTRO
    elif opcao == "Cadastrar":
        st.sidebar.subheader("📝 Criar conta")

        new_user = st.sidebar.text_input("Novo usuário")
        new_pass = st.sidebar.text_input("Nova senha", type="password")

        if st.sidebar.button("Cadastrar"):
            if new_user in usuarios:
                st.sidebar.warning("Usuário já existe")
            elif new_user == "" or new_pass == "":
                st.sidebar.warning("Preencha tudo")
            else:
                usuarios[new_user] = hash_senha(new_pass)
                salvar_usuarios(usuarios)
                st.sidebar.success("Usuário criado!")

    # RESET
    elif opcao == "Redefinir Senha":
        st.sidebar.subheader("🔄 Redefinir senha")

        user = st.sidebar.text_input("Usuário")
        nova_senha = st.sidebar.text_input("Nova senha", type="password")

        if st.sidebar.button("Atualizar"):
            if user not in usuarios:
                st.sidebar.error("Usuário não existe")
            else:
                usuarios[user] = hash_senha(nova_senha)
                salvar_usuarios(usuarios)
                st.sidebar.success("Senha atualizada!")

# =========================
# CONTROLE DE SESSÃO
# =========================
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    tela_login()
    st.stop()

# =========================
# BANCO DE DADOS
# =========================
ARQUIVO_DB = f"dados_{st.session_state['usuario']}.json"

def carregar():
    if os.path.exists(ARQUIVO_DB):
        df = pd.read_json(ARQUIVO_DB)
        return df.reindex(columns=COLUNAS)
    return pd.DataFrame(columns=COLUNAS)

def salvar(df):
    df.to_json(ARQUIVO_DB, orient="records", date_format="iso")

df = carregar()

st.title("💸 Finance PRO")

# =========================
# NOVO LANÇAMENTO
# =========================
st.sidebar.header("➕ Novo lançamento")

data = st.sidebar.date_input("Data")
descricao = st.sidebar.text_input("Descrição")
categoria = st.sidebar.selectbox("Categoria", [
    "Salário","Renda Extra","Moradia","Alimentação","Transporte",
    "Saúde","Lazer","Investimentos","Educação","Cartão","Outros"
])
tipo = st.sidebar.selectbox("Tipo", ["Entrada","Saída"])
valor = st.sidebar.number_input("Valor", min_value=0.0, step=10.0)

if st.sidebar.button("Salvar"):
    if descricao == "" or valor == 0:
        st.sidebar.warning("Preencha os dados corretamente")
    else:
        novo = pd.DataFrame([[data, descricao, categoria, tipo, valor]],
                            columns=COLUNAS)
        df = pd.concat([df, novo], ignore_index=True)
        salvar(df)
        st.success("Salvo!")
        st.rerun()

# =========================
# LIMPAR SEM ERRO
# =========================
if st.sidebar.button("🧹 Limpar tudo"):
    df = pd.DataFrame(columns=COLUNAS)
    salvar(df)
    st.success("Dados apagados!")
    st.rerun()

# =========================
# FILTROS
# =========================
if not df.empty:
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

    categorias = st.sidebar.multiselect(
        "Categoria", df["Categoria"].dropna().unique(),
        default=df["Categoria"].dropna().unique()
    )

    tipos = st.sidebar.multiselect(
        "Tipo", df["Tipo"].dropna().unique(),
        default=df["Tipo"].dropna().unique()
    )

    df_f = df[
        (df["Categoria"].isin(categorias)) &
        (df["Tipo"].isin(tipos))
    ]
else:
    df_f = pd.DataFrame(columns=COLUNAS)

# =========================
# PROTEÇÃO CONTRA ERRO
# =========================
if df_f.empty:
    st.warning("Nenhum dado disponível ainda")
    st.stop()

# =========================
# KPIs
# =========================
entradas = df_f[df_f["Tipo"]=="Entrada"]["Valor"].sum()
saidas = df_f[df_f["Tipo"]=="Saída"]["Valor"].sum()
saldo = entradas - saidas

col1, col2, col3 = st.columns(3)

col1.metric("💰 Entradas", f"R$ {entradas:,.2f}")
col2.metric("💸 Saídas", f"R$ {saidas:,.2f}")
col3.metric("📊 Saldo", f"R$ {saldo:,.2f}")

# =========================
# META
# =========================
meta = st.sidebar.number_input("🎯 Meta mensal", value=5000)

st.subheader("🎯 Progresso da Meta")
progresso = saldo / meta if meta > 0 else 0
st.progress(min(max(progresso, 0), 1))

# =========================
# CARTÃO
# =========================
st.subheader("💳 Cartão de Crédito")

limite = st.sidebar.number_input("Limite do cartão", value=3000)

cartao = df[df["Categoria"] == "Cartão"]
gasto_cartao = cartao["Valor"].sum()

uso = gasto_cartao / limite if limite > 0 else 0

st.progress(min(max(uso, 0), 1))
st.write(f"💸 Usado: R$ {gasto_cartao:,.2f} / R$ {limite:,.2f}")

if uso > 0.8:
    st.warning("⚠️ Mais de 80% do limite usado")

if uso >= 1:
    st.error("🚨 Limite estourado")

# =========================
# GRÁFICOS
# =========================
col4, col5 = st.columns(2)

with col4:
    gastos = df_f[df_f["Tipo"]=="Saída"]
    if not gastos.empty:
        fig = px.pie(gastos, names="Categoria", values="Valor", hole=0.5)
        st.plotly_chart(fig, use_container_width=True)

with col5:
    df_f = df_f.sort_values("Data")
    df_f["Saldo"] = df_f["Valor"].where(df_f["Tipo"]=="Entrada", -df_f["Valor"]).cumsum()
    fig = px.line(df_f, x="Data", y="Saldo", markers=True)
    st.plotly_chart(fig, use_container_width=True)

# =========================
# IA SIMPLES
# =========================
st.subheader("🧠 Análise Inteligente")

gastos = df[df["Tipo"]=="Saída"]

if not gastos.empty:
    total = gastos["Valor"].sum()
    por_categoria = gastos.groupby("Categoria")["Valor"].sum()

    maior_cat = por_categoria.idxmax()
    maior_valor = por_categoria.max()
    media = gastos["Valor"].mean()

    st.write(f"📊 Total gasto: R$ {total:,.2f}")
    st.write(f"🔥 Maior gasto: {maior_cat} (R$ {maior_valor:,.2f})")
    st.write(f"📉 Média: R$ {media:,.2f}")

    if maior_valor > total * 0.4:
        st.warning(f"⚠️ Muito gasto em {maior_cat}")

    if saldo < 0:
        st.error("🚨 Você está no negativo")

# =========================
# TABELA
# =========================
st.subheader("📋 Registros")

st.dataframe(df, use_container_width=True)

if len(df) > 0:
    index_delete = st.number_input("ID para deletar", min_value=0, max_value=len(df)-1, step=1)

    if st.button("🗑️ Deletar"):
        df = df.drop(index_delete).reset_index(drop=True)
        salvar(df)
        st.rerun()