from flask import Flask, render_template, request, jsonify
import pandas as pd

app = Flask(__name__)

# ================== CONFIGURAÇÕES FIXAS ==================
IMPOSTO = 0.191  # 19,1%

TARIFAS = {
    "Clássico": 0.115,
    "Premium": 0.165
}

# Taxa fixa para produtos abaixo de 79,00
TAXA_FIXA = [
    (12.50, 29.00, 6.25),
    (29.00, 50.00, 6.50),
    (50.00, 79.00, 6.75)
]

# Tabela de frete (produtos com frete grátis, >=79)
FRETE = [
    (0.3, [11.97, 13.97, 15.96, 17.96, 19.95]),
    (0.5, [12.87, 15.02, 17.16, 19.31, 21.45]),
    (1.0, [13.47, 15.72, 17.96, 20.21, 22.45]),
    (2.0, [14.07, 16.42, 18.76, 21.11, 23.45]),
    (3.0, [14.97, 17.47, 19.96, 22.46, 24.95]),
    (4.0, [17.87, 19.97, 21.56, 24.26, 26.95]),
    (5.0, [20.47, 22.47, 22.76, 25.61, 28.45]),
    (9.0, [22.76, 24.97, 24.76, 27.46, 44.45]),
    (13.0, [None, None, None, None, 65.95]),
    (17.0, [None, None, None, None, 73.45]),
    (23.0, [None, None, None, None, 85.95]),
    (30.0, [None, None, None, None, 98.95]),
    (40.0, [None, None, None, None, 101.95]),
]

FAIXAS_PRECO = [
    (79, 99.99),
    (100, 118.99),
    (120, 149.99),
    (150, 199.99),
    (200, 999999)
]


# ================== FUNÇÕES AUXILIARES ==================
def obter_frete(preco, peso):
    """Retorna o valor do frete com base no preço e peso."""
    faixa_idx = None
    for i, (min_p, max_p) in enumerate(FAIXAS_PRECO):
        if min_p <= preco <= max_p:
            faixa_idx = i
            break
    if faixa_idx is None:
        return 0.0

    for limite_peso, valores in FRETE:
        if peso <= limite_peso:
            return valores[faixa_idx] if valores[faixa_idx] else 0.0
    return 0.0


def obter_taxa_fixa(preco):
    """Retorna a taxa fixa conforme a faixa de preço."""
    for min_p, max_p, taxa in TAXA_FIXA:
        if min_p <= preco <= max_p:
            return taxa
    return 0.0


# ================== FUNÇÃO PRINCIPAL ==================
def calcular_preco(sku, preco_site, acrescimo, tipo_anuncio, desconto, quantidade):
    produtos = pd.read_excel("produtos.xlsx")
    produtos.columns = produtos.columns.str.strip()
    produtos['SKU'] = produtos['SKU'].astype(str).str.strip()

    sku_input = str(sku).strip()
    produto = produtos.loc[produtos['SKU'] == sku_input]

    if produto.empty:
        return {"erro": "SKU não encontrado na planilha"}

    custo_unitario = float(produto['custo'].values[0])
    peso_unitario = float(produto['peso'].values[0])

    # Multiplica custo e peso pela quantidade no kit
    custo = custo_unitario * quantidade
    peso = peso_unitario * quantidade

    preco_site = float(preco_site)
    acrescimo = float(acrescimo)
    desconto = float(desconto) if desconto else 0.0

    preco_ml = preco_site * (1 + acrescimo / 100)       # preço base no ML
    preco_com_desconto = preco_ml * (1 - desconto / 100)  # preço com desconto aplicado

    # Frete e taxa fixa baseiam-se no preço sem desconto
    if preco_ml >= 79:
        frete = obter_frete(preco_ml, peso)
        taxa_fixa = 0
    else:
        frete = 0
        taxa_fixa = obter_taxa_fixa(preco_ml)

    # Tarifa e imposto baseados no preço com desconto
    tarifa = preco_com_desconto * TARIFAS.get(tipo_anuncio, 0.15)
    imposto = preco_com_desconto * IMPOSTO

    total_custos = custo + tarifa + imposto + frete + taxa_fixa
    lucro = preco_com_desconto - total_custos

    margem = round((lucro / preco_com_desconto) * 100, 2)
    markup = round((preco_com_desconto / custo) * 100, 2)

    return {
        "Preço_ML": round(preco_ml, 2),
        "Preço_com_Desconto": round(preco_com_desconto, 2),
        "Lucro": round(lucro, 2),
        "Margem": margem,
        "Markup": markup,
        "Tarifa": round(tarifa, 2),
        "Imposto": round(imposto, 2),
        "Frete": round(frete, 2),
        "Taxa_Fixa": round(taxa_fixa, 2)
    }


# ================== ROTAS ==================
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/produto/<sku>')
def produto(sku):
    produtos = pd.read_excel("produtos.xlsx")
    produtos.columns = produtos.columns.str.strip()
    produtos['SKU'] = produtos['SKU'].astype(str).str.strip()

    produto = produtos.loc[produtos['SKU'] == sku.strip()]
    if produto.empty:
        return jsonify({"erro": "Produto não encontrado"}), 404

    colunas_nome = [c for c in produtos.columns if c.lower() in ["nome", "produto", "descrição", "descricao", "titulo", "título"]]
    nome = str(produto[colunas_nome[0]].values[0]) if colunas_nome else "Nome não disponível"
    return jsonify({"nome": nome})


@app.route('/calcular', methods=['POST'])
def calcular():
    data = request.json
    resultado = calcular_preco(
        sku=data['sku'],
        preco_site=float(data['preco_site']),
        acrescimo=float(data['acrescimo']),
        tipo_anuncio=data['tipo_anuncio'],
        desconto=float(data.get('desconto', 0)),
        quantidade=int(data.get('quantidade', 1))  # NOVO CAMPO
    )
    return jsonify(resultado)


if __name__ == '__main__':
    app.run(debug=True)
