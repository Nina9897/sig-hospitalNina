"""
Tema visual del SIG-Hospital.

Centraliza la identidad visual del sistema (colores, tipografías y estilos
de los componentes de Streamlit) para que todo el sistema —no solo las
gráficas— tenga un diseño coherente, clínico y moderno.
"""
import streamlit as st

# ----------------------------------------------------------------------
# Paleta de marca (identidad general del sistema)
# ----------------------------------------------------------------------
MARCA = {
    "primario": "#0B5566",       # azul-petróleo clínico (sidebar, encabezados)
    "primario_oscuro": "#062E36",
    "primario_claro": "#0E7086",
    "secundario": "#2FA8A0",     # verde-azulado (acentos, botones)
    "secundario_claro": "#5FCFC3",
    "fondo": "#F3F7F6",          # gris-lino muy claro
    "superficie": "#FFFFFF",
    "tinta": "#152426",
    "tinta_suave": "#5B6B6E",
    "borde": "#E1EAE9",
    "alerta": "#E4572E",
    "exito": "#2E8B57",
    "advertencia": "#E8A33D",
    "info": "#3B82C4",
}

FUENTE_TITULOS = "Sora"
FUENTE_TEXTO = "Inter"

# Colores de apoyo para badges de estado, reutilizables en cualquier módulo.
COLORES_ESTADO = {
    "Confirmada": "#2E8B57", "Completada": "#2E8B57", "Activo": "#2E8B57",
    "Alta": "#2E8B57", "Pagado": "#2E8B57", "Disponible": "#2E8B57",
    "Pendiente": "#E8A33D", "En espera": "#E8A33D", "Ocupada": "#E8A33D",
    "Cancelada": "#E4572E", "No Asistió": "#E4572E", "Vencido": "#E4572E",
    "Inactivo": "#E4572E", "Mantenimiento": "#E4572E",
    "Hospitalizado": "#3B82C4", "En proceso": "#3B82C4",
}


