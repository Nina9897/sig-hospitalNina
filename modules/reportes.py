"""
Módulo de Reportes y Análisis.

Aplica las cinco unidades del curso sobre el mismo conjunto de datos
hospitalarios:
  1. Modelado / integración de datos -> tabla analítica consolidada (tipo
     data warehouse simplificado) construida con pandas a partir de las
     "tablas" CSV.
  2. Indicadores de gestión (KPIs) -> métricas clave para la toma de
     decisiones.
  3. Visualización de datos -> gráficos de demanda, saturación y costos.
  4. Minería de datos no supervisada -> segmentación (clustering) de
     pacientes y reglas de asociación entre medicamentos.
  5. Minería de datos supervisada -> modelo de clasificación que predice
     la probabilidad de que una cita sea cancelada / no asistida.
"""
import itertools
from datetime import date

import numpy as np
import pandas as pd
import streamlit as st

from utils import storage as db
from utils import graficas as g
from utils import theme


# ----------------------------------------------------------------------
# 1) INTEGRACIÓN DE DATOS: tabla analítica consolidada
# ----------------------------------------------------------------------
def construir_tabla_analitica():
    citas = db.load("citas")
    pacientes = db.load("pacientes")
    medicos = db.load("medicos")
    especialidades = db.load("especialidades")

    if citas.empty:
        return pd.DataFrame()

    df = citas.merge(pacientes, on="id_paciente", how="left", suffixes=("", "_pac"))
    df = df.merge(medicos, on="id_medico", how="left", suffixes=("", "_med"))
    df = df.merge(especialidades, on="id_especialidad", how="left", suffixes=("", "_esp"))
    df = df.rename(columns={"nombre_esp": "especialidad"})
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["dia_semana"] = df["fecha"].dt.day_name()
    df["mes"] = df["fecha"].dt.to_period("M").astype(str)
    df["hora_num"] = df["hora"].str.split(":").str[0].astype(int)
    if "fecha_nacimiento" in df.columns:
        edad = (pd.Timestamp.today() - pd.to_datetime(df["fecha_nacimiento"], errors="coerce")).dt.days // 365
        df["edad"] = edad
    return df


def render():
    theme.encabezado("Reportes, Indicadores y Análisis de Datos",
                      "KPIs, visualizaciones y modelos de Machine Learning sobre los datos hospitalarios")

    tabla = construir_tabla_analitica()
    if tabla.empty:
        st.info("Aún no hay suficientes datos (citas) para generar reportes. "
               "Agenda algunas citas o utiliza los datos de ejemplo.")
        return

    tabs = st.tabs([
        "Gráficas Principales",
        "Indicadores (KPIs)",
        "Segmentación de pacientes",
        "Predicción de cancelaciones",
        "Asociación de medicamentos",
        "Datos y reinicio",
    ])

    with tabs[0]:
        render_graficas_principales(tabla)
    with tabs[1]:
        render_kpis(tabla)
    with tabs[2]:
        render_clustering(tabla)
    with tabs[3]:
        render_clasificacion(tabla)
    with tabs[4]:
        render_asociacion()
    with tabs[5]:
        render_datos()


