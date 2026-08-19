import streamlit as st
import pandas as pd
from datetime import date
from utils import storage as db
from utils import theme


def render():
    theme.encabezado("Hospitalización", "Ingresos, estancia y altas médicas")

    pacientes = db.load("pacientes")
    medicos = db.load("medicos")
    camas = db.load("camas")
    hosp = db.load("hospitalizaciones")

    tab_activos, tab_ingreso, tab_alta, tab_editar, tab_camas = st.tabs(
        ["Pacientes hospitalizados", "Nuevo ingreso", "Dar de alta", "Editar / Eliminar ingreso", "Camas"])

    disponibles = camas[camas.estado == "Disponible"] if not camas.empty else camas

    if pacientes.empty or medicos.empty or camas.empty:
        st.warning("Se requieren pacientes, médicos y camas registradas para usar este módulo. "
                    "Puedes registrar camas en la pestaña 'Camas'.")
        with tab_camas:
            _render_camas(camas, hosp)
        return

    with tab_activos:
        c1, c2, c3 = st.columns(3)
        c1.metric("Camas totales", len(camas))
        c2.metric("Camas ocupadas", len(camas[camas.estado == "Ocupada"]))
        c3.metric("Camas disponibles", len(disponibles))

        activos = hosp[hosp.estado == "Hospitalizado"] if not hosp.empty else hosp
        if activos.empty:
            st.info("No hay pacientes hospitalizados actualmente.")
        else:
            v = activos.merge(pacientes[["id_paciente", "nombre", "apellido"]], on="id_paciente", how="left")
            v = v.merge(medicos[["id_medico", "nombre", "apellido"]], on="id_medico", how="left",
                        suffixes=("_pac", "_med"))
            v = v.merge(camas[["id_cama", "numero", "area"]], on="id_cama", how="left")
            v["paciente"] = v["nombre_pac"] + " " + v["apellido_pac"]
            v["medico"] = "Dr(a). " + v["nombre_med"] + " " + v["apellido_med"]
            v["dias_internado"] = (pd.Timestamp.today() - pd.to_datetime(v["fecha_ingreso"])).dt.days
            cols = ["id_hospitalizacion", "paciente", "medico", "numero", "area",
                    "fecha_ingreso", "dias_internado", "motivo_ingreso", "diagnostico_ingreso", "costo_diario"]
            st.dataframe(v[[c for c in cols if c in v.columns]], use_container_width=True, hide_index=True)

    with tab_ingreso:
        if disponibles.empty:
            st.error("No hay camas disponibles en este momento.")
        else:
            with st.form("form_ingreso", clear_on_submit=True):
                pac_opts = {f"{r.id_paciente} - {r.nombre} {r.apellido}": r.id_paciente for r in pacientes.itertuples()}
                paciente_sel = st.selectbox("Paciente", list(pac_opts.keys()))
                med_opts = {f"Dr(a). {r.nombre} {r.apellido}": r.id_medico for r in medicos.itertuples()}
                medico_sel = st.selectbox("Médico responsable", list(med_opts.keys()))
                cama_opts = {f"{r.numero} - {r.area}": r.id_cama for r in disponibles.itertuples()}
                cama_sel = st.selectbox("Cama disponible", list(cama_opts.keys()))
                motivo = st.text_input("Motivo de ingreso")
                diagnostico = st.text_input("Diagnóstico de ingreso")
                costo_diario = st.number_input("Costo diario estimado", min_value=0.0, step=50.0, value=1000.0)
                enviado = st.form_submit_button("Registrar ingreso", type="primary")

                if enviado:
                    nuevo_id = db.next_id(hosp, "id_hospitalizacion")
                    db.upsert("hospitalizaciones", "id_hospitalizacion", {
                        "id_hospitalizacion": nuevo_id, "id_paciente": pac_opts[paciente_sel],
                        "id_medico": med_opts[medico_sel], "id_cama": cama_opts[cama_sel],
                        "fecha_ingreso": str(date.today()), "motivo_ingreso": motivo,
                        "diagnostico_ingreso": diagnostico, "costo_diario": costo_diario,
                        "fecha_alta": "", "estado": "Hospitalizado",
                    })
                    camas.loc[camas.id_cama == cama_opts[cama_sel], "estado"] = "Ocupada"
                    db.save("camas", camas)
                    st.success(f"Ingreso registrado con ID {nuevo_id}. Cama {cama_sel} marcada como ocupada.")
                    st.rerun()

    with tab_alta:
        activos = hosp[hosp.estado == "Hospitalizado"] if not hosp.empty else hosp
        if activos.empty:
            st.info("No hay pacientes hospitalizados para dar de alta.")
        else:
            v = activos.merge(pacientes[["id_paciente", "nombre", "apellido"]], on="id_paciente", how="left")
            opts = {f"{r.id_hospitalizacion} - {r.nombre} {r.apellido}": r.id_hospitalizacion for r in v.itertuples()}
            sel = st.selectbox("Selecciona al paciente", list(opts.keys()))
            id_sel = opts[sel]
            reg = hosp[hosp.id_hospitalizacion == id_sel].iloc[0]

            dias = (pd.Timestamp.today() - pd.to_datetime(reg["fecha_ingreso"])).days
            costo_total = dias * float(reg["costo_diario"])
            st.metric("Días de estancia", dias)
            st.metric("Costo estimado total", f"${costo_total:,.2f}")

            if st.button("Confirmar alta médica", type="primary"):
                actualizado = reg.to_dict()
                actualizado["fecha_alta"] = str(date.today())
                actualizado["estado"] = "Alta"
                db.upsert("hospitalizaciones", "id_hospitalizacion", actualizado)
                camas.loc[camas.id_cama == reg["id_cama"], "estado"] = "Disponible"
                db.save("camas", camas)
                st.success("Paciente dado de alta. La cama quedó disponible nuevamente.")
                st.rerun()

    with tab_editar:
        if hosp.empty:
            st.info("No hay hospitalizaciones registradas todavía.")
        else:
            v = hosp.merge(pacientes[["id_paciente", "nombre", "apellido"]], on="id_paciente", how="left")
            opts = {f"{r.id_hospitalizacion} - {r.nombre} {r.apellido} ({r.fecha_ingreso}) [{r.estado}]": r.id_hospitalizacion
                    for r in v.itertuples()}
            sel = st.selectbox("Selecciona una hospitalización", list(opts.keys()))
            id_sel = opts[sel]
            reg = hosp[hosp.id_hospitalizacion == id_sel].iloc[0]

            with st.form("form_editar_hospitalizacion"):
                med_opts = {f"Dr(a). {r.nombre} {r.apellido}": r.id_medico for r in medicos.itertuples()}
                nombres_med = list(med_opts.keys())
                idx_med = next((i for i, k in enumerate(nombres_med) if med_opts[k] == reg["id_medico"]), 0)
                medico_sel = st.selectbox("Médico responsable", nombres_med, index=idx_med)
                motivo = st.text_input("Motivo de ingreso", reg["motivo_ingreso"] if pd.notna(reg["motivo_ingreso"]) else "")
                diagnostico = st.text_input(
                    "Diagnóstico de ingreso", reg["diagnostico_ingreso"] if pd.notna(reg["diagnostico_ingreso"]) else "")
                costo_diario = st.number_input("Costo diario estimado", min_value=0.0, step=50.0,
                                                value=float(reg["costo_diario"]))
                st.caption(f"Estado actual: **{reg['estado']}** — el estado y la cama se administran "
                           "desde 'Nuevo ingreso' y 'Dar de alta'.")

                col_g, col_e = st.columns(2)
                guardar = col_g.form_submit_button("Guardar cambios", type="primary")
                eliminar = col_e.form_submit_button("Eliminar registro")

                if guardar:
                    db.upsert("hospitalizaciones", "id_hospitalizacion", {
                        "id_hospitalizacion": id_sel, "id_paciente": reg["id_paciente"],
                        "id_medico": med_opts[medico_sel], "id_cama": reg["id_cama"],
                        "fecha_ingreso": reg["fecha_ingreso"], "motivo_ingreso": motivo,
                        "diagnostico_ingreso": diagnostico, "costo_diario": costo_diario,
                        "fecha_alta": reg["fecha_alta"], "estado": reg["estado"],
                    })
                    st.success("Hospitalización actualizada.")
                    st.rerun()

                if eliminar:
                    if reg["estado"] == "Hospitalizado":
                        camas.loc[camas.id_cama == reg["id_cama"], "estado"] = "Disponible"
                        db.save("camas", camas)
                    db.delete_row("hospitalizaciones", "id_hospitalizacion", id_sel)
                    st.warning("Registro de hospitalización eliminado. Si la cama estaba ocupada, "
                               "quedó disponible nuevamente.")
                    st.rerun()

    with tab_camas:
        _render_camas(camas, hosp)