def aplicar():
    """Inyecta el CSS global del sistema. Llamar una vez desde app.py."""
    m = MARCA
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800'
                    '&family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {{
            font-family: '{FUENTE_TEXTO}', -apple-system, sans-serif;
        }}
        .stApp {{
            background:
                radial-gradient(1200px 500px at 100% -10%, {m['secundario']}14, transparent),
                {m['fondo']};
        }}
        .block-container {{
            padding-top: 2rem;
            max-width: 1200px;
        }}
        h1, h2, h3 {{
            font-family: '{FUENTE_TITULOS}', sans-serif !important;
            color: {m['primario']} !important;
            letter-spacing: -0.01em;
        }}
        h1 {{ font-weight: 800 !important; }}
        h2, h3 {{ font-weight: 700 !important; }}
        h4 {{ color: {m['tinta']} !important; font-weight: 700 !important; }}
        [data-testid="stCaptionContainer"] {{ color: {m['tinta_suave']} !important; }}

        /* Franja decorativa superior de Streamlit -> degradado de marca */
        div[data-testid="stDecoration"] {{
            background: linear-gradient(90deg, {m['primario']}, {m['secundario']});
        }}
        header[data-testid="stHeader"] {{
            background: rgba(255,255,255,0.0);
        }}

        /* --- Barra lateral --- */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {m['primario']} 0%, {m['primario_oscuro']} 100%);
        }}
        section[data-testid="stSidebar"] > div {{
            padding-top: 1.1rem;
        }}
        section[data-testid="stSidebar"] * {{
            color: #EAF6F4 !important;
        }}
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {{
            color: #FFFFFF !important;
        }}

        /* Navegación tipo "botón" para el st.radio del menú principal */
        section[data-testid="stSidebar"] div[role="radiogroup"] {{
            gap: 3px;
        }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label {{
            padding: 9px 12px;
            border-radius: 10px;
            transition: background 0.15s ease;
            width: 100%;
        }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
            background: rgba(255,255,255,0.12);
        }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
            background: rgba(255,255,255,0.16);
            box-shadow: inset 3px 0 0 {m['secundario_claro']};
        }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label p {{
            font-weight: 600;
            font-size: 0.94rem;
        }}
        section[data-testid="stSidebar"] hr {{
            border-color: rgba(255,255,255,0.18);
            margin: 1.1rem 0;
        }}
        .sidebar-marca {{
            padding: 2px 4px 14px 4px;
            border-bottom: 1px solid rgba(255,255,255,0.15);
            margin-bottom: 10px;
        }}
        .sidebar-marca .texto b {{
            display: block; font-family: '{FUENTE_TITULOS}', sans-serif;
            font-size: 1.08rem; font-weight: 800; color: #fff !important;
            letter-spacing: -0.01em;
        }}
        .sidebar-marca .texto span {{
            display: block; font-size: 0.72rem; color: #C6E6E1 !important;
            font-weight: 500;
        }}
        .sidebar-pie {{
            font-size: 0.72rem; color: #B9DAD5 !important; line-height: 1.5;
            padding-top: 4px;
        }}

        /* --- Tarjetas de métricas (st.metric) --- */
        div[data-testid="stMetric"] {{
            background: {m['superficie']};
            border: 1px solid {m['borde']};
            border-top: 4px solid {m['secundario']};
            border-radius: 14px;
            padding: 0.9rem 1.1rem 0.7rem 1.1rem;
            box-shadow: 0 2px 10px rgba(11, 85, 102, 0.06);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }}
        div[data-testid="stMetric"]:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(11, 85, 102, 0.12);
        }}
        div[data-testid="stMetricLabel"] {{
            color: {m['tinta_suave']} !important;
            font-weight: 600;
        }}
        div[data-testid="stMetricValue"] {{
            color: {m['primario']} !important;
            font-family: '{FUENTE_TITULOS}', sans-serif;
        }}

        /* --- Botones --- */
        button[kind="primary"], .stDownloadButton button {{
            background: linear-gradient(135deg, {m['primario']}, {m['secundario']}) !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            box-shadow: 0 2px 8px rgba(11, 85, 102, 0.18);
            transition: filter 0.15s ease, transform 0.1s ease;
        }}
        button[kind="primary"]:hover {{
            filter: brightness(1.08);
            transform: translateY(-1px);
        }}
        button[kind="secondary"] {{
            border-radius: 10px !important;
            border-color: {m['borde']} !important;
            font-weight: 600 !important;
        }}

        /* --- Inputs, selects, textarea --- */
        .stTextInput input, .stNumberInput input, .stDateInput input,
        .stTextArea textarea, div[data-baseweb="select"] > div {{
            border-radius: 9px !important;
            border-color: {m['borde']} !important;
        }}
        .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {{
            border-color: {m['secundario']} !important;
            box-shadow: 0 0 0 1px {m['secundario']} !important;
        }}

        /* --- Pestañas (tabs) --- */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 4px;
            border-bottom: 2px solid {m['borde']};
        }}
        .stTabs [data-baseweb="tab"] {{
            border-radius: 10px 10px 0 0;
            padding: 8px 16px;
            color: {m['tinta_suave']};
            font-weight: 600;
        }}
        .stTabs [aria-selected="true"] {{
            background: {m['primario']}14;
            color: {m['primario']} !important;
        }}

        /* --- Contenedores generales / expander / formularios --- */
        div[data-testid="stExpander"], div[data-testid="stForm"] {{
            border: 1px solid {m['borde']};
            border-radius: 14px;
            background: {m['superficie']};
        }}
        div[data-testid="stExpander"] summary {{
            font-weight: 600;
        }}

        hr {{
            border-top: 1px solid {m['borde']};
            margin: 1.6rem 0;
        }}

        /* --- Tablas --- */
        div[data-testid="stDataFrame"] {{
            border: 1px solid {m['borde']};
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 1px 6px rgba(11, 85, 102, 0.05);
        }}

        /* --- Alertas (info / success / warning / error) --- */
        div[data-testid="stAlert"] {{
            border-radius: 12px;
            border: 1px solid transparent;
        }}

        /* --- Slider --- */
        div[data-testid="stSlider"] [role="slider"] {{
            background-color: {m['secundario']} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def sidebar_marca(titulo, subtitulo=None):
    """Bloque de identidad de marca para la parte superior del sidebar."""
    sub = f"<span>{subtitulo}</span>" if subtitulo else ""
    st.markdown(
        f"""
        <div class="sidebar-marca">
            <div class="texto"><b>{titulo}</b>{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_pie(texto):
    """Texto de pie de página del sidebar, con estilo discreto."""
    st.markdown(f'<div class="sidebar-pie">{texto}</div>', unsafe_allow_html=True)


def encabezado(titulo, subtitulo=None):
    """Encabezado de página con estilo de tarjeta/banner de marca."""
    m = MARCA
    sub = f'<div style="color:#DDEDEA;font-size:0.95rem;margin-top:3px;">{subtitulo}</div>' if subtitulo else ""
    st.markdown(
        f"""
        <div style="background: linear-gradient(120deg, {m['primario']}, {m['secundario']});
                    border-radius: 16px; padding: 1.15rem 1.5rem; margin-bottom: 1.3rem;
                    box-shadow: 0 4px 16px rgba(11,85,102,0.18);
                    border-left: 6px solid {m['secundario_claro']};">
            <div style="color:white; font-family:'{FUENTE_TITULOS}',sans-serif;
                        font-size:1.55rem; font-weight:800;">{titulo}</div>
            {sub}
        </div>
        """,
        unsafe_allow_html=True,
    )


def tarjeta_modulo(titulo, descripcion):
    """HTML de una tarjeta de módulo para el grid de la página de inicio."""
    m = MARCA
    return f"""
    <div style="background:{m['superficie']}; border:1px solid {m['borde']};
                border-left:4px solid {m['secundario']}; border-radius:14px;
                padding:16px 18px; height:100%; box-shadow:0 2px 8px rgba(11,85,102,0.05);">
        <div style="font-family:'{FUENTE_TITULOS}',sans-serif; font-weight:700;
                    color:{m['primario']}; font-size:1rem; margin-bottom:3px;">{titulo}</div>
        <div style="color:{m['tinta_suave']}; font-size:0.85rem; line-height:1.4;">{descripcion}</div>
    </div>
    """


def aviso_en_uso(dependientes, accion="eliminar"):
    """Muestra un st.error legible cuando un registro no se puede eliminar
    por tener información relacionada en otras tablas (integridad
    referencial). 'dependientes' es el dict que devuelve
    storage.referencias_activas()."""
    etiquetas = {
        "citas": "cita(s)", "consultas": "consulta(s)", "tratamientos": "tratamiento(s)",
        "hospitalizaciones": "hospitalización(es)", "medicos": "médico(s)",
        "consultorios": "consultorio(s)", "pagos": "pago(s)",
    }
    partes = [f"{cant} {etiquetas.get(tabla, tabla)}" for tabla, cant in dependientes.items()]
    st.error(
        f"No se puede {accion} porque todavía tiene {', '.join(partes)} asociada(s). "
        "Elimina o reasigna primero esos registros relacionados."
    )


def badge(texto, color=None):
    """Devuelve el HTML de una etiqueta ('pill') de estado con color por categoría."""
    color = color or COLORES_ESTADO.get(texto, MARCA["info"])
    return (
        f'<span style="display:inline-block;background:{color}1A;color:{color};'
        f'border:1px solid {color}55;padding:2px 11px;border-radius:999px;'
        f'font-size:0.78rem;font-weight:700;font-family:{FUENTE_TEXTO},sans-serif;">'
        f'{texto}</span>'
    )
