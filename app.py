from flask import Flask, request, render_template
import requests
import pandas as pd
import math

app = Flask(__name__)

# --- CONVERSÃO UTM → LAT/LON MANUAL ---
def utm_to_latlon(x, y, zone=22, southern_hemisphere=True):
    a = 6378137.0
    e = 0.081819191
    e1sq = 0.006739497
    k0 = 0.9996

    x -= 500000.0
    if southern_hemisphere:
        y -= 10000000.0

    m = y / k0
    mu = m / (a * (1.0 - (e ** 2) / 4.0 - 3 * (e ** 4) / 64.0 - 5 * (e ** 6) / 256.0))

    e1 = (1 - math.sqrt(1 - e ** 2)) / (1 + math.sqrt(1 - e ** 2))
    j1 = (3 * e1 / 2 - 27 * (e1 ** 3) / 32.0)
    j2 = (21 * (e1 ** 2) / 16 - 55 * (e1 ** 4) / 32.0)
    j3 = (151 * (e1 ** 3) / 96.0)
    j4 = (1097 * (e1 ** 4) / 512.0)

    fp = mu + j1 * math.sin(2 * mu) + j2 * math.sin(4 * mu) + j3 * math.sin(6 * mu) + j4 * math.sin(8 * mu)

    c1 = e1sq * math.cos(fp) ** 2
    t1 = math.tan(fp) ** 2
    r1 = a * (1 - e ** 2) / ((1 - (e * math.sin(fp)) ** 2) ** 1.5)
    n1 = a / math.sqrt(1 - (e * math.sin(fp)) ** 2)

    d = x / (n1 * k0)

    lat = fp - (n1 * math.tan(fp) / r1) * (
        (d ** 2) / 2 - (5 + 3 * t1 + 10 * c1 - 4 * c1 ** 2 - 9 * e1sq) * d ** 4 / 24 +
        (61 + 90 * t1 + 298 * c1 + 45 * t1 ** 2 - 252 * e1sq - 3 * c1 ** 2) * d ** 6 / 720)

    lon = (d - (1 + 2 * t1 + c1) * d ** 3 / 6 +
           (5 - 2 * c1 + 28 * t1 - 3 * c1 ** 2 + 8 * e1sq + 24 * t1 ** 2) * d ** 5 / 120) / math.cos(fp)

    lat = math.degrees(lat)
    lon = math.degrees(lon) + (zone * 6 - 183)
    return lat, lon

# --- ZONEAMENTO DATA ---
zoneamento_data = [
    ["ZR1", 1.5, 0.50, 0.30, 3, "5 m", "360 m²", "12 m"],
    ["ZR2", 1.0, 0.50, 0.30, 2, "5 m", "360 m²", "12 m"],
    ["ZR3", 1.0, 0.50, 0.30, 2, "5 m", "360 m²", "12 m"],
    ["ZR4", 1.0, 0.50, 0.30, 2, "5 m", "360 m²", "12 m"],
    ["ZR5", 1.0, 0.50, 0.30, 2, "5 m", "360 m²", "12 m"],
    ["ZUM", 2.0, 0.70, 0.20, 6, "5 m", "300 m²", "12 m"],
    ["ZC", 3.0, 0.80, 0.15, 8, "5 m", "300 m²", "12 m"],
    ["ZPI", 2.5, 0.60, 0.25, 6, "10 m", "1.000 m²", "20 m"],
    ["ZOE", 1.0, 0.50, 0.30, 3, "5 m", "500 m²", "15 m"],
    ["ZPDS", 0.5, 0.20, 0.50, 2, "10 m", "2.000 m²", "30 m"]
]

zoneamento_df = pd.DataFrame(zoneamento_data, columns=[
    "Zona", "Coeficiente_Aproveitamento", "Taxa_Ocupacao", "Taxa_Perm",
    "Altura_Max_Pav", "Recuo_Min", "Area_Min_Lote", "Testada_Min"
])

def get_lote_info(indicacao_fiscal):
    url = "https://geocuritiba.ippuc.org.br/server/rest/services/GeoCuritiba/Publico_GeoCuritiba_MapaCadastral/MapServer/15/query"
    params = {
        "where": f"gtm_ind_fiscal = '{indicacao_fiscal}'",
        "outFields": "*",
        "f": "json"
    }
    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        if data and "features" in data and data["features"]:
            return data["features"][0]["attributes"]
    except:
        pass
    return None

