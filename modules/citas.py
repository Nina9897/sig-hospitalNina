import streamlit as st
import pandas as pd
from datetime import date, time
from utils import storage as db
from utils import theme

ESTADOS = ["Pendiente", "Confirmada", "Completada", "Cancelada", "No Asistió"]


def _vista_enriquecida(citas, pacientes, medicos, especialidades, consultorios):
    if citas.empty:
        return citas
    v = citas.merge(pacientes[["id_paciente", "nombre", "apellido"]], on="id_paciente", how="left")
    v = v.rename(columns={"nombre": "paciente_nombre", "apellido": "paciente_apellido"})
    v = v.merge(medicos[["id_medico", "nombre", "apellido", "id_especialidad"]], on="id_medico", how="left")
    v = v.rename(columns={"nombre": "medico_nombre", "apellido": "medico_apellido"})
    v = v.merge(especialidades[["id_especialidad", "nombre"]], on="id_especialidad", how="left")
    v = v.rename(columns={"nombre": "especialidad"})
    v = v.merge(consultorios[["id_consultorio", "nombre"]], on="id_consultorio", how="left")
    v = v.rename(columns={"nombre": "consultorio"})
    v["paciente"] = v["paciente_nombre"].fillna("") + " " + v["paciente_apellido"].fillna("")
    v["medico"] = "Dr(a). " + v["medico_nombre"].fillna("") + " " + v["medico_apellido"].fillna("")
    return v


