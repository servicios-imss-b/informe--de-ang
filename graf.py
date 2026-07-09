import pandas as pd
import os 
usuario = os.getlogin() 
base = pd.read_excel(fr"C:\Users\{usuario}\Downloads\nuevo-f\formulario-ang\bases\UnidadesIMB_CS!_v2.xlsx",sheet_name="Sheet 1")
clues = pd.read_parquet(fr"C:\Users\{usuario}\IMSS-BIENESTAR\División de Procesamiento de información - Repositorio de Datos\CLUES\clues.parquet")
import pandas as pd

sheet_id = "1maRNGDuU9rEFWZLgMdhJS1waAnJxl6ENntm-nyD0tq8"
gid = "1765182479"

url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

base_an = pd.read_csv(url)

col = ["clues_imb"]
base = base[col]
base = base.merge(
    clues[["clues_imb", "entidad",'nombre_de_la_unidad']],
    on="clues_imb",
    how="left"
)
colum =['clues_imb', 'entidad','consultorio','pregunta','nombre_de_la_unidad']
base_an = base_an[colum]    
b = pd.read_excel(fr"C:\Users\{usuario}\Downloads\nuevo-f\formulario-ang\bases\UM_IMB_SUS.xlsx",sheet_name="Hoja2")
b = b.drop(index=[0, 2, 5,3,1])
b = b.drop(columns=['Unnamed: 1'])
b = b.rename(columns={
   'CLUES' : 'preguntas',
})
base_an = base_an[
    ~base_an["pregunta"].str.contains("internet|turno_consultorio|consultorios_habilitados", case=False, na=False)
]
base_conteo =base["clues_imb"].unique()
base_conteo
total_unidades = base["clues_imb"].nunique()

respondieron = base_an["clues_imb"].nunique()

sin_responder = total_unidades - respondieron
base_an = base_an.drop_duplicates()
avance_general = round(respondieron / total_unidades * 100, 1)
# tablas
# TABLA 1 - AVANCE POR ENTIDAD

# Unidades esperadas
esperadas = (
    base
    .groupby("entidad")
    .size()
    .reset_index(name="esperadas")
)

# Unidades que respondieron
contestadas = (
    base_an[["entidad","clues_imb"]]
    .drop_duplicates()
    .groupby("entidad")
    .size()
    .reset_index(name="respondieron")
)

tabla_entidades = (
    esperadas
    .merge(contestadas,
           on="entidad",
           how="left")
)

tabla_entidades["respondieron"] = (
    tabla_entidades["respondieron"]
    .fillna(0)
    .astype(int)
)

tabla_entidades["porcentaje"] = (
    tabla_entidades["respondieron"]
    / tabla_entidades["esperadas"]
    *100
).round(1)

tabla_entidades = tabla_entidades.sort_values(
    "porcentaje",
    ascending=False
)
# TABLA 2 - COMPLETITUD POR UNIDAD

# Número de preguntas del formulario
n_preguntas = len(b)

# Número de consultorios por unidad
consultorios = (
    base_an
    .groupby(["clues_imb","entidad",'nombre_de_la_unidad'],as_index=False)
    ["consultorio"]
    .max()
)

consultorios.rename(
    columns={"consultorio":"consultorios"},
    inplace=True
)

# Preguntas respondidas
respondidas = (
    base_an
    .groupby(["clues_imb","entidad",'nombre_de_la_unidad'])
    .size()
    .reset_index(name="respondidas")
)

tabla_unidades = consultorios.merge(
    respondidas,
    on=["clues_imb","entidad", "nombre_de_la_unidad"]
)

tabla_unidades["esperadas"] = (
    tabla_unidades["consultorios"]
    * n_preguntas
)

tabla_unidades["porcentaje"] = (
    tabla_unidades["respondidas"]
    / tabla_unidades["esperadas"]
    *100
).round(1)

tabla_unidades = (
    tabla_unidades
    .rename(columns={"clues_imb":"clues"})
    .sort_values("porcentaje")
)
# LISTAS PARA JINJA2
entidades = tabla_entidades.to_dict(orient="records")
unidades = tabla_unidades.to_dict(orient="records")
tabla_entidades = (
    tabla_unidades
    .groupby("entidad", as_index=False)
    .agg(
        consultorios=("consultorios","sum"),
        respondidas=("respondidas","sum"),
        esperadas=("esperadas","sum"),
        unidades=("clues","count")
    )
)

tabla_entidades["porcentaje"] = (
    tabla_entidades["respondidas"]
    / tabla_entidades["esperadas"]
    *100
).round(1)

tabla_entidades = tabla_entidades.sort_values(
    "porcentaje",
    ascending=False
)
# Total de unidades por entidad (base completa)
total_por_entidad = (
    base
    .groupby("entidad")["clues_imb"]
    .nunique()
    .reset_index(name="total_unidades")
)

# Unidades que han respondido al menos una pregunta
respondieron_por_entidad = (
    base_an[["entidad", "clues_imb"]]
    .drop_duplicates()
    .groupby("entidad")["clues_imb"]
    .nunique()
    .reset_index(name="unidades_respondieron")
)

tabla_avance = total_por_entidad.merge(
    respondieron_por_entidad,
    on="entidad",
    how="left"
)

tabla_avance["unidades_respondieron"] = (
    tabla_avance["unidades_respondieron"].fillna(0).astype(int)
)

