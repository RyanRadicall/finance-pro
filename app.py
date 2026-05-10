import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import hashlib
from datetime import date

st.set_page_config(page_title="Finance PRO", layout="wide")

# =========================
# CONFIG
# =========================
DB = "finance.db"
COLUNAS = ["Data", "Descricao", "Categoria", "Tipo", "Valor"]

# =========================
# ESTILO
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
# BANCO SQLITE
# =========================
conn = sqlite3.connect(DB, check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    username TEXT PRIMARY KEY,
    senha TEXT NOT NULL,
    meta REAL DEFAULT 5000,
    limite REAL DEFAULT 3000
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS lancamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT,
    data TEXT,
    descricao TEXT,
    categoria TEXT,
    tipo TEXT,
    valor REAL
)
""")

conn.commit()

# =========================
# HELPERS
# =========================
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def brl(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# =========================
# LOGIN
# =========================
def tela_login():
    opcao = st.sidebar.selectbox(
        "Acesso",
        ["Login", "Cadastrar", "Redefinir Senha"]
    )

    # LOGIN
    if opcao == "Login":
        st.sidebar.subheader("🔐 Login")

        user = st.sidebar.text_input("Usuário")
        senha = st.sidebar.text_input("Senha", type="password")

        if st.sidebar.button("Entrar"):
            cur.execute(
                "SELECT senha FROM usuarios WHERE username=?",
                (user,)
            )
            row = cur.fetchone()

            if row and row[0] == hash_senha(senha):
                st.session_state["logado"] = True
                st.session_state["usuario"] = user
                st.rerun()
            else:
                st.sidebar.error("Login inválido")

    # CADASTRO
    elif opcao == "Cadastrar":
        st.sidebar.subheader("📝 Criar conta")

        new_user = st.sidebar.text_input("Novo usuário")
        new_pass = st.sidebar.text_input(
            "Nova senha",
            type="password"
        )

        if st.sidebar.button("Cadastrar"):
            try:
                cur.execute("""
                INSERT INTO usuarios
                (username, senha)
                VALUES (?, ?)
                """, (
                    new_user,
                    hash_senha(new_pass)
                ))
                conn.commit()
                st.sidebar.success("Usuário criado!")
            except:
                st.sidebar.error("Usuário já existe")

    # RESET
    elif opcao == "Redefinir Senha":
        st.sidebar.subheader("🔄 Redefinir senha")

        user = st.sidebar.text_input("Usuário")
        senha_atual = st.sidebar.text_input(
            "Senha atual",
            type="password"
        )
        nova_senha = st.sidebar.text_input(
            "Nova senha",
            type="password"
        )

        if st.sidebar.button("Atualizar"):
            cur.execute(
                "SELECT senha FROM usuarios WHERE username=?",
                (user,)
            )
            row = cur.fetchone()

            if not row:
                st.sidebar.error("Usuário não existe")
            elif row[0] != hash_senha(senha_atual):
                st.sidebar.error("Senha atual incorreta")
            else:
                cur.execute("""
                UPDATE usuarios
                SET senha=?
                WHERE username=?
                """, (
                    hash_senha(nova_senha),
                    user
                ))
                conn.commit()
                st.sidebar.success("Senha atualizada!")

# =========================
# SESSÃO
# =========================
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    tela_login()
    st.stop()

usuario = st.session_state["usuario"]

# =========================
# LOGOUT
# =========================
if st.sidebar.button("🚪 Sair"):
    st.session_state["logado"] = False
    st.rerun()

st.title("💸 Finance PRO")

# =========================
# CONFIG USUÁRIO
# =========================
cur.execute("""
SELECT meta, limite
FROM usuarios
WHERE username=?
""", (usuario,))
meta, limite = cur.fetchone()

meta = st.sidebar.number_input(
    "🎯 Meta mensal",
    value=float(meta)
)

limite = st.sidebar.number_input(
    "💳 Limite do cartão",
    value=float(limite)
)

cur.execute("""
UPDATE usuarios
SET meta=?, limite=?
WHERE username=?
""", (
    meta,
    limite,
    usuario
))
conn.commit()

# =========================
# NOVO LANÇAMENTO
# =========================
st.sidebar.header("➕ Novo lançamento")

data = st.sidebar.date_input(
    "Data",
    value=date.today()
)

descricao = st.sidebar.text_input(
    "Descrição"
)

categoria = st.sidebar.selectbox(
    "Categoria",
    [
        "Salário",
        "Renda Extra",
        "Moradia",
        "Alimentação",
        "Transporte",
        "Saúde",
        "Lazer",
        "Investimentos",
        "Educação",
        "Cartão",
        "Outros"
    ]
)

tipo = st.sidebar.selectbox(
    "Tipo",
    ["Entrada", "Saída"]
)

valor = st.sidebar.number_input(
    "Valor",
    min_value=0.0,
    step=10.0
)

if st.sidebar.button("Salvar"):
    if descricao and valor > 0:
        cur.execute("""
        INSERT INTO lancamentos
        (
            usuario,
            data,
            descricao,
            categoria,
            tipo,
            valor
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            usuario,
            str(data),
            descricao,
            categoria,
            tipo,
            valor
        ))
        conn.commit()
        st.success("Salvo!")
        st.rerun()