def render():
    theme.encabezado("Módulo de Citas", "Agendamiento y seguimiento de citas médicas")

    pacientes = db.load("pacientes")
    medicos = db.load("medicos")
    especialidades = db.load("especialidades")
    consultorios = db.load("consultorios")
    citas = db.load("citas")

    if pacientes.empty or medicos.empty:
        st.warning("Registra al menos un paciente y un médico antes de agendar citas.")
        return

    tab_agenda, tab_nueva, tab_gestion = st.tabs(["Agenda", "Nueva cita", "Gestionar estado"])

    with tab_agenda:
        c1, c2, c3 = st.columns(3)
        fecha_filtro = c1.date_input("Filtrar por fecha", value=None)
        estado_filtro = c2.selectbox("Estado", ["Todos"] + ESTADOS)
        esp_filtro = c3.selectbox("Especialidad", ["Todas"] + especialidades["nombre"].tolist())

        vista = _vista_enriquecida(citas, pacientes, medicos, especialidades, consultorios)
        if not vista.empty:
            if fecha_filtro:
                vista = vista[vista["fecha"] == str(fecha_filtro)]
            if estado_filtro != "Todos":
                vista = vista[vista["estado"] == estado_filtro]
            if esp_filtro != "Todas":
                vista = vista[vista["especialidad"] == esp_filtro]
            cols = ["id_cita", "fecha", "hora", "paciente", "medico", "especialidad",
                    "consultorio", "motivo", "estado"]
            st.dataframe(vista[[c for c in cols if c in vista.columns]].sort_values(["fecha", "hora"]),
                         use_container_width=True, hide_index=True)
        st.caption(f"Total de citas registradas: {len(citas)}")

    with tab_nueva:
        with st.form("form_nueva_cita", clear_on_submit=True):
            pac_opts = {f"{r.id_paciente} - {r.nombre} {r.apellido}": r.id_paciente for r in pacientes.itertuples()}
            paciente_sel = st.selectbox("Paciente", list(pac_opts.keys()))

            med_view = medicos.merge(especialidades, on="id_especialidad", how="left", suffixes=("", "_esp"))
            med_opts = {f"Dr(a). {r.nombre} {r.apellido} ({r.nombre_esp})": r.id_medico
                        for r in med_view.itertuples()}
            medico_sel = st.selectbox("Médico", list(med_opts.keys()))

            id_medico_sel = med_opts[medico_sel]
            id_esp_sel = int(medicos.loc[medicos.id_medico == id_medico_sel, "id_especialidad"].iloc[0])
            cons_validos = consultorios[consultorios.id_especialidad == id_esp_sel]
            if cons_validos.empty:
                cons_validos = consultorios
            cons_opts = {f"{r.nombre} ({r.ubicacion})": r.id_consultorio for r in cons_validos.itertuples()}
            consultorio_sel = st.selectbox("Consultorio", list(cons_opts.keys())) if cons_opts else None

            c1, c2 = st.columns(2)
            fecha_cita = c1.date_input("Fecha de la cita", min_value=date.today())
            hora_cita = c2.time_input("Hora de la cita", value=time(9, 0))
            motivo = st.text_input("Motivo de la cita")

            enviado = st.form_submit_button("Agendar cita", type="primary")
            if enviado:
                nuevo_id = db.next_id(citas, "id_cita")
                db.upsert("citas", "id_cita", {
                    "id_cita": nuevo_id,
                    "id_paciente": pac_opts[paciente_sel],
                    "id_medico": id_medico_sel,
                    "id_consultorio": cons_opts[consultorio_sel] if consultorio_sel else "",
                    "fecha": str(fecha_cita), "hora": hora_cita.strftime("%H:%M"),
                    "motivo": motivo, "estado": "Pendiente",
                    "fecha_registro": str(date.today()),
                })
                st.success(f"Cita agendada con ID {nuevo_id}.")
                st.rerun()

    with tab_gestion:
        if citas.empty:
            st.info("No hay citas registradas.")
        else:
            vista = _vista_enriquecida(citas, pacientes, medicos, especialidades, consultorios)
            opts = {f"{r.id_cita} - {r.paciente} con {r.medico} ({r.fecha} {r.hora})": r.id_cita
                    for r in vista.itertuples()}
            sel = st.selectbox("Selecciona una cita", list(opts.keys()))
            id_sel = opts[sel]
            reg = citas[citas.id_cita == id_sel].iloc[0]

            with st.form("form_editar_cita"):
                pac_opts = {f"{r.id_paciente} - {r.nombre} {r.apellido}": r.id_paciente for r in pacientes.itertuples()}
                nombres_pac = list(pac_opts.keys())
                idx_pac = next((i for i, k in enumerate(nombres_pac) if pac_opts[k] == reg["id_paciente"]), 0)
                paciente_sel = st.selectbox("Paciente", nombres_pac, index=idx_pac)

                med_view = medicos.merge(especialidades, on="id_especialidad", how="left", suffixes=("", "_esp"))
                med_opts = {f"Dr(a). {r.nombre} {r.apellido} ({r.nombre_esp})": r.id_medico
                            for r in med_view.itertuples()}
                nombres_med = list(med_opts.keys())
                idx_med = next((i for i, k in enumerate(nombres_med) if med_opts[k] == reg["id_medico"]), 0)
                medico_sel = st.selectbox("Médico", nombres_med, index=idx_med)

                cons_opts = {f"{r.nombre} ({r.ubicacion})": r.id_consultorio for r in consultorios.itertuples()}
                consultorio_sel = None
                if cons_opts:
                    nombres_cons = list(cons_opts.keys())
                    idx_cons = next((i for i, k in enumerate(nombres_cons) if cons_opts[k] == reg["id_consultorio"]), 0)
                    consultorio_sel = st.selectbox("Consultorio", nombres_cons, index=idx_cons)

                c1, c2 = st.columns(2)
                fecha_cita = c1.date_input("Fecha de la cita", pd.to_datetime(reg["fecha"]).date())
                hora_actual = pd.to_datetime(reg["hora"], format="%H:%M").time() if reg["hora"] else time(9, 0)
                hora_cita = c2.time_input("Hora de la cita", value=hora_actual)
                motivo = st.text_input("Motivo de la cita", reg["motivo"] if pd.notna(reg["motivo"]) else "")
                nuevo_estado = st.selectbox("Estado", ESTADOS, index=ESTADOS.index(reg["estado"]))

                col_g, col_e = st.columns(2)
                guardar = col_g.form_submit_button("Guardar cambios", type="primary")
                eliminar = col_e.form_submit_button("Eliminar cita")

                if guardar:
                    db.upsert("citas", "id_cita", {
                        "id_cita": id_sel,
                        "id_paciente": pac_opts[paciente_sel],
                        "id_medico": med_opts[medico_sel],
                        "id_consultorio": cons_opts[consultorio_sel] if consultorio_sel else reg["id_consultorio"],
                        "fecha": str(fecha_cita), "hora": hora_cita.strftime("%H:%M"),
                        "motivo": motivo, "estado": nuevo_estado,
                        "fecha_registro": reg["fecha_registro"],
                    })
                    st.success("Cita actualizada correctamente.")
                    st.rerun()

                if eliminar:
                    dependientes = db.referencias_activas(id_sel, [("consultas", "id_cita")])
                    if dependientes:
                        theme.aviso_en_uso(dependientes, "eliminar esta cita")
                    else:
                        db.delete_row("citas", "id_cita", id_sel)
                        st.warning("Cita eliminada.")
                        st.rerun()
