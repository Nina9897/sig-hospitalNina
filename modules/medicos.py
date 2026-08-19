import streamlit as st
import pandas as pd
from datetime import date
from utils import storage as db
from utils import theme


def render():
    theme.encabezado("Médicos, Especialidades y Consultorios",
                      "Personal médico, especialidades y consultorios")
    tab_medicos, tab_esp, tab_cons = st.tabs(["Médicos", "Especialidades", "Consultorios"])

    especialidades = db.load("especialidades")
    medicos = db.load("medicos")
    consultorios = db.load("consultorios")

    # ---------------- MÉDICOS ----------------
    with tab_medicos:
        sub_lista, sub_nuevo = st.tabs(["Listado", "Nuevo / Editar"])
        with sub_lista:
            vista = medicos.merge(especialidades, on="id_especialidad", how="left",
                                   suffixes=("", "_esp"))
            vista = vista.rename(columns={"nombre_esp": "especialidad"})
            cols = ["id_medico", "nombre", "apellido", "especialidad", "cedula",
                    "telefono", "email", "fecha_ingreso"]
            st.dataframe(vista[[c for c in cols if c in vista.columns]],
                         use_container_width=True, hide_index=True)
            st.caption(f"Total de médicos: {len(medicos)}")

        with sub_nuevo:
            if especialidades.empty:
                st.warning("Registra primero al menos una especialidad.")
            else:
                modo = st.radio("Acción", ["Nuevo médico", "Editar / Eliminar existente"], horizontal=True)
                esp_opts = {r.nombre: r.id_especialidad for r in especialidades.itertuples()}

                if modo == "Nuevo médico":
                    with st.form("form_nuevo_medico", clear_on_submit=True):
                        c1, c2 = st.columns(2)
                        nombre = c1.text_input("Nombre*")
                        apellido = c2.text_input("Apellido*")
                        especialidad = st.selectbox("Especialidad", list(esp_opts.keys()))
                        c3, c4 = st.columns(2)
                        cedula = c3.text_input("Cédula profesional")
                        telefono = c4.text_input("Teléfono")
                        email = st.text_input("Correo electrónico")
                        enviado = st.form_submit_button("Registrar médico", type="primary")
                        if enviado:
                            if not nombre or not apellido:
                                st.error("Nombre y apellido son obligatorios.")
                            else:
                                nuevo_id = db.next_id(medicos, "id_medico")
                                db.upsert("medicos", "id_medico", {
                                    "id_medico": nuevo_id, "nombre": nombre, "apellido": apellido,
                                    "id_especialidad": esp_opts[especialidad], "cedula": cedula,
                                    "telefono": telefono, "email": email,
                                    "fecha_ingreso": str(date.today()),
                                })
                                st.success(f"Médico registrado con ID {nuevo_id}.")
                                st.rerun()
                else:
                    if medicos.empty:
                        st.info("No hay médicos registrados.")
                    else:
                        opts = {f"{r.id_medico} - {r.nombre} {r.apellido}": r.id_medico for r in medicos.itertuples()}
                        sel = st.selectbox("Selecciona un médico", list(opts.keys()))
                        id_sel = opts[sel]
                        reg = medicos[medicos.id_medico == id_sel].iloc[0]
                        with st.form("form_editar_medico"):
                            c1, c2 = st.columns(2)
                            nombre = c1.text_input("Nombre", reg["nombre"])
                            apellido = c2.text_input("Apellido", reg["apellido"])
                            nombres_esp = list(esp_opts.keys())
                            idx_esp = 0
                            esp_actual = especialidades[especialidades.id_especialidad == reg["id_especialidad"]]
                            if not esp_actual.empty and esp_actual.iloc[0]["nombre"] in nombres_esp:
                                idx_esp = nombres_esp.index(esp_actual.iloc[0]["nombre"])
                            especialidad = st.selectbox("Especialidad", nombres_esp, index=idx_esp)
                            c3, c4 = st.columns(2)
                            cedula = c3.text_input("Cédula", reg["cedula"])
                            telefono = c4.text_input("Teléfono", reg["telefono"])
                            email = st.text_input("Correo", reg["email"])
                            col_g, col_e = st.columns(2)
                            guardar = col_g.form_submit_button("Guardar", type="primary")
                            eliminar = col_e.form_submit_button("Eliminar")
                            if guardar:
                                db.upsert("medicos", "id_medico", {
                                    "id_medico": id_sel, "nombre": nombre, "apellido": apellido,
                                    "id_especialidad": esp_opts[especialidad], "cedula": cedula,
                                    "telefono": telefono, "email": email,
                                    "fecha_ingreso": reg["fecha_ingreso"],
                                })
                                st.success("Médico actualizado.")
                                st.rerun()
                            if eliminar:
                                dependientes = db.referencias_activas(id_sel, [
                                    ("citas", "id_medico"), ("consultas", "id_medico"),
                                    ("hospitalizaciones", "id_medico"),
                                ])
                                if dependientes:
                                    theme.aviso_en_uso(dependientes, "eliminar este médico")
                                else:
                                    db.delete_row("medicos", "id_medico", id_sel)
                                    st.warning("Médico eliminado.")
                                    st.rerun()

    # ---------------- ESPECIALIDADES ----------------
    with tab_esp:
        sub_lista_esp, sub_nueva_esp, sub_editar_esp = st.tabs(["Listado", "Nueva", "Editar / Eliminar"])

        with sub_lista_esp:
            st.dataframe(especialidades, use_container_width=True, hide_index=True)
            st.caption(f"Total de especialidades: {len(especialidades)}")

        with sub_nueva_esp:
            with st.form("form_especialidad", clear_on_submit=True):
                nombre = st.text_input("Nombre de la especialidad")
                descripcion = st.text_area("Descripción")
                enviado = st.form_submit_button("Agregar especialidad", type="primary")
                if enviado:
                    if not nombre:
                        st.error("El nombre es obligatorio.")
                    else:
                        nuevo_id = db.next_id(especialidades, "id_especialidad")
                        db.upsert("especialidades", "id_especialidad", {
                            "id_especialidad": nuevo_id, "nombre": nombre, "descripcion": descripcion
                        })
                        st.success("Especialidad agregada.")
                        st.rerun()

        with sub_editar_esp:
            if especialidades.empty:
                st.info("No hay especialidades registradas todavía.")
            else:
                opts = {f"{r.id_especialidad} - {r.nombre}": r.id_especialidad
                        for r in especialidades.itertuples()}
                sel = st.selectbox("Selecciona una especialidad", list(opts.keys()), key="sel_editar_esp")
                id_sel = opts[sel]
                reg = especialidades[especialidades.id_especialidad == id_sel].iloc[0]
                with st.form("form_editar_especialidad"):
                    nombre = st.text_input("Nombre de la especialidad", reg["nombre"])
                    descripcion = st.text_area("Descripción", reg["descripcion"] if pd.notna(reg["descripcion"]) else "")
                    col_g, col_e = st.columns(2)
                    guardar = col_g.form_submit_button("Guardar cambios", type="primary")
                    eliminar = col_e.form_submit_button("Eliminar especialidad")

                    if guardar:
                        if not nombre:
                            st.error("El nombre es obligatorio.")
                        else:
                            db.upsert("especialidades", "id_especialidad", {
                                "id_especialidad": id_sel, "nombre": nombre, "descripcion": descripcion
                            })
                            st.success("Especialidad actualizada.")
                            st.rerun()

                    if eliminar:
                        dependientes = db.referencias_activas(id_sel, [
                            ("medicos", "id_especialidad"), ("consultorios", "id_especialidad"),
                        ])
                        if dependientes:
                            theme.aviso_en_uso(dependientes, "eliminar esta especialidad")
                        else:
                            db.delete_row("especialidades", "id_especialidad", id_sel)
                            st.warning("Especialidad eliminada.")
                            st.rerun()

    # ---------------- CONSULTORIOS ----------------
    with tab_cons:
        sub_lista_cons, sub_nuevo_cons, sub_editar_cons = st.tabs(["Listado", "Nuevo", "Editar / Eliminar"])

        with sub_lista_cons:
            vista = consultorios.merge(especialidades, on="id_especialidad", how="left", suffixes=("", "_esp"))
            vista = vista.rename(columns={"nombre_esp": "especialidad"})
            st.dataframe(vista[["id_consultorio", "nombre", "ubicacion", "especialidad"]],
                         use_container_width=True, hide_index=True)
            st.caption(f"Total de consultorios: {len(consultorios)}")

        with sub_nuevo_cons:
            if especialidades.empty:
                st.warning("Registra primero al menos una especialidad.")
            else:
                with st.form("form_consultorio", clear_on_submit=True):
                    nombre = st.text_input("Nombre del consultorio")
                    ubicacion = st.text_input("Ubicación")
                    esp_opts = {r.nombre: r.id_especialidad for r in especialidades.itertuples()}
                    especialidad = st.selectbox("Especialidad asignada", list(esp_opts.keys()))
                    enviado = st.form_submit_button("Agregar consultorio", type="primary")
                    if enviado:
                        if not nombre:
                            st.error("El nombre es obligatorio.")
                        else:
                            nuevo_id = db.next_id(consultorios, "id_consultorio")
                            db.upsert("consultorios", "id_consultorio", {
                                "id_consultorio": nuevo_id, "nombre": nombre, "ubicacion": ubicacion,
                                "id_especialidad": esp_opts[especialidad],
                            })
                            st.success("Consultorio agregado.")
                            st.rerun()

        with sub_editar_cons:
            if consultorios.empty:
                st.info("No hay consultorios registrados todavía.")
            elif especialidades.empty:
                st.warning("Registra primero al menos una especialidad.")
            else:
                opts = {f"{r.id_consultorio} - {r.nombre}": r.id_consultorio
                        for r in consultorios.itertuples()}
                sel = st.selectbox("Selecciona un consultorio", list(opts.keys()), key="sel_editar_cons")
                id_sel = opts[sel]
                reg = consultorios[consultorios.id_consultorio == id_sel].iloc[0]
                with st.form("form_editar_consultorio"):
                    nombre = st.text_input("Nombre del consultorio", reg["nombre"])
                    ubicacion = st.text_input("Ubicación", reg["ubicacion"])
                    esp_opts = {r.nombre: r.id_especialidad for r in especialidades.itertuples()}
                    nombres_esp = list(esp_opts.keys())
                    idx_esp = 0
                    esp_actual = especialidades[especialidades.id_especialidad == reg["id_especialidad"]]
                    if not esp_actual.empty and esp_actual.iloc[0]["nombre"] in nombres_esp:
                        idx_esp = nombres_esp.index(esp_actual.iloc[0]["nombre"])
                    especialidad = st.selectbox("Especialidad asignada", nombres_esp, index=idx_esp)

                    col_g, col_e = st.columns(2)
                    guardar = col_g.form_submit_button("Guardar cambios", type="primary")
                    eliminar = col_e.form_submit_button("Eliminar consultorio")

                    if guardar:
                        if not nombre:
                            st.error("El nombre es obligatorio.")
                        else:
                            db.upsert("consultorios", "id_consultorio", {
                                "id_consultorio": id_sel, "nombre": nombre, "ubicacion": ubicacion,
                                "id_especialidad": esp_opts[especialidad],
                            })
                            st.success("Consultorio actualizado.")
                            st.rerun()

                    if eliminar:
                        dependientes = db.referencias_activas(id_sel, [("citas", "id_consultorio")])
                        if dependientes:
                            theme.aviso_en_uso(dependientes, "eliminar este consultorio")
                        else:
                            db.delete_row("consultorios", "id_consultorio", id_sel)
                            st.warning("Consultorio eliminado.")
                            st.rerun()
