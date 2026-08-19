import streamlit as st

from utils import storage as db
from utils import seed_data
from utils import theme
from modules import pacientes, medicos, citas, consultas, diagnosticos, tratamientos, hospitalizacion, reportes

st.set_page_config(
    page_title="SIG-Hospital",
    layout="wide",
    initial_sidebar_state="expanded",
)

theme.aplicar()

# Inicializa la "base de datos" en archivos CSV y siembra información de
# ejemplo la primera vez que se ejecuta la aplicación.
db.ensure_data_dir()
seed_data.initialize()

MODULOS = {
    "Inicio": "inicio",
    "Pacientes": "pacientes",
    "Médicos y Especialidades": "medicos",
    "Citas": "citas",
    "Consultas": "consultas",
    "Diagnósticos": "diagnosticos",
    "Tratamientos": "tratamientos",
    "Hospitalización": "hospitalizacion",
    "Reportes y Análisis": "reportes",
}

with st.sidebar:
    theme.sidebar_marca("SIG-Hospital", "Gestión Hospitalaria")
    opcion = st.radio("Menú principal", list(MODULOS.keys()), label_visibility="collapsed")
    st.divider()
    theme.sidebar_pie(
        "Proyecto académico · Python + Streamlit<br>"
        "Persistencia en archivos CSV, sin API ni motor de<br>base de datos externo."
    )

seccion = MODULOS[opcion]

if seccion == "inicio":
    theme.encabezado("SIG-Hospital", "Sistema Integral de Gestión y Análisis Hospitalario")

    pacientes_df = db.load("pacientes")
    medicos_df = db.load("medicos")
    citas_df = db.load("citas")
    hosp_df = db.load("hospitalizaciones")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pacientes registrados", len(pacientes_df))
    c2.metric("Médicos activos", len(medicos_df))
    c3.metric("Citas registradas", len(citas_df))
    c4.metric("Hospitalizaciones activas",
              len(hosp_df[hosp_df.estado == "Hospitalizado"]) if not hosp_df.empty else 0)

    st.write("")
    st.markdown("#### Módulos del sistema")
    st.caption("Usa el menú de la izquierda para navegar entre ellos.")

    tarjetas = [
        ("Pacientes", "Alta, edición y consulta de expedientes básicos."),
        ("Médicos y Especialidades", "Personal médico, especialidades y consultorios."),
        ("Citas", "Agendamiento y seguimiento de citas médicas."),
        ("Consultas", "Registro de la atención médica brindada."),
        ("Diagnósticos", "Catálogo de diagnósticos usado en las consultas."),
        ("Tratamientos", "Catálogo de medicamentos y tratamientos asignados."),
        ("Hospitalización", "Ingresos, estancia y altas médicas."),
        ("Reportes y Análisis", "Indicadores, visualizaciones y modelos de Machine Learning."),
    ]
    filas = [tarjetas[i:i + 4] for i in range(0, len(tarjetas), 4)]
    for fila in filas:
        cols = st.columns(4)
        for col, (titulo, desc) in zip(cols, fila):
            with col:
                st.markdown(theme.tarjeta_modulo(titulo, desc), unsafe_allow_html=True)
        st.write("")

    st.info(
        "El sistema incluye datos de ejemplo generados automáticamente para que puedas "
        "explorar todos los módulos desde el primer momento. Puedes reiniciarlos en "
        "cualquier momento desde **Reportes y Análisis → Datos y reinicio**."
    )

elif seccion == "pacientes":
    pacientes.render()
elif seccion == "medicos":
    medicos.render()
elif seccion == "citas":
    citas.render()
elif seccion == "consultas":
    consultas.render()
elif seccion == "diagnosticos":
    diagnosticos.render()
elif seccion == "tratamientos":
    tratamientos.render()
elif seccion == "hospitalizacion":
    hospitalizacion.render()
elif seccion == "reportes":
    reportes.render()
