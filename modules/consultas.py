import streamlit as st
import pandas as pd
from datetime import date
from utils import storage as db
from utils import theme


def render():
    theme.encabezado("Módulo de Consultas Médicas", "Registro de la atención médica brindada")

    citas = db.load("citas")
    pacientes = db.load("pacientes")
    medicos = db.load("medicos")
    consultas = db.load("consultas")
    diagnosticos_cat = db.load("diagnosticos_catalogo")

    tab_lista, tab_nueva, tab_editar = st.tabs(
        ["Historial de consultas", "Registrar consulta", "Editar / Eliminar"])

    with tab_lista:
        if consultas.empty:
            st.info("Aún no hay consultas registradas.")
        else:
            v = consultas.merge(pacientes[["id_paciente", "nombre", "apellido"]], on="id_paciente", how="left")
            v = v.merge(diagnosticos_cat[["id_diagnostico", "nombre"]], on="id_diagnostico", how="left",
                        suffixes=("", "_diag"))
            v["paciente"] = v["nombre"] + " " + v["apellido"]
            v = v.rename(columns={"nombre_diag": "diagnostico"})
            cols = ["id_consulta", "fecha", "paciente", "peso", "talla", "presion",
                    "temperatura", "motivo_consulta", "diagnostico", "observaciones"]
            st.dataframe(v[[c for c in cols if c in v.columns]].sort_values("fecha", ascending=False),
                         use_container_width=True, hide_index=True)
            st.caption(f"Total de consultas registradas: {len(consultas)}")

    with tab_nueva:
        citas_pendientes = citas[citas.estado.isin(["Confirmada", "Pendiente"])] if not citas.empty else citas
        if citas_pendientes.empty:
            st.warning("No hay citas confirmadas/pendientes disponibles para generar una consulta. "
                       "Agenda y confirma una cita primero en el módulo de Citas.")
            return
        if diagnosticos_cat.empty:
            st.warning("Registra primero al menos un diagnóstico en el catálogo (pestaña 'Diagnósticos').")
            return

        v = citas_pendientes.merge(pacientes[["id_paciente", "nombre", "apellido"]], on="id_paciente", how="left")
        v = v.merge(medicos[["id_medico", "nombre", "apellido"]], on="id_medico", how="left",
                    suffixes=("_pac", "_med"))
        opts = {f"Cita {r.id_cita}: {r.nombre_pac} {r.apellido_pac} - Dr(a). {r.nombre_med} ({r.fecha})": r.id_cita
                for r in v.itertuples()}
        cita_sel = st.selectbox("Selecciona la cita a atender", list(opts.keys()))
        id_cita_sel = opts[cita_sel]
        cita_reg = citas[citas.id_cita == id_cita_sel].iloc[0]

        with st.form("form_nueva_consulta"):
            c1, c2, c3, c4 = st.columns(4)
            peso = c1.number_input("Peso (kg)", min_value=0.0, step=0.1)
            talla = c2.number_input("Talla (m)", min_value=0.0, step=0.01)
            presion = c3.text_input("Presión arterial", placeholder="120/80")
            temperatura = c4.number_input("Temperatura (°C)", min_value=30.0, max_value=45.0, value=36.5, step=0.1)
            motivo_consulta = st.text_input("Motivo de la consulta")
            diag_opts = {f"{r.codigo} - {r.nombre}": r.id_diagnostico for r in diagnosticos_cat.itertuples()}
            diagnostico_sel = st.selectbox("Diagnóstico", list(diag_opts.keys()))
            observaciones = st.text_area("Observaciones")
            marcar_completada = st.checkbox("Marcar la cita como Completada", value=True)

            enviado = st.form_submit_button("Registrar consulta", type="primary")
            if enviado:
                nuevo_id = db.next_id(consultas, "id_consulta")
                db.upsert("consultas", "id_consulta", {
                    "id_consulta": nuevo_id, "id_cita": id_cita_sel,
                    "id_paciente": cita_reg["id_paciente"], "id_medico": cita_reg["id_medico"],
                    "fecha": str(date.today()), "peso": peso, "talla": talla,
                    "presion": presion, "temperatura": temperatura,
                    "motivo_consulta": motivo_consulta, "observaciones": observaciones,
                    "id_diagnostico": diag_opts[diagnostico_sel],
                })
                if marcar_completada:
                    actualizado = cita_reg.to_dict()
                    actualizado["estado"] = "Completada"
                    db.upsert("citas", "id_cita", actualizado)
                st.success(f"Consulta registrada con ID {nuevo_id}.")
                st.rerun()

    with tab_editar:
        if consultas.empty:
            st.info("No hay consultas registradas todavía.")
        elif diagnosticos_cat.empty:
            st.warning("Registra primero al menos un diagnóstico en el catálogo.")
        else:
            v = consultas.merge(pacientes[["id_paciente", "nombre", "apellido"]], on="id_paciente", how="left")
            opts = {f"{r.id_consulta} - {r.nombre} {r.apellido} ({r.fecha})": r.id_consulta
                    for r in v.itertuples()}
            sel = st.selectbox("Selecciona una consulta", list(opts.keys()))
            id_sel = opts[sel]
            reg = consultas[consultas.id_consulta == id_sel].iloc[0]

            with st.form("form_editar_consulta"):
                c1, c2, c3, c4 = st.columns(4)
                peso = c1.number_input("Peso (kg)", min_value=0.0, step=0.1, value=float(reg["peso"]))
                talla = c2.number_input("Talla (m)", min_value=0.0, step=0.01, value=float(reg["talla"]))
                presion = c3.text_input("Presión arterial", reg["presion"] if pd.notna(reg["presion"]) else "")
                temperatura = c4.number_input("Temperatura (°C)", min_value=30.0, max_value=45.0, step=0.1,
                                               value=float(reg["temperatura"]))
                motivo_consulta = st.text_input(
                    "Motivo de la consulta", reg["motivo_consulta"] if pd.notna(reg["motivo_consulta"]) else "")
                diag_opts = {f"{r.codigo} - {r.nombre}": r.id_diagnostico for r in diagnosticos_cat.itertuples()}
                nombres_diag = list(diag_opts.keys())
                idx_diag = next((i for i, k in enumerate(nombres_diag)
                                  if diag_opts[k] == reg["id_diagnostico"]), 0)
                diagnostico_sel = st.selectbox("Diagnóstico", nombres_diag, index=idx_diag)
                observaciones = st.text_area(
                    "Observaciones", reg["observaciones"] if pd.notna(reg["observaciones"]) else "")

                col_g, col_e = st.columns(2)
                guardar = col_g.form_submit_button("Guardar cambios", type="primary")
                eliminar = col_e.form_submit_button("Eliminar consulta")

                if guardar:
                    db.upsert("consultas", "id_consulta", {
                        "id_consulta": id_sel, "id_cita": reg["id_cita"],
                        "id_paciente": reg["id_paciente"], "id_medico": reg["id_medico"],
                        "fecha": reg["fecha"], "peso": peso, "talla": talla,
                        "presion": presion, "temperatura": temperatura,
                        "motivo_consulta": motivo_consulta, "observaciones": observaciones,
                        "id_diagnostico": diag_opts[diagnostico_sel],
                    })
                    st.success("Consulta actualizada correctamente.")
                    st.rerun()

                if eliminar:
                    dependientes = db.referencias_activas(id_sel, [("tratamientos", "id_consulta")])
                    if dependientes:
                        theme.aviso_en_uso(dependientes, "eliminar esta consulta")
                    else:
                        db.delete_row("consultas", "id_consulta", id_sel)
                        st.warning("Consulta eliminada.")
                        st.rerun()