# ----------------------------------------------------------------------
# GRÁFICAS PRINCIPALES SOLICITADAS
# ----------------------------------------------------------------------
def render_graficas_principales(tabla):
    st.caption("Las 10 gráficas principales del sistema, listas para la toma de decisiones.")

    pacientes = db.load("pacientes")
    consultas = db.load("consultas")
    diagnosticos_cat = db.load("diagnosticos_catalogo")
    tratamientos = db.load("tratamientos")
    medicamentos = db.load("medicamentos")
    camas = db.load("camas")
    hosp = db.load("hospitalizaciones")
    pagos = db.load("pagos")

    # 1. Demanda de servicios médicos ----------------------------------
    st.subheader("1. Demanda de servicios médicos")
    st.caption("Volumen total de citas solicitadas mes a mes.")
    g.chip("lineas")
    tendencia = tabla.groupby("mes").size()
    st.plotly_chart(g.lineas(tendencia), use_container_width=True)
    st.metric("Total de citas registradas (demanda histórica)", len(tabla))

    st.divider()

    # 2. Especialidades con mayor demanda -------------------------------
    st.subheader("2. Especialidades con mayor demanda")
    st.caption("Número de citas solicitadas por especialidad médica.")
    g.chip("barras")
    st.plotly_chart(g.barras(tabla["especialidad"].value_counts()), use_container_width=True)

    st.divider()

    # 3. Horarios de mayor saturación -----------------------------------
    st.subheader("3. Horarios de mayor saturación")
    st.caption("Cantidad de citas agendadas por día de la semana y hora del día: entre más "
               "intenso el color, mayor la saturación de la agenda en ese horario.")
    g.chip("mapa_calor")
    dias_es = {
        "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
        "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo",
    }
    orden_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    tabla_horarios = tabla.copy()
    tabla_horarios["dia_semana_es"] = tabla_horarios["dia_semana"].map(dias_es).fillna(tabla_horarios["dia_semana"])
    matriz_horarios = tabla_horarios.groupby(["dia_semana_es", "hora_num"]).size().unstack(fill_value=0)
    matriz_horarios = matriz_horarios.reindex([d for d in orden_dias if d in matriz_horarios.index])
    matriz_horarios.columns = [f"{h}:00" for h in matriz_horarios.columns]
    st.plotly_chart(g.mapa_calor(matriz_horarios), use_container_width=True)

    st.divider()

    # 4. Frecuencia de enfermedades ---------------------------------------
    st.subheader("4. Frecuencia de enfermedades")
    st.caption("Proporción de los diagnósticos más frecuentes registrados en las consultas.")
    if not consultas.empty and not diagnosticos_cat.empty:
        v = consultas.merge(diagnosticos_cat[["id_diagnostico", "nombre"]], on="id_diagnostico", how="left")
        frecuencia = v["nombre"].value_counts().head(10)
        g.chip("dona")
        st.plotly_chart(g.dona(frecuencia.index, frecuencia.values, texto_centro=f"{len(v)} dx"),
                        use_container_width=True)
    else:
        st.info("Aún no hay consultas con diagnóstico registrado.")

    st.divider()

    # 5. Pacientes con mayor número de consultas -------------------------
    st.subheader("5. Pacientes con mayor número de consultas")
    st.caption("Los 10 pacientes con más citas/consultas registradas.")
    top_pac = tabla.groupby("id_paciente").size().sort_values(ascending=False).head(10).reset_index(name="num_citas")
    top_pac = top_pac.merge(pacientes[["id_paciente", "nombre", "apellido"]], on="id_paciente", how="left")
    top_pac["paciente"] = top_pac["nombre"].fillna("") + " " + top_pac["apellido"].fillna("")
    g.chip("barras")
    st.plotly_chart(g.barras(top_pac.set_index("paciente")["num_citas"], horizontal=True),
                    use_container_width=True)

    st.divider()

    # 6. Uso de medicamentos ----------------------------------------------
    st.subheader("6. Medicamentos más usados")
    st.caption("Los medicamentos más recetados en los tratamientos asignados a los pacientes.")
    if not tratamientos.empty and not medicamentos.empty:
        v = tratamientos.merge(medicamentos[["id_medicamento", "nombre"]], on="id_medicamento", how="left")
        conteo = v["nombre"].value_counts().head(10)
        g.chip("pastel")
        st.plotly_chart(g.pastel(conteo.index, conteo.values), use_container_width=True)
    else:
        st.info("Aún no hay tratamientos registrados.")

    st.divider()

    # 7. Ocupación hospitalaria -------------------------------------------
    st.subheader("7. Ocupación hospitalaria")
    st.caption("Camas por área y estado: entre más intenso el color, mayor la cantidad de camas.")
    if not camas.empty:
        c1, c2 = st.columns([1, 2])
        ocupacion_pct = (camas["estado"] == "Ocupada").sum() / len(camas) * 100
        c1.metric("Ocupación general", f"{ocupacion_pct:.1f}%")
        with c2:
            g.chip("mapa_calor")
            matriz = camas.groupby(["area", "estado"]).size().unstack(fill_value=0)
            st.plotly_chart(g.mapa_calor(matriz), use_container_width=True)
    else:
        st.info("Aún no hay camas registradas.")

    st.divider()

    # 8. Cancelación de citas -----------------------------------------------
    st.subheader("8. Cancelación de citas")
    st.caption("Distribución de las citas según su estado final.")
    col1, col2 = st.columns(2)
    with col1:
        g.chip("dona")
        estado_counts = tabla["estado"].value_counts()
        st.markdown("**Citas por estado final**")
        st.caption("Cuántas citas terminaron en cada estado (confirmada, cancelada, no asistió, etc.).")
        st.plotly_chart(g.dona(estado_counts.index, estado_counts.values), use_container_width=True)
    with col2:
        cancel_mes = tabla.assign(
            cancelada=tabla["estado"].isin(["Cancelada", "No Asistió"])
        ).groupby("mes")["cancelada"].mean() * 100
        st.markdown("**Tasa de cancelación mensual (%)**")
        st.caption("Porcentaje de citas canceladas o no asistidas de cada mes.")
        g.chip("area")
        st.plotly_chart(g.area(cancel_mes, sufijo_y="%"), use_container_width=True)

    st.divider()

    # 9. Costos de atención --------------------------------------------------
    st.subheader("9. Costos de atención")
    st.caption("Ingresos por consultas y distribución del costo de hospitalización.")
    col1, col2 = st.columns(2)
    with col1:
        if not pagos.empty:
            pagos_m = pagos.copy()
            pagos_m["mes"] = pd.to_datetime(pagos_m["fecha_pago"]).dt.to_period("M").astype(str)
            st.markdown("**Ingresos por consultas (mensual)**")
            st.caption("Monto total cobrado por consultas y servicios, agrupado por mes.")
            g.chip("area")
            st.plotly_chart(g.area(pagos_m.groupby("mes")["monto"].sum()), use_container_width=True)
        else:
            st.info("Aún no hay pagos registrados.")
    with col2:
        if not hosp.empty and not camas.empty:
            h = hosp.merge(camas[["id_cama", "area"]], on="id_cama", how="left")
            h["fecha_ingreso"] = pd.to_datetime(h["fecha_ingreso"])
            h["fecha_fin"] = pd.to_datetime(h["fecha_alta"].replace("", np.nan)).fillna(pd.Timestamp.today())
            h["dias"] = (h["fecha_fin"] - h["fecha_ingreso"]).dt.days.clip(lower=1)
            h["costo_total"] = h["dias"] * h["costo_diario"]
            st.markdown("**Distribución del costo de hospitalización por área**")
            st.caption("Costo total por paciente hospitalizado, agrupado por área del hospital "
                       "(la línea punteada marca el promedio).")
            g.chip("boxplot")
            st.plotly_chart(g.boxplot(h, "area", "costo_total"), use_container_width=True)
        else:
            st.info("Aún no hay hospitalizaciones registradas.")

    st.divider()

    # 10. Predicción y clasificación de determinados comportamientos --------
    st.subheader("10. Predicción y clasificación de determinados comportamientos")
    st.caption("Resumen de los modelos de Machine Learning del sistema. "
              "El detalle interactivo está en las pestañas **Segmentación de pacientes** "
              "y **Predicción de cancelaciones**.")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Segmentación de pacientes (clustering)**")
        _resumen_clustering_rapido(tabla)
    with col2:
        st.markdown("**Predicción de cancelación de citas (clasificación)**")
        _resumen_clasificacion_rapido(tabla)


