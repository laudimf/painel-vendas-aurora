# Painel de vendas — Loja Aurora Cosméticos

Projeto de portfólio em análise de dados. Painel interativo feito com Python e Streamlit, a partir de pedidos de um e-commerce fictício de cosméticos naturais.

**Todos os dados são fictícios.** A empresa, os clientes e os números foram criados só para demonstração.

## O que o painel mostra

- Receita, margem de contribuição, pedidos entregues, ticket médio e cancelamentos
- Receita e margem por mês
- Comparação por canal de venda e por categoria
- Filtros por canal e categoria

## Como rodar no seu computador

```
pip install -r requirements.txt
streamlit run app.py
```

## Tratamento dos dados

Remoção de pedidos duplicados e padronização do nome do canal. A margem considera receita menos custo do produto e taxa do canal, e não inclui frete, impostos nem custos fixos.

## Tecnologias

Python, pandas, Streamlit, Altair.
