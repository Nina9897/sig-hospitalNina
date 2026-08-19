import streamlit as st
import pandas as pd
from datetime import date
from utils import storage as db
from utils import graficas as g
from utils import theme


def render():
    theme.encabezado("Tratamientos y Medicamentos",
                      "Catálogo de medicamentos y tratamientos asignados")
    tab_meds, tab_trat_lista, tab_trat_nuevo, tab_trat_editar = st.tabs(
        ["Catálogo de medicamentos", "Tratamientos asignados", "Asignar tratamiento", "Editar / Eliminar"])

    medicamentos = db.load("medicamentos")
    tratamientos = db.load("tratamientos")
    consultas = db.load("consultas")
    pacientes = db.load("pacientes")

    with tab_meds:
        st.dataframe(medicamentos, use_container_width=True, hide_index=True)
        bajo_stock = medicamentos[medicamentos["stock"] < 50] if not medicamentos.empty else medicamentos
        if not bajo_stock.empty:
            st.warning(f"{len(bajo_stock)} medicamento(s) con stock bajo (menos de 50 unidades).")

        sub_nuevo_med, sub_editar_med = st.tabs(["Agregar medicamento", "Editar / Eliminar"])

        with sub_nuevo_med:
            with st.form("form_medicamento", clear_on_submit=True):
                c1, c2 = st.columns(2)
                nombre = c1.text_input("Nombre del medicamento")
                presentacion = c2.text_input("Presentación (tableta, jarabe...)")
                c3, c4 = st.columns(2)
                stock = c3.number_input("Stock inicial", min_value=0, step=1)
                precio = c4.number_input("Precio unitario", min_value=0.0, step=0.1)
                enviado = st.form_submit_button("Agregar medicamento", type="primary")
                if enviado:
                    if not nombre:
                        st.error("El nombre del medicamento es obligatorio.")
                    else:
                        nuevo_id = db.next_id(medicamentos, "id_medicamento")
                        db.upsert("medicamentos", "id_medicamento", {
                            "id_medicamento": nuevo_id, "nombre": nombre, "presentacion": presentacion,
                            "stock": stock, "precio_unitario": precio,
                        })
                        st.success("Medicamento agregado al catálogo.")
                        st.rerun()

        with sub_editar_med:
            if medicamentos.empty:
                st.info("No hay medicamentos registrados todavía.")
            else:
                opts = {f"{r.id_medicamento} - {r.nombre}": r.id_medicamento for r in medicamentos.itertuples()}
                sel = st.selectbox("Selecciona un medicamento", list(opts.keys()))
                id_sel = opts[sel]
                reg = medicamentos[medicamentos.id_medicamento == id_sel].iloc[0]
                with st.form("form_editar_medicamento"):
                    c1, c2 = st.columns(2)
                    nombre = c1.text_input("Nombre del medicamento", reg["nombre"])
                    presentacion = c2.text_input("Presentación", reg["presentacion"] if pd.notna(reg["presentacion"]) else "")
                    c3, c4 = st.columns(2)
                    stock = c3.number_input("Stock", min_value=0, step=1, value=int(reg["stock"]))
                    precio = c4.number_input("Precio unitario", min_value=0.0, step=0.1, value=float(reg["precio_unitario"]))
                    col_g, col_e = st.columns(2)
                    guardar = col_g.form_submit_button("Guardar cambios", type="primary")
                    eliminar = col_e.form_submit_button("Eliminar medicamento")

                    if guardar:
                        if not nombre:
                            st.error("El nombre del medicamento es obligatorio.")
                        else:
                            db.upsert("medicamentos", "id_medicamento", {
                                "id_medicamento": id_sel, "nombre": nombre, "presentacion": presentacion,
                                "stock": stock, "precio_unitario": precio,
                            })
                            st.success("Medicamento actualizado.")
                            st.rerun()

                    if eliminar:
                        dependientes = db.referencias_activas(id_sel, [("tratamientos", "id_medicamento")])
                        if dependientes:
                            theme.aviso_en_uso(dependientes, "eliminar este medicamento")
                        else:
                            db.delete_row("medicamentos", "id_medicamento", id_sel)
                            st.warning("Medicamento eliminado.")
                            st.rerun()

    with tab_trat_lista:
        if tratamientos.empty:
            st.info("No hay tratamientos asignados todavía.")
        else:
            v = tratamientos.merge(pacientes[["id_paciente", "nombre", "apellido"]], on="id_paciente", how="left")
            v = v.merge(medicamentos[["id_medicamento", "nombre"]], on="id_medicamento", how="left",
                        suffixes=("", "_med"))
            v["paciente"] = v["nombre"] + " " + v["apellido"]
            v = v.rename(columns={"nombre_med": "medicamento"})
            cols = ["id_tratamiento", "fecha", "paciente", "medicamento", "dosis",
                    "frecuencia", "duracion_dias", "indicaciones"]
            st.dataframe(v[[c for c in cols if c in v.columns]].sort_values("fecha", ascending=False),
                         use_container_width=True, hide_index=True)

            st.subheader("Medicamentos más utilizados")
            st.caption("Los medicamentos que más se han recetado en los tratamientos asignados, "
                       "de mayor a menor uso.")
            veces = v["medicamento"].value_counts().rename_axis("nombre").reset_index(name="veces_recetado")
            top_medicamentos = veces.sort_values("veces_recetado", ascending=False).head(10)
            g.chip("barras")
            st.plotly_chart(
                g.barras(top_medicamentos.set_index("nombre")["veces_recetado"], horizontal=True),
                use_container_width=True)

    with tab_trat_nuevo:
        if consultas.empty:
            st.warning("Primero registra una consulta médica en el módulo de Consultas.")
            return
        if medicamentos.empty:
            st.warning("Registra al menos un medicamento en el catálogo.")
            return

        v = consultas.merge(pacientes[["id_paciente", "nombre", "apellido"]], on="id_paciente", how="left")
        opts = {f"Consulta {r.id_consulta}: {r.nombre} {r.apellido} ({r.fecha})": r.id_consulta
                for r in v.itertuples()}
        consulta_sel = st.selectbox("Selecciona la consulta", list(opts.keys()))
        id_consulta_sel = opts[consulta_sel]
        consulta_reg = consultas[consultas.id_consulta == id_consulta_sel].iloc[0]

        with st.form("form_nuevo_tratamiento"):
            med_opts = {r.nombre: r.id_medicamento for r in medicamentos.itertuples()}
            medicamento_sel = st.selectbox("Medicamento", list(med_opts.keys()))
            c1, c2 = st.columns(2)
            dosis = c1.text_input("Dosis", placeholder="1 tableta")
            frecuencia = c2.selectbox("Frecuencia", ["Cada 8 horas", "Cada 12 horas", "Cada 24 horas", "Según necesidad"])
            duracion = st.number_input("Duración (días)", min_value=1, step=1, value=7)
            indicaciones = st.text_area("Indicaciones adicionales")
            enviado = st.form_submit_button("Asignar tratamiento", type="primary")

            if enviado:
                nuevo_id = db.next_id(tratamientos, "id_tratamiento")
                db.upsert("tratamientos", "id_tratamiento", {
                    "id_tratamiento": nuevo_id, "id_consulta": id_consulta_sel,
                    "id_paciente": consulta_reg["id_paciente"], "id_medicamento": med_opts[medicamento_sel],
                    "dosis": dosis, "frecuencia": frecuencia, "duracion_dias": duracion,
                    "indicaciones": indicaciones, "fecha": str(date.today()),
                })
                st.success("Tratamiento asignado correctamente.")
                st.rerun()

    with tab_trat_editar:
        if tratamientos.empty:
            st.info("No hay tratamientos asignados todavía.")
        elif medicamentos.empty:
            st.warning("No hay medicamentos en el catálogo.")
        else:
            v = tratamientos.merge(pacientes[["id_paciente", "nombre", "apellido"]], on="id_paciente", how="left")
            opts = {f"{r.id_tratamiento} - {r.nombre} {r.apellido} ({r.fecha})": r.id_tratamiento
                    for r in v.itertuples()}
            sel = st.selectbox("Selecciona un tratamiento", list(opts.keys()))
            id_sel = opts[sel]
            reg = tratamientos[tratamientos.id_tratamiento == id_sel].iloc[0]

            with st.form("form_editar_tratamiento"):
                med_opts = {r.nombre: r.id_medicamento for r in medicamentos.itertuples()}
                nombres_med = list(med_opts.keys())
                idx_med = next((i for i, k in enumerate(nombres_med)
                                 if med_opts[k] == reg["id_medicamento"]), 0)
                medicamento_sel = st.selectbox("Medicamento", nombres_med, index=idx_med)
                c1, c2 = st.columns(2)
                dosis = c1.text_input("Dosis", reg["dosis"] if pd.notna(reg["dosis"]) else "")
                frecuencias = ["Cada 8 horas", "Cada 12 horas", "Cada 24 horas", "Según necesidad"]
                idx_frec = frecuencias.index(reg["frecuencia"]) if reg["frecuencia"] in frecuencias else 0
                frecuencia = c2.selectbox("Frecuencia", frecuencias, index=idx_frec)
                duracion = st.number_input("Duración (días)", min_value=1, step=1, value=int(reg["duracion_dias"]))
                indicaciones = st.text_area("Indicaciones adicionales",
                                             reg["indicaciones"] if pd.notna(reg["indicaciones"]) else "")

                col_g, col_e = st.columns(2)
                guardar = col_g.form_submit_button("Guardar cambios", type="primary")
                eliminar = col_e.form_submit_button("Eliminar tratamiento")

                if guardar:
                    db.upsert("tratamientos", "id_tratamiento", {
                        "id_tratamiento": id_sel, "id_consulta": reg["id_consulta"],
                        "id_paciente": reg["id_paciente"], "id_medicamento": med_opts[medicamento_sel],
                        "dosis": dosis, "frecuencia": frecuencia, "duracion_dias": duracion,
                        "indicaciones": indicaciones, "fecha": reg["fecha"],
                    })
                    st.success("Tratamiento actualizado.")
                    st.rerun()

                if eliminar:
                    db.delete_row("tratamientos", "id_tratamiento", id_sel)
                    st.warning("Tratamiento eliminado.")
                    st.rerun()