def _resumen_clustering_rapido(tabla):
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    resumen = tabla.groupby("id_paciente").agg(
        edad=("edad", "max"),
        num_citas=("id_cita", "count"),
        num_canceladas=("estado", lambda s: (s.isin(["Cancelada", "No Asistió"])).sum()),
    ).reset_index()
    resumen["edad"] = resumen["edad"].fillna(resumen["edad"].median())
    resumen["tasa_inasistencia"] = (resumen["num_canceladas"] / resumen["num_citas"] * 100).round(1)

    if len(resumen) < 5:
        st.info("Se requieren más pacientes con citas para segmentar.")
        return

    X = resumen[["edad", "num_citas", "tasa_inasistencia"]].fillna(0)
    X_esc = StandardScaler().fit_transform(X)
    modelo = KMeans(n_clusters=3, n_init=10, random_state=42)
    resumen["grupo"] = "Grupo " + (modelo.fit_predict(X_esc) + 1).astype(str)
    g.chip("dispersion")
    st.plotly_chart(
        g.dispersion(resumen, x="edad", y="num_citas", color_col="grupo"),
        use_container_width=True)
    st.caption("Pacientes agrupados en 3 perfiles según edad, frecuencia de citas e inasistencia "
              "(cada color es un grupo).")


def _resumen_clasificacion_rapido(tabla):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
    from sklearn.preprocessing import LabelEncoder

    datos = tabla.copy()
    datos["cancelada"] = datos["estado"].isin(["Cancelada", "No Asistió"]).astype(int)
    datos = datos.dropna(subset=["edad"])

    if len(datos) < 30 or datos["cancelada"].nunique() < 2:
        st.info("Se requiere más historial de citas para entrenar el modelo.")
        return

    le_esp = LabelEncoder()
    le_sexo = LabelEncoder()
    datos["especialidad_cod"] = le_esp.fit_transform(datos["especialidad"].astype(str))
    datos["sexo_cod"] = le_sexo.fit_transform(datos["sexo"].astype(str))
    features = ["edad", "hora_num", "especialidad_cod", "sexo_cod"]
    X, y = datos[features], datos["cancelada"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    modelo = RandomForestClassifier(n_estimators=150, max_depth=6, random_state=42)
    modelo.fit(X_train, y_train)
    exactitud = accuracy_score(y_test, modelo.predict(X_test))
    st.metric("Exactitud del modelo", f"{exactitud * 100:.1f}%")
    st.caption("Random Forest entrenado con el historial de citas para predecir cancelaciones/inasistencias.")


# ----------------------------------------------------------------------
# 2) INDICADORES DE GESTIÓN (KPIs)
# ----------------------------------------------------------------------
def render_kpis(tabla):
    st.subheader("Indicadores clave para la toma de decisiones")

    hosp = db.load("hospitalizaciones")
    camas = db.load("camas")
    pagos = db.load("pagos")

    total_citas = len(tabla)
    completadas = (tabla["estado"] == "Completada").sum()
    canceladas = (tabla["estado"] == "Cancelada").sum()
    no_asistio = (tabla["estado"] == "No Asistió").sum()
    tasa_cancelacion = (canceladas + no_asistio) / total_citas * 100 if total_citas else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de citas", total_citas)
    c2.metric("Citas completadas", int(completadas))
    c3.metric("Tasa de cancelación / inasistencia", f"{tasa_cancelacion:.1f}%")
    c4.metric("Pacientes únicos atendidos", tabla["id_paciente"].nunique())

    ocupacion = 0
    if not camas.empty:
        ocupacion = (camas["estado"] == "Ocupada").sum() / len(camas) * 100
    ingresos_activos = len(hosp[hosp.estado == "Hospitalizado"]) if not hosp.empty else 0
    ingreso_total = pagos["monto"].sum() if not pagos.empty else 0

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Ocupación hospitalaria", f"{ocupacion:.1f}%")
    c6.metric("Pacientes hospitalizados", ingresos_activos)
    c7.metric("Ingresos totales por consultas", f"${ingreso_total:,.2f}")
    c8.metric("Especialidad con más demanda",
              tabla["especialidad"].value_counts().idxmax() if not tabla.empty else "-")

    st.divider()
    st.caption("Estos indicadores resumen la operación diaria del hospital y sirven como base "
              "para decisiones de personal, insumos y capacidad instalada.")


# ----------------------------------------------------------------------
# 4a) MINERÍA NO SUPERVISADA: SEGMENTACIÓN DE PACIENTES (CLUSTERING)
# ----------------------------------------------------------------------
def render_clustering(tabla):
    st.subheader("Segmentación de pacientes con K-Means")
    st.caption("Agrupa a los pacientes según edad, número de consultas y tasa de inasistencia, "
              "para identificar perfiles de uso del servicio (frecuentes, ocasionales, de riesgo, etc.)")

    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    resumen = tabla.groupby("id_paciente").agg(
        edad=("edad", "max"),
        num_citas=("id_cita", "count"),
        num_canceladas=("estado", lambda s: (s.isin(["Cancelada", "No Asistió"])).sum()),
    ).reset_index()
    resumen["edad"] = resumen["edad"].fillna(resumen["edad"].median())
    resumen["tasa_inasistencia"] = (resumen["num_canceladas"] / resumen["num_citas"] * 100).round(1)

    if len(resumen) < 5:
        st.info("Se requieren al menos 5 pacientes con citas para segmentar.")
        return

    n_clusters = st.slider("Número de grupos (clusters)", min_value=2, max_value=6, value=3)

    X = resumen[["edad", "num_citas", "tasa_inasistencia"]].fillna(0)
    X_esc = StandardScaler().fit_transform(X)
    modelo = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
    resumen["grupo"] = modelo.fit_predict(X_esc)

    st.markdown("**Perfil promedio de cada grupo**")
    perfil = resumen.groupby("grupo")[["edad", "num_citas", "tasa_inasistencia"]].mean().round(1)
    perfil["pacientes"] = resumen.groupby("grupo").size()
    st.dataframe(perfil, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Pacientes por grupo**")
        st.caption("Cuántos pacientes quedaron asignados a cada grupo (cluster).")
        g.chip("pastel")
        grupo_counts = resumen["grupo"].value_counts().sort_index()
        st.plotly_chart(
            g.pastel([f"Grupo {i}" for i in grupo_counts.index], grupo_counts.values),
            use_container_width=True)
    with col2:
        st.markdown("**Distribución del número de consultas por paciente**")
        st.caption("Cuántos pacientes tienen determinado número de consultas registradas.")
        g.chip("histograma")
        st.plotly_chart(g.histograma(resumen["num_citas"]), use_container_width=True)

    with st.expander("Ver detalle de pacientes por grupo"):
        pacientes = db.load("pacientes")
        detalle = resumen.merge(pacientes[["id_paciente", "nombre", "apellido"]], on="id_paciente", how="left")
        st.dataframe(
            detalle[["id_paciente", "nombre", "apellido", "edad", "num_citas", "tasa_inasistencia", "grupo"]],
            use_container_width=True, hide_index=True)

    st.info("**Uso para la toma de decisiones:** los grupos con alta tasa de inasistencia pueden "
           "recibir recordatorios reforzados; los grupos con muchas consultas pueden priorizarse "
           "en programas de seguimiento crónico.")


# ----------------------------------------------------------------------
# 4b) MINERÍA NO SUPERVISADA: REGLAS DE ASOCIACIÓN (MEDICAMENTOS)
# ----------------------------------------------------------------------
def _apriori_simple(transacciones, soporte_min=0.05, confianza_min=0.3):
    """Implementación ligera del algoritmo Apriori (sin dependencias externas)."""
    n = len(transacciones)
    items = sorted(set(itertools.chain.from_iterable(transacciones)))

    def soporte(itemset):
        itemset = set(itemset)
        return sum(1 for t in transacciones if itemset.issubset(t)) / n

    frecuentes_1 = {frozenset([i]): soporte([i]) for i in items if soporte([i]) >= soporte_min}
    frecuentes = dict(frecuentes_1)
    nivel = frecuentes_1
    k = 2
    while nivel:
        candidatos = set()
        claves = list(nivel.keys())
        for a, b in itertools.combinations(claves, 2):
            union = a | b
            if len(union) == k:
                candidatos.add(union)
        nuevo_nivel = {}
        for c in candidatos:
            s = soporte(c)
            if s >= soporte_min:
                nuevo_nivel[c] = s
        frecuentes.update(nuevo_nivel)
        nivel = nuevo_nivel
        k += 1

    reglas = []
    for itemset, sop in frecuentes.items():
        if len(itemset) < 2:
            continue
        for tam_ant in range(1, len(itemset)):
            for antecedente in itertools.combinations(itemset, tam_ant):
                antecedente = frozenset(antecedente)
                consecuente = itemset - antecedente
                sop_ant = frecuentes.get(antecedente)
                if not sop_ant:
                    continue
                confianza = sop / sop_ant
                if confianza >= confianza_min:
                    reglas.append({
                        "si_receta": ", ".join(sorted(antecedente)),
                        "entonces_receta": ", ".join(sorted(consecuente)),
                        "soporte": round(sop, 3),
                        "confianza": round(confianza, 3),
                    })
    return pd.DataFrame(reglas).sort_values("confianza", ascending=False) if reglas else pd.DataFrame()


def render_asociacion():
    st.subheader("Reglas de asociación entre medicamentos")
    st.caption("Identifica qué medicamentos suelen recetarse juntos en un mismo tratamiento por consulta "
              "(algoritmo tipo Apriori), útil para logística de farmacia y protocolos clínicos.")

    tratamientos = db.load("tratamientos")
    medicamentos = db.load("medicamentos")
    if tratamientos.empty or len(tratamientos["id_consulta"].unique()) < 5:
        st.info("Se requieren más tratamientos registrados (varios medicamentos por consulta) "
               "para calcular reglas de asociación significativas.")
        return

    t = tratamientos.merge(medicamentos[["id_medicamento", "nombre"]], on="id_medicamento", how="left")
    transacciones = t.groupby("id_consulta")["nombre"].apply(lambda s: set(s.dropna())).tolist()
    transacciones = [tr for tr in transacciones if len(tr) >= 1]

    soporte_min = st.slider("Soporte mínimo", 0.01, 0.5, 0.03, step=0.01)
    confianza_min = st.slider("Confianza mínima", 0.1, 1.0, 0.3, step=0.05)

    reglas = _apriori_simple(transacciones, soporte_min, confianza_min)
    if reglas.empty:
        st.warning("No se encontraron reglas con los parámetros actuales; intenta reducir el soporte/confianza.")
    else:
        st.dataframe(reglas, use_container_width=True, hide_index=True)
        st.info("**Lectura:** una confianza de 0.60 en 'Si receta A → entonces receta B' significa que "
               "el 60% de las veces que se receta A, también se receta B en la misma consulta.")


# ----------------------------------------------------------------------
# 5) MINERÍA SUPERVISADA: PREDICCIÓN DE CANCELACIÓN DE CITAS
# ----------------------------------------------------------------------
def render_clasificacion(tabla):
    st.subheader("Predicción de cancelación / inasistencia a citas")
    st.caption("Modelo de clasificación (Random Forest) entrenado con el historial de citas para estimar "
              "la probabilidad de que una cita futura sea cancelada o no atendida, permitiendo tomar "
              "acciones preventivas (recordatorios, sobre-agendamiento controlado).")

    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report
    from sklearn.preprocessing import LabelEncoder

    datos = tabla.copy()
    datos["cancelada"] = datos["estado"].isin(["Cancelada", "No Asistió"]).astype(int)
    datos = datos.dropna(subset=["edad"])

    if len(datos) < 30 or datos["cancelada"].nunique() < 2:
        st.info("Se requiere más historial de citas (con casos canceladas y no canceladas) "
               "para entrenar el modelo predictivo.")
        return

    le_esp = LabelEncoder()
    le_sexo = LabelEncoder()
    datos["especialidad_cod"] = le_esp.fit_transform(datos["especialidad"].astype(str))
    datos["sexo_cod"] = le_sexo.fit_transform(datos["sexo"].astype(str))

    features = ["edad", "hora_num", "especialidad_cod", "sexo_cod"]
    X = datos[features]
    y = datos["cancelada"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    modelo = RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42)
    modelo.fit(X_train, y_train)
    y_pred = modelo.predict(X_test)
    exactitud = accuracy_score(y_test, y_pred)

    c1, c2 = st.columns(2)
    c1.metric("Exactitud del modelo (test)", f"{exactitud * 100:.1f}%")
    c2.metric("Citas usadas para entrenar", len(X_train))

    importancias = pd.Series(modelo.feature_importances_, index=features).sort_values(ascending=False)
    st.markdown("**Importancia de variables en la predicción**")
    st.caption("Qué tanto influye cada variable en la predicción del modelo (a mayor valor, más peso tiene).")
    g.chip("barras")
    st.plotly_chart(g.barras(importancias, horizontal=True), use_container_width=True)

    st.markdown("**Distribución de la probabilidad predicha según el resultado real**")
    st.caption("Compara la probabilidad de cancelación que estimó el modelo contra lo que realmente ocurrió "
               "con esas citas (la línea punteada marca el promedio de cada grupo).")
    probas = pd.DataFrame({
        "resultado_real": np.where(y_test.values == 1, "Sí canceló / faltó", "Asistió"),
        "probabilidad_predicha": modelo.predict_proba(X_test)[:, 1],
    })
    g.chip("boxplot")
    st.plotly_chart(g.boxplot(probas, "resultado_real", "probabilidad_predicha"), use_container_width=True)

    st.divider()
    st.markdown("### Simular predicción para una nueva cita")
    with st.form("form_prediccion"):
        c1, c2 = st.columns(2)
        edad_sim = c1.number_input("Edad del paciente", min_value=0, max_value=110, value=35)
        hora_sim = c2.slider("Hora de la cita", 7, 20, 10)
        c3, c4 = st.columns(2)
        especialidad_sim = c3.selectbox("Especialidad", sorted(datos["especialidad"].dropna().unique()))
        sexo_sim = c4.selectbox("Sexo", sorted(datos["sexo"].dropna().unique()))
        simular = st.form_submit_button("Predecir riesgo de cancelación", type="primary")

        if simular:
            entrada = pd.DataFrame([{
                "edad": edad_sim, "hora_num": hora_sim,
                "especialidad_cod": le_esp.transform([especialidad_sim])[0],
                "sexo_cod": le_sexo.transform([sexo_sim])[0],
            }])
            prob = modelo.predict_proba(entrada)[0][1]
            if prob >= 0.5:
                st.error(f"Alto riesgo de cancelación / inasistencia: {prob * 100:.1f}%")
            else:
                st.success(f"Riesgo bajo de cancelación / inasistencia: {prob * 100:.1f}%")


# ----------------------------------------------------------------------
# DATOS Y REINICIO
# ----------------------------------------------------------------------
def render_datos():
    st.subheader("Exploración de la tabla analítica consolidada")
    tabla = construir_tabla_analitica()
    st.dataframe(tabla, use_container_width=True)
    st.download_button("Descargar tabla analítica (CSV)", tabla.to_csv(index=False),
                       file_name="tabla_analitica_hospital.csv", mime="text/csv")

    st.divider()
    st.subheader("Zona de reinicio")
    st.caption("Elimina todos los datos y vuelve a generar la información de ejemplo. Útil para hacer "
              "demostraciones desde cero.")
    if st.button("Reiniciar todos los datos de ejemplo"):
        from utils import seed_data
        db.reset_all()
        seed_data.initialize(force=True)
        st.success("Datos reiniciados correctamente.")
        st.rerun()
