"""
Utilidades de visualización del SIG-Hospital.

Provee una función por cada tipo de gráfica requerido por el sistema:
barras, líneas, pastel, dona, dispersión, histograma, boxplot, mapa de
calor y área. Cada tipo tiene asignado su propio color/escala para que
todas las gráficas del sistema sean visualmente distinguibles entre sí.
"""
import colorsys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------
# Un color propio por tipo de gráfica (no se repiten entre sí)
# ----------------------------------------------------------------------
PALETA = {
    "barras": "#1D6A6A",       # verde-azulado profundo
    "lineas": "#3B82C4",       # azul acero
    "pastel": "#E8A33D",       # ámbar
    "dona": "#9B5DE5",         # violeta
    "dispersion": "#F15BB5",   # magenta/rosa
    "histograma": "#37A169",   # verde jade
    "boxplot": "#F3722C",      # naranja
    "mapa_calor": "#118AB2",   # azul cian (escala)
    "area": "#06D6A0",         # turquesa
}
ESCALA_MAPA_CALOR = "Teal"
FUENTE = "Inter, -apple-system, sans-serif"

NOMBRES = {
    "barras": "Gráfica de barras",
    "lineas": "Gráfica de líneas",
    "pastel": "Gráfica de pastel",
    "dona": "Gráfica de dona",
    "dispersion": "Gráfica de dispersión",
    "histograma": "Histograma",
    "boxplot": "Diagrama de caja (boxplot)",
    "mapa_calor": "Mapa de calor",
    "area": "Gráfica de área",
}


def chip(tipo):
    """Etiqueta de color que identifica el tipo de gráfica sobre el subtítulo."""
    color = PALETA.get(tipo, "#0B5566")
    st.markdown(
        f'<span style="display:inline-block;background:{color}1A;color:{color};'
        f'border:1px solid {color}55;padding:2px 12px;border-radius:999px;'
        f'font-size:0.72rem;font-weight:700;letter-spacing:.02em;'
        f'font-family:{FUENTE};text-transform:uppercase;margin-bottom:6px;">'
        f'{NOMBRES.get(tipo, tipo)}</span>',
        unsafe_allow_html=True,
    )