tabla_avance["porcentaje"] = (
    tabla_avance["unidades_respondieron"]
    / tabla_avance["total_unidades"]
    * 100
).round(1)

tabla_avance = tabla_avance.sort_values("porcentaje", ascending=False)
#graficas
import plotly.express as px

tabla = tabla_avance.sort_values("porcentaje", ascending=False).copy()

# Semáforo de colores
tabla["color"] = tabla["porcentaje"].apply(
    lambda p:
        "#0D5D2A" if p == 100 else
        "#88A91E" if p >= 80 else
        "#F1D54A" if p >= 50 else
        "#D41111"
)

fig = px.bar(
    tabla,
    x="entidad",
    y="porcentaje",
    text="porcentaje",
    title="Avance por entidad sobre unidades"
)

fig.update_traces(
    marker_color=tabla["color"],
    texttemplate="%{text:.1f}%",
    textposition="outside",
    hovertemplate="<b>%{x}</b><br>Avance: %{y:.1f}%<extra></extra>"
)

fig.update_yaxes(showticklabels=False)

fig.update_layout(
    xaxis_title="",
    yaxis_title="",
    template="plotly_white",
    width=1200,
    height=700
)

fig.show()
import plotly.graph_objects as go

# Ordenar de menor a mayor para efecto cascada
df_plot = tabla_entidades.sort_values("porcentaje", ascending=True)

# Semáforo de colores
colores = [
    "#0D5D2A" if p >= 95 else
    "#88A91E" if p >= 80 else
    "#F1D54A" if p >= 60 else
    "#D41111"
    for p in df_plot["porcentaje"]
]

fig_cascada = go.Figure()

fig_cascada.add_trace(
    go.Bar(
        x=df_plot["porcentaje"],
        y=df_plot["entidad"],
        orientation="h",
        marker=dict(color=colores),
        text=[f"{p:.1f}%" for p in df_plot["porcentaje"]],
        textposition="outside",
        textfont=dict(size=11),
        hovertemplate="<b>%{y}</b><br>Porcentaje: %{x:.1f}%<extra></extra>",
    )
)

fig_cascada.update_layout(
    title=dict(
        text="Gráfica de llenado de consultorios",
        x=0.5,
        font=dict(size=16)
    ),
    xaxis=dict(
        title="",
        range=[0, 115],
        ticksuffix="%",
        showgrid=True,
        gridcolor="lightgrey"
    ),
    yaxis=dict(
        title="",
        automargin=True
    ),
    plot_bgcolor="white",
    height=500,
    margin=dict(l=20, r=60, t=60, b=40)
)

fig_cascada.show()
from pathlib import Path
import json
from datetime import datetime
from plotly.utils import PlotlyJSONEncoder

base_dir = Path.cwd()
salida_data = base_dir / "data.js"
html_origen = base_dir / "reporte_interactivo.html"
index_destino = base_dir / "index.html"

figures = [
    {"id": "fig_avance", "figure": fig.to_plotly_json()},
]

if "fig_cascada" in globals():
    figures.append({"id": "fig_cascada", "figure": fig_cascada.to_plotly_json()})
else:
    print("Aviso: fig_cascada no existe todavia; se exporta solo fig_avance.")

payload = {
    "title": "Tablero IMSS Bienestar",
    "updated_at": datetime.now().isoformat(timespec="seconds"),
    "tables": {
        "tabla_avance": {
            "columns": list(tabla_avance.columns),
            "rows": tabla_avance.to_dict(orient="records"),
            "excel": "tabla_avance.xlsx",
        },
        "tabla_entidades": {
            "columns": list(tabla_entidades.columns),
            "rows": tabla_entidades.to_dict(orient="records"),
            "excel": "tabla_entidades.xlsx",
        },
        "tabla_unidades": {
            "columns": list(tabla_unidades.columns),
            "rows": tabla_unidades.to_dict(orient="records"),
            "excel": "tabla_unidades.xlsx",
        },
    },
    "figures": figures,
}

# Mantener los Excel sincronizados con los datos mostrados en el tablero.
tabla_avance.to_excel(base_dir / "tabla_avance.xlsx", index=False)
tabla_entidades.to_excel(base_dir / "tabla_entidades.xlsx", index=False)
tabla_unidades.to_excel(base_dir / "tabla_unidades.xlsx", index=False)

contenido_js = "window.DASHBOARD_DATA = " + json.dumps(payload, ensure_ascii=False, cls=PlotlyJSONEncoder) + ";\n"
salida_data.write_text(contenido_js, encoding="utf-8")

# Si no existe el HTML origen, se crea desde index.html para que lo puedas editar
if not html_origen.exists() and index_destino.exists():
    html_origen.write_text(index_destino.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Se creo plantilla HTML: {html_origen}")

# Evitar que cambios manuales en index.html se pierdan al regenerar datos.
if not index_destino.exists() and html_origen.exists():
    index_destino.write_text(html_origen.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Index creado desde: {html_origen}")
elif not html_origen.exists():
    print(f"No se encontro {html_origen.name}; index.html no se pudo crear.")
else:
    print("Index conservado sin sobrescribir.")

print(f"Datos exportados en: {salida_data}")
print("Ejecuta esta celda tras modificar graficas o HTML para refrescar el tablero.")