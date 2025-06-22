import pandas as pd

# Dados das zonas organizados
data = [
    ["ZR1", 1.5, "50%", "30%", 3, "5 m", "360 m²", "12 m"],
    ["ZR2", 1.0, "50%", "30%", 2, "5 m", "360 m²", "12 m"],
    ["ZR3", 1.0, "50%", "30%", 2, "5 m", "360 m²", "12 m"],
    ["ZR4", 1.0, "50%", "30%", 2, "5 m", "360 m²", "12 m"],
    ["ZR5", 1.0, "50%", "30%", 2, "5 m", "360 m²", "12 m"],
    ["ZUM", 2.0, "70%", "20%", 6, "5 m", "300 m²", "12 m"],
    ["ZC", 3.0, "80%", "15%", 8, "5 m", "300 m²", "12 m"],
    ["ZPI", 2.5, "60%", "25%", 6, "10 m", "1.000 m²", "20 m"],
    ["ZOE", 1.0, "50%", "30%", 3, "5 m", "500 m²", "15 m"],
    ["ZPDS", 0.5, "20%", "50%", 2, "10 m", "2.000 m²", "30 m"]
]

# Criar DataFrame
columns = ["Zona", "Coef. Máx.", "Ocupação Máx.", "Permeabilidade Mín.", "Altura Máx. (Pav.)", "Recuo Mín.", "Área Mín. do Lote", "Testada Mín."]
df = pd.DataFrame(data, columns=columns)

# Exportar para CSV
df.to_csv("parametros_zoneamento_curitiba.csv", index=False)
