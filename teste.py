import pandas as pd

# Lê a planilha
produtos = pd.read_excel("produtos.xlsx")

# Mostra todas as colunas para conferir
print(produtos.columns)

# Padroniza colunas e valores
produtos.columns = produtos.columns.str.strip()  # remove espaços nos nomes das colunas
produtos['SKU'] = produtos['SKU'].astype(str).str.strip()  # garante que todos os SKUs sejam strings

# Pega o primeiro SKU
primeiro_sku = produtos['SKU'].iloc[0]
print("Primeiro SKU:", primeiro_sku)

# Pega o nome do primeiro produto
primeiro_nome = produtos['nome'].iloc[0]
print("Nome do primeiro produto:", primeiro_nome)

# Pega o custo e peso
custo = float(produtos['custo'].iloc[0])
peso = float(produtos['peso'].iloc[0])
print("custo:", custo, "| peso:", peso)
