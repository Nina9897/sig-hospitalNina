import streamlit as st
import pandas as pd
from datetime import date
from utils import storage as db
from utils import theme


def calcular_edad(fecha_nac):
    try:
        f = pd.to_datetime(fecha_nac).date()
        hoy = date.today()
        return hoy.year - f.year - ((hoy.month, hoy.day) < (f.month, f.day))
    except Exception:
        return None


def render():
    theme.encabezado("Módulo de Pacientes", "Alta, edición y consulta de expedientes básicos")
    tab_lista, tab_nuevo, tab_editar = st.tabs(["Listado", "Nuevo paciente", "Editar / Eliminar"])

    df = db.load("pacientes")

    with tab_lista:
        col1, col2 = st.columns([2, 1])
        with col1:
            busqueda = st.text_input("Buscar por nombre o apellido")
        with col2:
            sexo_filtro = st.selectbox("Filtrar por sexo", ["Todos", "F", "M"])

        vista = df.copy()
        if busqueda:
            mask = vista["nombre"].str.contains(busqueda, case=False, na=False) | \
                   vista["apellido"].str.contains(busqueda, case=False, na=False)
            vista = vista[mask]
        if sexo_filtro != "Todos":
            vista = vista[vista["sexo"] == sexo_filtro]

        if not vista.empty:
            vista = vista.copy()
            vista["edad"] = vista["fecha_nacimiento"].apply(calcular_edad)
        st.dataframe(vista, use_container_width=True, hide_index=True)
        st.caption(f"Total de pacientes registrados: {len(df)}")

    with tab_nuevo:
        with st.form("form_nuevo_paciente", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nombre = c1.text_input("Nombre*")
            apellido = c2.text_input("Apellido*")
            c3, c4 = st.columns(2)
            fecha_nac = c3.date_input("Fecha de nacimiento", min_value=date(1900, 1, 1), max_value=date.today())
            sexo = c4.selectbox("Sexo", ["F", "M"])
            c5, c6 = st.columns(2)
            telefono = c5.text_input("Teléfono")
            email = c6.text_input("Correo electrónico")
            direccion = st.text_input("Dirección")
            tipo_sangre = st.selectbox("Tipo de sangre", ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"])
            enviado = st.form_submit_button("Registrar paciente", type="primary")

            if enviado:
                if not nombre or not apellido:
                    st.error("Nombre y apellido son obligatorios.")
                else:
                    nuevo_id = db.next_id(df, "id_paciente")
                    registro = {
                        "id_paciente": nuevo_id, "nombre": nombre, "apellido": apellido,
                        "fecha_nacimiento": str(fecha_nac), "sexo": sexo, "telefono": telefono,
                        "email": email, "direccion": direccion, "tipo_sangre": tipo_sangre,
                        "fecha_registro": str(date.today()),
                    }
                    db.upsert("pacientes", "id_paciente", registro)
                    st.success(f"Paciente '{nombre} {apellido}' registrado con ID {nuevo_id}.")
                    st.rerun()

    with tab_editar:
        if df.empty:
            st.info("No hay pacientes registrados todavía.")
            return
        opciones = {f"{r.id_paciente} - {r.nombre} {r.apellido}": r.id_paciente for r in df.itertuples()}
        seleccion = st.selectbox("Selecciona un paciente", list(opciones.keys()))
        id_sel = opciones[seleccion]
        registro = df[df.id_paciente == id_sel].iloc[0]

        with st.form("form_editar_paciente"):
            c1, c2 = st.columns(2)
            nombre = c1.text_input("Nombre", registro["nombre"])
            apellido = c2.text_input("Apellido", registro["apellido"])
            c3, c4 = st.columns(2)
            fecha_nac = c3.date_input("Fecha de nacimiento", pd.to_datetime(registro["fecha_nacimiento"]).date())
            sexo = c4.selectbox("Sexo", ["F", "M"], index=["F", "M"].index(registro["sexo"]))
            c5, c6 = st.columns(2)
            telefono = c5.text_input("Teléfono", registro["telefono"])
            email = c6.text_input("Correo electrónico", registro["email"])
            direccion = st.text_input("Dirección", registro["direccion"])
            tipos = ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"]
            tipo_sangre = st.selectbox("Tipo de sangre", tipos, index=tipos.index(registro["tipo_sangre"]))

            col_g, col_e = st.columns(2)
            guardar = col_g.form_submit_button("Guardar cambios", type="primary")
            eliminar = col_e.form_submit_button("Eliminar paciente")

            if guardar:
                actualizado = {
                    "id_paciente": id_sel, "nombre": nombre, "apellido": apellido,
                    "fecha_nacimiento": str(fecha_nac), "sexo": sexo, "telefono": telefono,
                    "email": email, "direccion": direccion, "tipo_sangre": tipo_sangre,
                    "fecha_registro": registro["fecha_registro"],
                }
                db.upsert("pacientes", "id_paciente", actualizado)
                st.success("Paciente actualizado correctamente.")
                st.rerun()

            if eliminar:
                dependientes = db.referencias_activas(id_sel, [
                    ("citas", "id_paciente"), ("consultas", "id_paciente"),
                    ("tratamientos", "id_paciente"), ("hospitalizaciones", "id_paciente"),
                    ("pagos", "id_paciente"),
                ])
                if dependientes:
                    theme.aviso_en_uso(dependientes, "eliminar este paciente")
                else:
                    db.delete_row("pacientes", "id_paciente", id_sel)
                    st.warning("Paciente eliminado.")
                    st.rerun()