def _render_camas(camas, hosp):
    """Alta, edición y baja del catálogo de camas."""
    sub_lista, sub_nueva, sub_editar = st.tabs(["Listado", "Nueva cama", "Editar / Eliminar"])

    with sub_lista:
        st.dataframe(camas, use_container_width=True, hide_index=True)
        st.caption(f"Total de camas: {len(camas)}")

    with sub_nueva:
        with st.form("form_nueva_cama", clear_on_submit=True):
            c1, c2 = st.columns(2)
            numero = c1.text_input("Número de cama")
            area = c2.text_input("Área (ej. Urgencias, Pediatría, UCI...)")
            estado = st.selectbox("Estado inicial", ["Disponible", "Ocupada", "Mantenimiento"])
            enviado = st.form_submit_button("Agregar cama", type="primary")
            if enviado:
                if not numero:
                    st.error("El número de cama es obligatorio.")
                else:
                    nuevo_id = db.next_id(camas, "id_cama")
                    db.upsert("camas", "id_cama", {
                        "id_cama": nuevo_id, "numero": numero, "area": area, "estado": estado,
                    })
                    st.success("Cama agregada.")
                    st.rerun()

    with sub_editar:
        if camas.empty:
            st.info("No hay camas registradas todavía.")
        else:
            opts = {f"{r.id_cama} - {r.numero} ({r.area})": r.id_cama for r in camas.itertuples()}
            sel = st.selectbox("Selecciona una cama", list(opts.keys()))
            id_sel = opts[sel]
            reg = camas[camas.id_cama == id_sel].iloc[0]

            with st.form("form_editar_cama"):
                numero = st.text_input("Número de cama", reg["numero"])
                area = st.text_input("Área", reg["area"] if pd.notna(reg["area"]) else "")
                estados = ["Disponible", "Ocupada", "Mantenimiento"]
                idx_estado = estados.index(reg["estado"]) if reg["estado"] in estados else 0
                estado = st.selectbox("Estado", estados, index=idx_estado)

                col_g, col_e = st.columns(2)
                guardar = col_g.form_submit_button("Guardar cambios", type="primary")
                eliminar = col_e.form_submit_button("Eliminar cama")

                if guardar:
                    if not numero:
                        st.error("El número de cama es obligatorio.")
                    else:
                        db.upsert("camas", "id_cama", {
                            "id_cama": id_sel, "numero": numero, "area": area, "estado": estado,
                        })
                        st.success("Cama actualizada.")
                        st.rerun()

                if eliminar:
                    if reg["estado"] == "Ocupada":
                        st.error("No se puede eliminar una cama Ocupada. Cambia su estado o da de alta "
                                 "al paciente primero.")
                    else:
                        dependientes = db.referencias_activas(id_sel, [("hospitalizaciones", "id_cama")])
                        if dependientes:
                            theme.aviso_en_uso(dependientes, "eliminar esta cama")
                        else:
                            db.delete_row("camas", "id_cama", id_sel)
                            st.warning("Cama eliminada.")
                            st.rerun()
