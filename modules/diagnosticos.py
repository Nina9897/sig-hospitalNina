import streamlit as st
import pandas as pd
from utils import storage as db
from utils import graficas as g
from utils import theme


def render():
    theme.encabezado("Catálogo de Diagnósticos",
                      "Catálogo tipo CIE-10 simplificado, utilizado por el módulo de Consultas")

    diagnosticos = db.load("diagnosticos_catalogo")
    consultas = db.load("consultas")

    tab_lista, tab_nuevo, tab_editar = st.tabs(["Catálogo", "Agregar diagnóstico", "Editar / Eliminar"])

    with tab_lista:
        vista = diagnosticos.copy()
        if not consultas.empty and not vista.empty:
            frecuencia = consultas["id_diagnostico"].value_counts().rename_axis("id_diagnostico") \
                .reset_index(name="veces_diagnosticado")
            vista = vista.merge(frecuencia, on="id_diagnostico", how="left")
            vista["veces_diagnosticado"] = vista["veces_diagnosticado"].fillna(0).astype(int)
        st.dataframe(vista, use_container_width=True, hide_index=True)
        st.caption(f"Total de diagnósticos en catálogo: {len(diagnosticos)}")

        if not consultas.empty and not diagnosticos.empty:
            st.subheader("Enfermedades más frecuentes")
            st.caption("Los diagnósticos que más se repiten en las consultas registradas.")
            g.chip("barras")
            top = vista.sort_values("veces_diagnosticado", ascending=False).head(10)
            st.plotly_chart(
                g.barras(top.set_index("nombre")["veces_diagnosticado"], horizontal=True),
                use_container_width=True)

    with tab_nuevo:
        with st.form("form_nuevo_diagnostico", clear_on_submit=True):
            codigo = st.text_input("Código (CIE-10)")
            nombre = st.text_input("Nombre del diagnóstico")
            categoria = st.text_input("Categoría (ej. Respiratorio, Digestivo...)")
            enviado = st.form_submit_button("Agregar al catálogo", type="primary")
            if enviado:
                if not nombre:
                    st.error("El nombre del diagnóstico es obligatorio.")
                else:
                    nuevo_id = db.next_id(diagnosticos, "id_diagnostico")
                    db.upsert("diagnosticos_catalogo", "id_diagnostico", {
                        "id_diagnostico": nuevo_id, "codigo": codigo, "nombre": nombre, "categoria": categoria
                    })
                    st.success("Diagnóstico agregado al catálogo.")
                    st.rerun()

    with tab_editar:
        if diagnosticos.empty:
            st.info("No hay diagnósticos registrados todavía.")
        else:
            opts = {f"{r.id_diagnostico} - {r.codigo} - {r.nombre}": r.id_diagnostico
                    for r in diagnosticos.itertuples()}
            sel = st.selectbox("Selecciona un diagnóstico", list(opts.keys()))
            id_sel = opts[sel]
            reg = diagnosticos[diagnosticos.id_diagnostico == id_sel].iloc[0]

            with st.form("form_editar_diagnostico"):
                codigo = st.text_input("Código (CIE-10)", reg["codigo"] if pd.notna(reg["codigo"]) else "")
                nombre = st.text_input("Nombre del diagnóstico", reg["nombre"])
                categoria = st.text_input("Categoría", reg["categoria"] if pd.notna(reg["categoria"]) else "")
                col_g, col_e = st.columns(2)
                guardar = col_g.form_submit_button("Guardar cambios", type="primary")
                eliminar = col_e.form_submit_button("Eliminar diagnóstico")

                if guardar:
                    if not nombre:
                        st.error("El nombre del diagnóstico es obligatorio.")
                    else:
                        db.upsert("diagnosticos_catalogo", "id_diagnostico", {
                            "id_diagnostico": id_sel, "codigo": codigo, "nombre": nombre, "categoria": categoria
                        })
                        st.success("Diagnóstico actualizado.")
                        st.rerun()

                if eliminar:
                    dependientes = db.referencias_activas(id_sel, [("consultas", "id_diagnostico")])
                    if dependientes:
                        theme.aviso_en_uso(dependientes, "eliminar este diagnóstico")
                    else:
                        db.delete_row("diagnosticos_catalogo", "id_diagnostico", id_sel)
                        st.warning("Diagnóstico eliminado.")
                        st.rerun()
