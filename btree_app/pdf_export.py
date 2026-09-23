from __future__ import annotations

import textwrap
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from .render import render_tree

A4 = (8.27, 11.69)

PROCESS_LABEL = {
    "split": "SPLIT",
    "merge": "MERGE",
    "borrow": "BORROW",
}
PROCESS_COLOR = {
    "split": "#2E7D32",
    "merge": "#1565C0",
    "borrow": "#E65100",
}


def _wrap(text, width=90):
    out = []
    for line in text.split("\n"):
        wrapped = textwrap.wrap(line, width=width, subsequent_indent="   ")
        out.extend(wrapped if wrapped else [""])
    return "\n".join(out)


def _draw_arrow_panel(ax, label, color):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.annotate(
        "",
        xy=(0.95, 0.45),
        xytext=(0.05, 0.45),
        arrowprops=dict(arrowstyle="-|>", color=color, lw=3.2, mutation_scale=16),
        zorder=2,
    )
    ax.text(
        0.5, 0.78, label,
        ha="center", va="center",
        fontsize=9, fontweight="bold", color=color,
        family="DejaVu Sans",
        bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor=color, lw=1.4),
        zorder=3,
    )
    ax.text(
        0.5, 0.12, "reordenamiento",
        ha="center", va="center",
        fontsize=6.5, color=color, style="italic",
        family="DejaVu Sans",
    )


def _draw_process_page(fig, entry, idx, total):
    """Página completa bien compacta: título claro + ANTES|flecha|DESPUÉS + narración."""
    process = entry.get("process") or "split"
    color = PROCESS_COLOR.get(process, "#2E7D32")
    label = PROCESS_LABEL.get(process, process.upper())

    ax_t = fig.add_axes([0.05, 0.935, 0.90, 0.045])
    ax_t.set_xlim(0, 1)
    ax_t.set_ylim(0, 1)
    ax_t.axis("off")
    ax_t.text(
        0, 0.55,
        f"Paso {idx} de {total}:  {entry['title']}    ·    orden t = {entry['t']}    ·    {label}",
        fontsize=10.5, fontweight="bold", color="#5C3A21",
        va="center", ha="left", family="DejaVu Sans",
        transform=ax_t.transAxes, clip_on=True,
    )
    ax_t.plot([0, 1], [0.08, 0.08], color="#C4A574", lw=1.0, transform=ax_t.transAxes)

    ax_lbl = fig.add_axes([0.05, 0.895, 0.90, 0.03])
    ax_lbl.set_xlim(0, 1)
    ax_lbl.set_ylim(0, 1)
    ax_lbl.axis("off")
    ax_lbl.text(0.20, 0.4, "ANTES", ha="center", va="center",
                fontsize=9, fontweight="bold", color="#8B5E34", family="DejaVu Sans",
                transform=ax_lbl.transAxes)
    ax_lbl.text(0.80, 0.4, "DESPUES", ha="center", va="center",
                fontsize=9, fontweight="bold", color="#8B5E34", family="DejaVu Sans",
                transform=ax_lbl.transAxes)

    tree_bottom, tree_height = 0.50, 0.38

    ax_before = fig.add_axes([0.03, tree_bottom, 0.38, tree_height])
    ax_before.set_facecolor("white")
    before = entry.get("before") or entry["tree"]
    render_tree(
        before, ax_before,
        touched=entry.get("touched"),
        axes_width_in=A4[0] * 0.38,
        axes_height_in=A4[1] * tree_height,
    )

    ax_mid = fig.add_axes([0.42, tree_bottom + tree_height * 0.25, 0.16, tree_height * 0.50])
    _draw_arrow_panel(ax_mid, label, color)

    ax_after = fig.add_axes([0.59, tree_bottom, 0.38, tree_height])
    ax_after.set_facecolor("white")
    render_tree(
        entry["tree"], ax_after,
        touched=entry.get("touched"),
        axes_width_in=A4[0] * 0.38,
        axes_height_in=A4[1] * tree_height,
    )

    ax_txt = fig.add_axes([0.06, 0.03, 0.88, 0.44])
    ax_txt.set_xlim(0, 1)
    ax_txt.set_ylim(0, 1)
    ax_txt.axis("off")

    ax_txt.plot([0, 1], [0.98, 0.98], color="#D9BE96", lw=0.8, transform=ax_txt.transAxes)

    wrapped = _wrap(entry["text"], width=95)
    n_lines = max(wrapped.count("\n") + 1, 1)
    avail_in = A4[1] * 0.42
    linespacing = 1.32
    fit_fs = (avail_in * 72) / (n_lines * linespacing)
    fontsize = max(5.5, min(8.2, fit_fs))

    ax_txt.text(
        0, 0.96, wrapped,
        fontsize=fontsize, va="top", ha="left",
        family="DejaVu Sans", color="#3D2914",
        linespacing=linespacing, clip_on=True,
        transform=ax_txt.transAxes,
    )


