"""
Capa de persistencia del SIG-Hospital.
No se utiliza motor de base de datos ni API externa: toda la información
se administra con archivos CSV (simulando tablas de una base de datos
relacional) manipulados con pandas. Esto permite que el sistema sea
100% funcional de forma local, sin dependencias externas.
"""
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Esquema de cada "tabla" del sistema (nombre de archivo -> columnas)
SCHEMA = {
    "especialidades": ["id_especialidad", "nombre", "descripcion"],
    "consultorios": ["id_consultorio", "nombre", "ubicacion", "id_especialidad"],
    "medicos": ["id_medico", "nombre", "apellido", "id_especialidad", "cedula",
                "telefono", "email", "fecha_ingreso"],
    "pacientes": ["id_paciente", "nombre", "apellido", "fecha_nacimiento", "sexo",
                  "telefono", "email", "direccion", "tipo_sangre", "fecha_registro"],
    "citas": ["id_cita", "id_paciente", "id_medico", "id_consultorio", "fecha",
              "hora", "motivo", "estado", "fecha_registro"],
    "consultas": ["id_consulta", "id_cita", "id_paciente", "id_medico", "fecha",
                  "peso", "talla", "presion", "temperatura", "motivo_consulta",
                  "observaciones", "id_diagnostico"],
    "diagnosticos_catalogo": ["id_diagnostico", "codigo", "nombre", "categoria"],
    "medicamentos": ["id_medicamento", "nombre", "presentacion", "stock", "precio_unitario"],
    "tratamientos": ["id_tratamiento", "id_consulta", "id_paciente", "id_medicamento",
                      "dosis", "frecuencia", "duracion_dias", "indicaciones", "fecha"],
    "camas": ["id_cama", "numero", "area", "estado"],
    "hospitalizaciones": ["id_hospitalizacion", "id_paciente", "id_medico", "id_cama",
                           "fecha_ingreso", "motivo_ingreso", "diagnostico_ingreso",
                           "costo_diario", "fecha_alta", "estado"],
    "pagos": ["id_pago", "id_paciente", "concepto", "referencia", "monto",
              "fecha_pago", "metodo_pago", "estado"],
}


# Columnas verdaderamente numéricas (medidas, cantidades, montos). Todo lo
# demás que no sea un identificador (id_*) se lee siempre como texto: si no
# se fuerza el tipo, pandas puede inferir como número una columna como
# "cedula", "telefono" o "numero" (de cama) cuando todos sus valores parecen
# dígitos, y en cuanto aparece una fila vacía la columna pasa a float,
# mostrando cosas como "555.0" y provocando errores al editar/guardar.
COLUMNAS_NUMERICAS = {
    "consultas": ["peso", "talla", "temperatura"],
    "medicamentos": ["stock", "precio_unitario"],
    "tratamientos": ["duracion_dias"],
    "hospitalizaciones": ["costo_diario"],
    "pagos": ["monto"],
}


def _path(table):
    return os.path.join(DATA_DIR, f"{table}.csv")


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)
    for table, cols in SCHEMA.items():
        p = _path(table)
        if not os.path.exists(p):
            pd.DataFrame(columns=cols).to_csv(p, index=False)


def _dtype_map(table):
    numericas = set(COLUMNAS_NUMERICAS.get(table, []))
    return {
        c: str for c in SCHEMA.get(table, [])
        if c not in numericas and not c.startswith("id_")
    }


def load(table) -> pd.DataFrame:
    ensure_data_dir()
    p = _path(table)
    if not os.path.exists(p):
        return pd.DataFrame(columns=SCHEMA.get(table, []))
    df = pd.read_csv(p, dtype=_dtype_map(table))
    return df


def save(table, df: pd.DataFrame):
    ensure_data_dir()
    df.to_csv(_path(table), index=False)


def next_id(df: pd.DataFrame, id_col: str) -> int:
    if df.empty or id_col not in df.columns or df[id_col].dropna().empty:
        return 1
    return int(df[id_col].max()) + 1


def upsert(table, id_col, record: dict):
    """Inserta un registro nuevo o actualiza uno existente según id_col.

    En vez de escribir valor por valor sobre el DataFrame existente
    (df.loc[idx, columna] = valor), se reconstruye la fila completa y se
    reinserta en su posición. Esto evita errores de incompatibilidad de
    tipos que pandas lanza al forzar, por ejemplo, un texto sobre una
    columna que se infirió como numérica (algo que ocurría antes al
    editar un registro y podía impedir guardar los cambios).
    """
    df = load(table)
    # Se normaliza a int cuando es posible para evitar que un mismo id no
    # coincida por diferencias de tipo (str/int/np.int64) entre lo que
    # entrega un formulario y lo que se leyó del CSV.
    id_value = _normaliza_id(record.get(id_col))
    ids_existentes = df[id_col].apply(_normaliza_id) if id_col in df.columns else pd.Series(dtype=object)
    coincide = (ids_existentes == id_value) if not ids_existentes.empty else pd.Series(dtype=bool)

    columnas = list(dict.fromkeys(list(df.columns) + list(record.keys())))
    fila_nueva = pd.DataFrame([record]).reindex(columns=columnas)

    if coincide.any():
        pos = df.index.get_loc(df.index[coincide][0])
        antes = df.iloc[:pos].reindex(columns=columnas)
        despues = df.iloc[pos + 1:].reindex(columns=columnas)
        df = pd.concat([antes, fila_nueva, despues], ignore_index=True)
    else:
        df = pd.concat([df.reindex(columns=columnas), fila_nueva], ignore_index=True)

    save(table, df)
    return df


def _normaliza_id(valor):
    """Convierte un id a int cuando es numéricamente equivalente, para que
    comparaciones entre tipos (int, np.int64, '3', 3.0) funcionen bien."""
    try:
        if pd.isna(valor):
            return valor
    except (TypeError, ValueError):
        pass
    try:
        return int(valor)
    except (TypeError, ValueError):
        return valor


def delete_row(table, id_col, id_value):
    """Elimina el registro cuyo id_col coincida con id_value.
    Devuelve (df_actualizado, eliminados) donde 'eliminados' es la cantidad
    de filas realmente borradas (0 si el id no existía)."""
    df = load(table)
    if id_col not in df.columns:
        return df, 0
    objetivo = _normaliza_id(id_value)
    mascara = df[id_col].apply(_normaliza_id) == objetivo
    eliminados = int(mascara.sum())
    df = df[~mascara]
    save(table, df)
    return df, eliminados


def referencias_activas(id_value, referencias):
    """Verifica si un id sigue siendo usado como llave foránea en otras
    tablas antes de permitir borrarlo, para no dejar datos huérfanos.

    referencias: lista de tuplas (tabla, columna_fk).
    Devuelve un diccionario {tabla: cantidad} solo con las tablas donde
    todavía existan registros dependientes.
    """
    objetivo = _normaliza_id(id_value)
    activos = {}
    for tabla, columna in referencias:
        df = load(tabla)
        if columna not in df.columns or df.empty:
            continue
        cnt = int((df[columna].apply(_normaliza_id) == objetivo).sum())
        if cnt > 0:
            activos[tabla] = cnt
    return activos


def reset_all():
    """Elimina todos los datos (usado por el botón de reinicio en Reportes)."""
    import shutil
    if os.path.exists(DATA_DIR):
        shutil.rmtree(DATA_DIR)
    ensure_data_dir()