# =========================
# CARREGAR DADOS
# =========================
df = pd.read_sql_query("""
SELECT *
FROM lancamentos
WHERE usuario=?
""", conn, params=(usuario,))

if df.empty:
    st.warning("Nenhum dado disponível ainda")
    st.stop()

df["Data"] = pd.to_datetime(df["data"])

# =========================
# FILTROS
# =========================
categorias = st.sidebar.multiselect(
    "Categoria",
    df["categoria"].unique(),
    default=df["categoria"].unique()
)

tipos = st.sidebar.multiselect(
    "Tipo",
    df["tipo"].unique(),
    default=df["tipo"].unique()
)

df_f = df[
    df["categoria"].isin(categorias)
    &
    df["tipo"].isin(tipos)
]

# =========================
# KPIs
# =========================
entradas = df_f[df_f["tipo"]=="Entrada"]["valor"].sum()
saidas = df_f[df_f["tipo"]=="Saída"]["valor"].sum()
saldo = entradas - saidas

c1, c2, c3 = st.columns(3)

c1.metric("💰 Entradas", brl(entradas))
c2.metric("💸 Saídas", brl(saidas))
c3.metric("📊 Saldo", brl(saldo))

# =========================
# META
# =========================
st.subheader("🎯 Progresso da Meta")

progresso = saldo / meta if meta > 0 else 0
st.progress(min(max(progresso, 0), 1))

# =========================
# CARTÃO
# =========================
st.subheader("💳 Cartão")

cartao = df[
    (df["categoria"]=="Cartão")
    &
    (df["tipo"]=="Saída")
]

gasto_cartao = cartao["valor"].sum()
uso = gasto_cartao / limite if limite > 0 else 0

st.progress(min(max(uso, 0), 1))
st.write(
    f"{brl(gasto_cartao)} / {brl(limite)}"
)

if uso > 0.8:
    st.warning("⚠️ Mais de 80% usado")

if uso >= 1:
    st.error("🚨 Limite estourado")

# =========================
# GRÁFICOS
# =========================
col1, col2 = st.columns(2)

with col1:
    gastos = df_f[df_f["tipo"]=="Saída"]

    if not gastos.empty:
        fig = px.pie(
            gastos,
            names="categoria",
            values="valor",
            hole=0.5
        )
        st.plotly_chart(
            fig,
            use_container_width=True
        )

with col2:
    df_f = df_f.sort_values("Data")
    df_f["Saldo"] = df_f["valor"].where(
        df_f["tipo"]=="Entrada",
        -df_f["valor"]
    ).cumsum()

    fig = px.line(
        df_f,
        x="Data",
        y="Saldo",
        markers=True
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =========================
# IA SIMPLES
# =========================
st.subheader("🧠 Análise Inteligente")

gastos = df[df["tipo"]=="Saída"]

if not gastos.empty:
    total = gastos["valor"].sum()
    por_cat = gastos.groupby(
        "categoria"
    )["valor"].sum()

    maior_cat = por_cat.idxmax()
    maior_valor = por_cat.max()
    media = gastos["valor"].mean()

    st.write(
        f"📊 Total gasto: {brl(total)}"
    )
    st.write(
        f"🔥 Maior gasto: {maior_cat} ({brl(maior_valor)})"
    )
    st.write(
        f"📉 Média: {brl(media)}"
    )

# =========================
# TABELA
# =========================
st.subheader("📋 Registros")

st.dataframe(
    df[
        ["id","data","descricao",
         "categoria","tipo","valor"]
    ],
    use_container_width=True
)

if len(df) > 0:
    idx = st.number_input(
        "ID para deletar",
        min_value=int(df["id"].min()),
        max_value=int(df["id"].max()),
        step=1
    )

    if st.button("🗑️ Deletar"):
        cur.execute(
            "DELETE FROM lancamentos WHERE id=?",
            (int(idx),)
        )
        conn.commit()
        st.rerun()
