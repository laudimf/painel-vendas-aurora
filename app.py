"""Painel de vendas da Loja Aurora Cosméticos (dados fictícios) em Streamlit."""
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Painel de vendas — Loja Aurora", page_icon="🧴", layout="wide")

CSV = Path(__file__).parent / "pedidos_loja_aurora_2025_ficticio.csv"
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def brl(v):
    return "R$ " + f"{v:,.0f}".replace(",", ".")


def pct(v):
    return f"{v * 100:.1f}".replace(".", ",") + "%"


@st.cache_data
def carregar():
    df = pd.read_csv(CSV, encoding="utf-8-sig", parse_dates=["data"])
    df = df.drop_duplicates("pedido_id")
    # padroniza o canal (espaços e maiúsculas), usando a grafia mais frequente
    chave = df["canal"].str.strip().str.lower()
    padrao = (df.assign(c=df["canal"].str.strip(), k=chave)
                .groupby("k")["c"].agg(lambda s: s.mode().iloc[0]))
    df["canal"] = chave.map(padrao)
    df["receita"] = df["quantidade"] * df["preco_unitario"] * (1 - df["desconto_pct"])
    df["lucro"] = df["receita"] * (1 - df["taxa_canal_pct"]) - df["quantidade"] * df["custo_unit"]
    df["entregue"] = df["status"] == "Entregue"
    df["cancelado"] = df["status"] == "Cancelado"
    df["mes"] = df["data"].dt.month
    return df


def indicadores(d):
    ent = d[d["entregue"]]
    rec, luc = ent["receita"].sum(), ent["lucro"].sum()
    return {
        "receita": rec,
        "margem": luc / rec if rec else 0,
        "entregues": len(ent),
        "ticket": rec / len(ent) if len(ent) else 0,
        "cancel": d["cancelado"].mean() if len(d) else 0,
    }


def tabela(d, coluna):
    total = d.loc[d["entregue"], "receita"].sum()
    linhas = []
    for nome, g in d.groupby(coluna):
        i = indicadores(g)
        linhas.append({
            coluna.capitalize(): nome,
            "% da receita": i["receita"] / total * 100 if total else 0,
            "Margem": i["margem"] * 100,
            "Cancelamentos": i["cancel"] * 100,
        })
    return pd.DataFrame(linhas).sort_values("% da receita", ascending=False)


df = carregar()

# --- cabeçalho e filtros
st.title("Painel de vendas — Loja Aurora Cosméticos")
st.caption("Pedidos de 2025 · dados fictícios criados para portfólio")

canais = ["Todos"] + sorted(df["canal"].unique())
categorias = ["Todas"] + sorted(df["categoria"].unique())
c1, c2 = st.columns(2)
canal = c1.selectbox("Canal de venda", canais)
categoria = c2.selectbox("Categoria", categorias)

filtro_canal = df if canal == "Todos" else df[df["canal"] == canal]
filtro_cat = df if categoria == "Todas" else df[df["categoria"] == categoria]
d = filtro_canal if categoria == "Todas" else filtro_canal[filtro_canal["categoria"] == categoria]

# --- indicadores
ind = indicadores(d)
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Receita", brl(ind["receita"]))
k2.metric("Margem de contribuição", pct(ind["margem"]))
k3.metric("Pedidos entregues", f"{ind['entregues']:,}".replace(",", "."))
k4.metric("Ticket médio", brl(ind["ticket"]))
k5.metric("Cancelamentos", pct(ind["cancel"]))

# --- série mensal
linhas = []
for m in range(1, 13):
    i = indicadores(d[d["mes"] == m])
    linhas.append({"mes": MESES[m - 1], "receita": i["receita"],
                   "margem": i["margem"] if i["receita"] else None})
mensal = pd.DataFrame(linhas)

com_receita = mensal[mensal["receita"] > 0]
if len(com_receita) > 1:
    pico = com_receita.loc[com_receita["receita"].idxmax()]
    baixo = com_receita.loc[com_receita["margem"].idxmin()]
    st.info(f"Maior receita em {pico['mes']} ({brl(pico['receita'])}). "
            f"A menor margem foi em {baixo['mes']}, com {pct(baixo['margem'])}.")
else:
    st.info("Sem dados para esta combinação de filtros.")

st.subheader("Receita e margem por mês")
base = alt.Chart(mensal).encode(x=alt.X("mes:N", sort=MESES, title=None))
barras = base.mark_bar(color="#7fc6cb").encode(
    y=alt.Y("receita:Q", title="Receita (R$)"),
    tooltip=["mes", alt.Tooltip("receita:Q", format=",.0f")])
linha = base.mark_line(color="#e0902a", point=True).encode(
    y=alt.Y("margem:Q", title="Margem", axis=alt.Axis(format="%"),
            scale=alt.Scale(domain=[0, 0.7])),
    tooltip=["mes", alt.Tooltip("margem:Q", format=".1%")])
st.altair_chart(alt.layer(barras, linha).resolve_scale(y="independent")
                .properties(width="container", height=320))

# --- tabelas por canal e categoria
cfg = {
    "% da receita": st.column_config.ProgressColumn("% da receita", format="%.1f%%",
                                                    min_value=0, max_value=100),
    "Margem": st.column_config.NumberColumn("Margem", format="%.1f%%"),
    "Cancelamentos": st.column_config.NumberColumn("Cancelamentos", format="%.1f%%"),
}
t1, t2 = st.columns(2)
with t1:
    st.subheader("Por canal")
    st.dataframe(tabela(filtro_cat, "canal"), hide_index=True, column_config=cfg)
with t2:
    st.subheader("Por categoria")
    st.dataframe(tabela(filtro_canal, "categoria"), hide_index=True, column_config=cfg)

st.caption("Margem de contribuição = receita menos custo do produto e taxa do canal; "
           "não inclui frete, impostos nem custos fixos. Cancelamento = pedidos cancelados "
           "sobre o total de pedidos. Receita considera só pedidos entregues.")
