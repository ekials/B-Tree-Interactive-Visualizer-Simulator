from __future__ import annotations

import io
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import matplotlib.pyplot as plt

from btree_app.model import BTree
from btree_app.render import render_tree
from btree_app.pdf_export import export_pdf

st.set_page_config(page_title="Simulador de Arbol B", page_icon=None, layout="centered")

st.markdown(
    """
    <style>
    .stApp { background-color: #FBF4E8; }
    h1, h2, h3 { color: #5C3A21; font-family: 'Trebuchet MS', sans-serif; }
    .step-box { background: #FFF8EC; border: 1px solid #D9BE96; border-radius: 10px;
                padding: 14px 18px; font-size: 0.92rem; color: #4A3018; white-space: pre-wrap; }
    div.stButton > button, div.stFormSubmitButton > button {
        background-color: #F6E3C3; color: #5C3A21; border: 1px solid #B5804B;
        border-radius: 8px; font-weight: 600;
    }
    div.stButton > button:hover, div.stFormSubmitButton > button:hover {
        background-color: #F0D2A0; border-color: #8B5E34;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Simulador interactivo de Arbol B")
st.caption("Inserta, elimina y busca claves paso a paso, con la explicacion completa del algoritmo.")


def _parse(v):
    try:
        return int(v)
    except ValueError:
        return v


if "bt" not in st.session_state:
    st.session_state.bt = None
    st.session_state.t = 3
if "step_idx" not in st.session_state:
    st.session_state.step_idx = 0

with st.sidebar:
    st.header("Configuracion")
    t_val = st.number_input(
        "Grado minimo t", min_value=2, max_value=8, value=st.session_state.t, step=1
    )
    if st.button("Reiniciar arbol con este t"):
        st.session_state.bt = BTree(int(t_val))
        st.session_state.t = int(t_val)
        st.session_state.step_idx = 0
        st.rerun()

    st.divider()
    n_ops = len(st.session_state.bt.history) if st.session_state.bt else 0
    st.markdown(f"**Historial:** {n_ops} operacion(es)")

    if st.session_state.bt and st.session_state.bt.history:
      
        try:
            tmp_dir = tempfile.gettempdir()
            tmp_path = str(Path(tmp_dir) / "_btree_export.pdf")
            export_pdf(st.session_state.bt, tmp_path)
            with open(tmp_path, "rb") as f:
                st.download_button(
                    "Exportar historial a PDF",
                    f.read(),
                    file_name="btree_historial.pdf",
                    mime="application/pdf",
                )
        except Exception as e:
            st.caption(f"No se pudo generar el PDF: {e}")

if st.session_state.bt is None:
    st.session_state.bt = BTree(st.session_state.t)

bt = st.session_state.bt

with st.form("op_form", clear_on_submit=True):
    key_in = st.text_input("Clave", placeholder="ej. 25")
    c1, c2, c3 = st.columns(3)
    with c1:
        do_insert = st.form_submit_button("Insertar", use_container_width=True)
    with c2:
        do_delete = st.form_submit_button("Eliminar", use_container_width=True)
    with c3:
        do_search = st.form_submit_button("Buscar", use_container_width=True)

if (do_insert or do_delete or do_search) and not str(key_in).strip():
    st.warning("Escribe una clave antes de presionar el boton.")
elif do_insert and str(key_in).strip():
    bt.insert(_parse(str(key_in).strip()))
    st.session_state.step_idx = len(bt.history) - 1
elif do_delete and str(key_in).strip():
    bt.delete(_parse(str(key_in).strip()))
    st.session_state.step_idx = len(bt.history) - 1
elif do_search and str(key_in).strip():
    bt.search(_parse(str(key_in).strip()))
    st.session_state.step_idx = len(bt.history) - 1

if bt.history:
    n = len(bt.history)

    if st.session_state.step_idx >= n:
        st.session_state.step_idx = n - 1
    if st.session_state.step_idx < 0:
        st.session_state.step_idx = 0

    st.subheader("Explorar historial")

    if n == 1:
        st.caption("Paso 1 de 1")
        st.session_state.step_idx = 0
    else:
        col_a, col_b = st.columns([4, 1])
        with col_a:
            idx = st.slider(
                "Paso",
                min_value=1,
                max_value=n,
                value=min(st.session_state.step_idx + 1, n),
                key="step_slider",
            )
            st.session_state.step_idx = idx - 1
        with col_b:
            st.write("")
            if st.button("Ultimo", use_container_width=True):
                st.session_state.step_idx = n - 1
                st.rerun()

    entry = bt.history[st.session_state.step_idx]
    tree_to_show = entry["tree"]
    touched = entry.get("touched") or set()
    titulo_paso = f"Paso {st.session_state.step_idx + 1} de {n}: {entry['title']}"
else:
    tree_to_show = bt.root
    touched = set()
    titulo_paso = None

st.subheader("Arbol")
fig, ax = plt.subplots(figsize=(8, 4.2))
fig.patch.set_facecolor("#FBF4E8")
ax.set_facecolor("#FBF4E8")
render_tree(
    tree_to_show,
    ax,
    touched=touched,
    axes_width_in=8 * 0.92,
    axes_height_in=4.2 * 0.90,
)
st.pyplot(fig, use_container_width=True)
plt.close(fig)

if titulo_paso:
    st.subheader(titulo_paso)
    entry = bt.history[st.session_state.step_idx]

    proc = entry.get("process")
    if proc:
        labels = {"split": "SPLIT", "merge": "MERGE", "borrow": "BORROW"}
        st.info(f"Esta operacion incluyo un reordenamiento: **{labels.get(proc, proc)}**")
    st.markdown(f'<div class="step-box">{entry["text"]}</div>', unsafe_allow_html=True)
    with st.expander(f"Indice de pasos ({len(bt.history)})"):
        for i, h in enumerate(bt.history, start=1):
            tag = ""
            if h.get("process"):
                tag = f"  [{h['process'].upper()}]"
            st.markdown(f"{i}. {h['title']}{tag}")
else:
    st.info("Ingresa una clave y presiona Insertar, Eliminar o Buscar para comenzar.")