def get_lote_info_extra(indicacao_fiscal):
    url = "https://geocuritiba.ippuc.org.br/server/rest/services/GeoCuritiba/Publico_GeoCuritiba_MapaCadastral/MapServer/20/query"
    params = {
        "where": f"gtm_ind_fiscal = '{indicacao_fiscal}'",
        "outFields": "*",
        "f": "json"
    }
    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        if data and "features" in data:
            return [f["attributes"] for f in data["features"]]
    except:
        pass
    return []

@app.route("/", methods=["GET", "POST"])
def index():
    tabela = None
    mensagem = None
    lat = None
    lon = None
    html_calc = ""
    html_lote = ""
    html_extra = ""

    if request.method == "POST":
        indicacao_fiscal = request.form.get("indicacao_fiscal")
        lote_info = get_lote_info(indicacao_fiscal)
        lote_extra = get_lote_info_extra(indicacao_fiscal)

        if lote_info and "x_coord" in lote_info and "y_coord" in lote_info:
            try:
                x = float(lote_info["x_coord"])
                y = float(lote_info["y_coord"])
                lat, lon = utm_to_latlon(x, y)
            except Exception as e:
                print("Erro na conversão:", e)

        if lote_info:
            zona = lote_info.get("gtm_sigla_zoneamento", "").strip()
            area_terreno = lote_info.get("gtm_mtr_area_terreno", 0)
            try:
                area_terreno = float(area_terreno)
            except:
                area_terreno = 0

            df_lote = pd.DataFrame(lote_info.items(), columns=["Campo", "Valor"])
            html_lote = df_lote.to_html(classes="table table-sm table-bordered", index=False, justify="left", border=0)

            parametros = zoneamento_df[zoneamento_df["Zona"] == zona]

            if not parametros.empty and area_terreno > 0:
                coef = parametros.iloc[0]["Coeficiente_Aproveitamento"]
                taxa_ocup = parametros.iloc[0]["Taxa_Ocupacao"]
                taxa_perm = parametros.iloc[0]["Taxa_Perm"]
                altura_max = parametros.iloc[0]["Altura_Max_Pav"]
                recuo_min = parametros.iloc[0]["Recuo_Min"]
                area_min_lote = parametros.iloc[0]["Area_Min_Lote"]
                testada_min = parametros.iloc[0]["Testada_Min"]

                area_max_construida = area_terreno * coef
                area_max_ocupada = area_terreno * taxa_ocup
                area_min_permeavel = area_terreno * taxa_perm

                calculos = {
                    "Zona": zona,
                    "Área do Lote (m²)": f"{area_terreno:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " m²",
                    "Coef. de Aproveitamento": coef,
                    "Taxa de Ocupação": f"{taxa_ocup * 100:.0f}%",
                    "Taxa de Permeabilidade": f"{taxa_perm * 100:.0f}%",
                    "Altura Máxima (Pavimentos)": f"{altura_max} pavimentos",
                    "Área Máx. Construída (m²)": f"{area_max_construida:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " m²",
                    "Área Máx. Ocupada (m²)": f"{area_max_ocupada:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " m²",
                    "Área Mín. Permeável (m²)": f"{area_min_permeavel:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " m²",
                    "Recuo Mínimo": recuo_min,
                    "Área Mínima do Lote": area_min_lote,
                    "Testada Mínima": testada_min
                }

                df_calc = pd.DataFrame(calculos.items(), columns=["Item", "Valor"])
                html_calc = df_calc.to_html(classes="table table-sm table-bordered", justify="left", index=False, border=0, table_id="A")
            else:
                html_lote += f"<div class='alert alert-warning'>Zona '{zona}' não reconhecida ou área inválida.</div>"
        else:
            mensagem = "Nenhuma informação encontrada na Camada 15 para a indicação fiscal fornecida."

        if lote_extra:
            html_extra = "<h4>Dados Complementares (Camada 20)</h4>"
            for i, item in enumerate(lote_extra, start=1):
                df = pd.DataFrame(item.items(), columns=["Campo", "Valor"])
                html_extra += f"<h5>Registro {i}</h5>" + df.to_html(classes="table table-sm table-bordered", index=False, border=0)

    return render_template("index.html", html_calc=html_calc,
                           html_lote=html_lote,
                           html_extra=html_extra,
                           mensagem=mensagem,
                           lat=lat,
                           lon=lon)

if __name__ == "__main__":
    app.run(debug=True)