def _hex_a_rgba(hex_color, alpha=0.35):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def _tonos(hex_color, n):
    """Genera n variaciones (claro -> oscuro) de un mismo color, para pastel/dona."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    n = max(n, 1)
    tonos = []
    for i in range(n):
        li = max(0.30, min(0.80, l + (i - n / 2) * 0.075))
        rr, gg, bb = colorsys.hls_to_rgb(h, li, min(s + 0.05, 1))
        tonos.append(f"rgb({int(rr * 255)},{int(gg * 255)},{int(bb * 255)})")
    return tonos


def _layout_base(fig, titulo=None, altura=380):
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=14)) if titulo else None,
        font=dict(family=FUENTE, size=12.5, color="#152426"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=44 if titulo else 30, b=10),
        height=altura,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#E7EEED", zeroline=False)
    return fig


# ----------------------------------------------------------------------
# 1) BARRAS
# ----------------------------------------------------------------------
def barras(serie, titulo=None, horizontal=False, top_n=None, color=None):
    color = color or PALETA["barras"]
    s = serie.dropna()
    if top_n:
        s = s.sort_values(ascending=False).head(top_n)
    s = s.sort_values(ascending=horizontal)
    if horizontal:
        fig = px.bar(x=s.values, y=s.index.astype(str), orientation="h", text=s.values)
        fig.update_traces(textposition="outside")
    else:
        fig = px.bar(x=s.index.astype(str), y=s.values, text=s.values)
        fig.update_traces(textposition="outside")
    fig.update_traces(marker_color=color, marker_line_width=0, texttemplate="%{text:,.0f}")
    fig.update_xaxes(title=None)
    fig.update_yaxes(title=None)
    return _layout_base(fig, titulo)


# ----------------------------------------------------------------------
# 2) LÍNEAS
# ----------------------------------------------------------------------
def lineas(serie, titulo=None, color=None, sufijo_y=None):
    color = color or PALETA["lineas"]
    fig = go.Figure(go.Scatter(
        x=serie.index.astype(str), y=serie.values, mode="lines+markers+text",
        line=dict(color=color, width=3), marker=dict(size=7, color=color),
        text=serie.values, texttemplate="%{text:,.0f}" + (sufijo_y or ""),
        textposition="top center",
        fill="tozeroy", fillcolor=_hex_a_rgba(color, 0.10),
    ))
    if sufijo_y:
        fig.update_yaxes(ticksuffix=sufijo_y)
    return _layout_base(fig, titulo)


# ----------------------------------------------------------------------
# 3) PASTEL
# ----------------------------------------------------------------------
def pastel(labels, values, titulo=None):
    fig = go.Figure(go.Pie(labels=list(labels), values=list(values), hole=0.0,
                            marker=dict(colors=_tonos(PALETA["pastel"], len(list(labels)))),
                            textinfo="label+value+percent"))
    return _layout_base(fig, titulo, altura=420)


# ----------------------------------------------------------------------
# 4) DONA
# ----------------------------------------------------------------------
def dona(labels, values, titulo=None, texto_centro=None):
    fig = go.Figure(go.Pie(labels=list(labels), values=list(values), hole=0.58,
                            marker=dict(colors=_tonos(PALETA["dona"], len(list(labels)))),
                            textinfo="label+value+percent"))
    if texto_centro:
        fig.add_annotation(text=texto_centro, showarrow=False, font=dict(size=16, color=PALETA["dona"]))
    return _layout_base(fig, titulo, altura=420)


# ----------------------------------------------------------------------
# 5) DISPERSIÓN
# ----------------------------------------------------------------------
def dispersion(df, x, y, color_col=None, size_col=None, titulo=None, etiquetas=None):
    if color_col:
        fig = px.scatter(df, x=x, y=y, color=color_col, size=size_col, hover_name=etiquetas,
                          color_discrete_sequence=px.colors.qualitative.Bold)
    else:
        fig = px.scatter(df, x=x, y=y, size=size_col, hover_name=etiquetas)
        fig.update_traces(marker_color=PALETA["dispersion"])
    fig.update_traces(marker=dict(line=dict(width=0.6, color="white"), opacity=0.85, sizemin=6))
    return _layout_base(fig, titulo)


# ----------------------------------------------------------------------
# 6) HISTOGRAMA
# ----------------------------------------------------------------------
def histograma(datos, titulo=None, nbins=None, color=None):
    color = color or PALETA["histograma"]
    fig = px.histogram(x=list(datos), nbins=nbins)
    fig.update_traces(marker_color=color, marker_line_width=0.6, marker_line_color="white",
                       texttemplate="%{y:,.0f}", textposition="outside")
    fig.update_xaxes(title=None)
    fig.update_yaxes(title="Frecuencia")
    return _layout_base(fig, titulo)


# ----------------------------------------------------------------------
# 7) BOXPLOT
# ----------------------------------------------------------------------
def boxplot(df, x_col, y_col, titulo=None, color=None):
    color = color or PALETA["boxplot"]
    fig = px.box(df, x=x_col, y=y_col, points="outliers")
    fig.update_traces(marker_color=color, line_color=color, boxmean=True)
    fig.update_xaxes(title=None)
    return _layout_base(fig, titulo)


# ----------------------------------------------------------------------
# 8) MAPA DE CALOR
# ----------------------------------------------------------------------
def mapa_calor(tabla_2d, titulo=None):
    fig = go.Figure(go.Heatmap(
        z=tabla_2d.values,
        x=[str(c) for c in tabla_2d.columns],
        y=[str(i) for i in tabla_2d.index],
        colorscale=ESCALA_MAPA_CALOR,
        text=tabla_2d.values, texttemplate="%{text}",
        hoverongaps=False, showscale=True,
    ))
    return _layout_base(fig, titulo, altura=340)


# ----------------------------------------------------------------------
# 9) ÁREA
# ----------------------------------------------------------------------
def area(serie, titulo=None, color=None, sufijo_y=None):
    color = color or PALETA["area"]
    fig = go.Figure(go.Scatter(
        x=serie.index.astype(str), y=serie.values, mode="lines+markers+text",
        line=dict(color=color, width=2.5), fill="tozeroy", fillcolor=_hex_a_rgba(color, 0.40),
        marker=dict(size=6, color=color),
        text=serie.values, texttemplate="%{text:,.1f}" + (sufijo_y or ""),
        textposition="top center",
    ))
    if sufijo_y:
        fig.update_yaxes(ticksuffix=sufijo_y)
    return _layout_base(fig, titulo)
