
## Instalación

```bash
# 1. Entra a la carpeta del proyecto
cd sig-hospital

# 2. (Recomendado) crea un entorno virtual
python -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate

# 3. Instala las dependencias
pip install -r requirements.txt
```

## 3. Ejecución

```bash
streamlit run app.py
```

Streamlit abrirá automáticamente el navegador en `http://localhost:8501`.
Al primer arranque, el sistema genera automáticamente **datos de ejemplo**
(pacientes, médicos, citas, consultas, tratamientos, hospitalizaciones,
etc. de los últimos 6 meses) para que puedas explorar todos los módulos
y reportes sin capturar información manualmente. Puedes reiniciarlos en
cualquier momento desde **Reportes y Análisis → Datos y reinicio**.

## 4. Estructura del proyecto

```
sig-hospital/
├── app.py                     # Punto de entrada de la aplicación (menú y ruteo)
├── requirements.txt
├── data/                      # "Base de datos" en archivos CSV (se genera sola)
├── utils/
│   ├── storage.py             # Capa de persistencia (cargar/guardar CSV)
│   └── seed_data.py           # Generador de datos de ejemplo
└── modules/
    ├── pacientes.py
    ├── medicos.py              # Médicos + Especialidades + Consultorios
    ├── citas.py
    ├── consultas.py
    ├── diagnosticos.py         # Catálogo de diagnósticos
    ├── tratamientos.py         # Medicamentos + Tratamientos
    ├── hospitalizacion.py      # Ingresos, camas y altas
    └── reportes.py             # KPIs, visualizaciones y Machine Learning
```

## 5. Módulos del sistema

1. **Pacientes** — alta, edición, baja y búsqueda de pacientes.
2. **Médicos y Especialidades** — médicos, especialidades y consultorios.
3. **Citas** — agendamiento y gestión de estado (Pendiente, Confirmada,
   Completada, Cancelada, No Asistió).
4. **Consultas** — registro de signos vitales, motivo y diagnóstico de
   cada atención médica, ligada a una cita.
5. **Diagnósticos** — catálogo tipo CIE-10 simplificado y frecuencia de uso.
6. **Tratamientos** — catálogo de medicamentos (con control de stock) y
   asignación de tratamientos por consulta.
7. **Hospitalización** — ingreso, ocupación de camas por área y alta médica
   con cálculo de días de estancia y costo estimado.
8. **Reportes y Análisis** — ver sección siguiente.

## 6. Reportes y Análisis: las 5 unidades aplicadas

El módulo de **Reportes y Análisis** aplica, sobre el mismo conjunto de
datos hospitalarios, las cinco unidades del curso:

| Unidad | Técnica aplicada | Dónde se ve |
|---|---|---|
| 1. Modelado / integración de datos | Se construye una **tabla analítica consolidada** (tipo data warehouse simplificado) uniendo citas, pacientes, médicos y especialidades con `pandas.merge` | `construir_tabla_analitica()` |
| 2. Indicadores de gestión (KPIs) | Total de citas, tasa de cancelación, ocupación hospitalaria, especialidad con más demanda, ingresos, etc. | Pestaña **Indicadores (KPIs)** |
| 3. Visualización de datos | Demanda por especialidad, horarios de saturación, tendencia mensual, distribución por edad, costos por área | Pestaña **Visualizaciones** |
| 4. Minería de datos no supervisada | **Clustering (K-Means)** para segmentar pacientes por edad/frecuencia/inasistencia, y **reglas de asociación (Apriori)** entre medicamentos recetados juntos | Pestañas **Segmentación de pacientes** y **Asociación de medicamentos** |
| 5. Minería de datos supervisada | **Clasificación (Random Forest)** que predice la probabilidad de cancelación/inasistencia de una cita, con simulador interactivo | Pestaña **Predicción de cancelaciones** |

Todos los modelos se entrenan **en tiempo real** con los datos que existen
en ese momento en el sistema (archivos CSV), por lo que si agregas más
citas, consultas o tratamientos, los reportes y modelos se actualizan
automáticamente.

## 7. Notas técnicas

- No se utiliza ningún servidor de base de datos (MySQL, PostgreSQL, etc.)
  ni ninguna API externa: todo el almacenamiento es local en `data/*.csv`.
- El algoritmo de reglas de asociación (Apriori) está implementado desde
  cero en `modules/reportes.py`, sin depender de librerías externas
  adicionales como `mlxtend`.
- Puedes cambiar el nombre del sistema editando el título en `app.py`
  (`st.set_page_config` y el encabezado de la sección de inicio).