def _draw_simple_block(fig, entry, idx, total, y0, y1):
    h = y1 - y0
    left, width = 0.05, 0.90

    ax_t = fig.add_axes([left, y0 + h * 0.92, width, h * 0.07])
    ax_t.set_xlim(0, 1)
    ax_t.set_ylim(0, 1)
    ax_t.axis("off")
    ax_t.text(
        0, 0.45,
        f"Paso {idx} de {total}:  {entry['title']}    ·    orden t = {entry['t']}",
        fontsize=9.5, fontweight="bold", color="#5C3A21",
        va="center", family="DejaVu Sans",
        transform=ax_t.transAxes, clip_on=True,
    )
    ax_t.plot([0, 1], [0.08, 0.08], color="#C4A574", lw=0.9, transform=ax_t.transAxes)

    ax_tree = fig.add_axes([left + 0.01, y0 + h * 0.38, width - 0.02, h * 0.52])
    ax_tree.set_facecolor("white")
    render_tree(
        entry["tree"], ax_tree,
        touched=entry.get("touched"),
        axes_width_in=A4[0] * (width - 0.02),
        axes_height_in=A4[1] * (h * 0.52),
    )

    ax_txt = fig.add_axes([left + 0.02, y0 + 0.008, width - 0.04, h * 0.35])
    ax_txt.set_xlim(0, 1)
    ax_txt.set_ylim(0, 1)
    ax_txt.axis("off")
    wrapped = _wrap(entry["text"], width=86)
    n_lines = max(wrapped.count("\n") + 1, 1)
    avail_in = A4[1] * h * 0.33
    linespacing = 1.32
    fit_fs = (avail_in * 72) / (n_lines * linespacing)
    fontsize = max(4.8, min(7.5, fit_fs))
    ax_txt.text(
        0, 1, wrapped,
        fontsize=fontsize, va="top", ha="left",
        family="DejaVu Sans", color="#3D2914",
        linespacing=linespacing, clip_on=True,
        transform=ax_txt.transAxes,
    )


def _cover_page(pdf, bt):
    fig = plt.figure(figsize=A4)
    fig.patch.set_facecolor("#FBF4E8")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    t = bt.t
    ax.text(0.5, 0.88, "Simulador de Arbol B", fontsize=22, fontweight="bold",
            ha="center", color="#5C3A21", family="DejaVu Sans")
    ax.text(0.5, 0.82, "Historial paso a paso con reordenamientos", fontsize=12,
            ha="center", color="#8B5E34", family="DejaVu Sans")

    ax.add_patch(plt.Rectangle((0.12, 0.55), 0.76, 0.22,
                                facecolor="#FFF8EC", edgecolor="#C4A574", lw=1.5,
                                transform=ax.transAxes, zorder=1))
    ax.text(0.5, 0.73, f"Orden minimo  t  =  {t}", fontsize=14, fontweight="bold",
            ha="center", color="#5C3A21", family="DejaVu Sans", zorder=2)
    ax.text(0.5, 0.66,
            f"Propiedades del Arbol B (grado t = {t}):\n"
            f"• Nodo no-raiz: entre t-1 = {t-1} y 2t-1 = {2*t-1} claves\n"
            f"• Raiz: entre 1 y 2t-1 = {2*t-1} claves\n"
            f"• Factor de ramificacion: entre t y 2t hijos por nodo interno\n"
            f"• Balanceo: todas las hojas al mismo nivel\n"
            f"• SPLIT / MERGE / BORROW se muestran como ANTES → DESPUES",
            fontsize=8.5, ha="center", va="top", color="#5C3A21",
            family="DejaVu Sans", linespacing=1.45, zorder=2)

    ax.text(0.5, 0.50, f"{len(bt.history)} operaciones registradas", fontsize=11,
            ha="center", color="#8B5E34", fontweight="bold", family="DejaVu Sans")

    lines = [f"{i:>3}.  {h['title']}" + (
        f"   [{PROCESS_LABEL.get(h.get('process'),'')}]" if h.get("process") else ""
    ) for i, h in enumerate(bt.history, 1)]
    max_show = 26
    body = "\n".join(lines[:max_show])
    if len(lines) > max_show:
        body += f"\n  ... y {len(lines) - max_show} mas"
    ax.text(0.15, 0.46, body, fontsize=8, va="top", ha="left",
            family="DejaVu Sans", color="#3D2914", linespacing=1.35)

    ax.text(0.5, 0.04,
            "Verde = SPLIT   ·   Azul = MERGE   ·   Naranja = BORROW",
            fontsize=8, ha="center", color="#A97C50", family="DejaVu Sans")

    pdf.savefig(fig, facecolor=fig.get_facecolor())
    plt.close(fig)


def export_pdf(bt, filename="btree_historial.pdf"):
    if not bt.history:
        raise ValueError("No hay operaciones registradas todavia.")

    n = len(bt.history)
    hist = bt.history

    with PdfPages(filename) as pdf:
        _cover_page(pdf, bt)

        i = 0
        while i < n:
            entry = hist[i]
            has_process = bool(entry.get("process") and entry.get("before") is not None)

            if has_process:
                fig = plt.figure(figsize=A4)
                fig.patch.set_facecolor("white")
                _draw_process_page(fig, entry, i + 1, n)
                pdf.savefig(fig, facecolor="white")
                plt.close(fig)
                i += 1
            else:
                fig = plt.figure(figsize=A4)
                fig.patch.set_facecolor("white")
                _draw_simple_block(fig, entry, i + 1, n, y0=0.515, y1=0.975)
                if i + 1 < n and not (hist[i + 1].get("process") and hist[i + 1].get("before") is not None):
                    _draw_simple_block(fig, hist[i + 1], i + 2, n, y0=0.02, y1=0.475)
                    ax_sep = fig.add_axes([0.08, 0.492, 0.84, 0.008])
                    ax_sep.axis("off")
                    ax_sep.axhline(0.5, color="#D9BE96", lw=1.3)
                    i += 2
                else:
                    i += 1
                pdf.savefig(fig, facecolor="white")
                plt.close(fig)

    return filename
