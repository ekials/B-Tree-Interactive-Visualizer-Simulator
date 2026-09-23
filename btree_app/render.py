from __future__ import annotations

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

BG = "#FBF4E8"
BORDER = "#8B5E34"
TEXT = "#5C3A21"
EDGE = "#A97C50"
HILITE_BG = "#F6C453"
HILITE_BORDER = "#B5480A"

BASE_GAP = 0.70          
BASE_CELL_H = 0.90       
BASE_ROW_GAP = 1.65      
CELL_INNER_PAD = 0.05

TARGET_CELL_IN = 0.40
MIN_CELL_IN = 0.18


def _layout(root):
    positions = {}
    cursor = [0.0]

    def rec(node, depth):
        w = max(len(node.keys), 1)
        if node.leaf or not node.children:
            start = cursor[0]
            cursor[0] += w + BASE_GAP
            x = start + w / 2.0
            positions[id(node)] = {"x": x, "depth": depth, "w": w}
            return x
        xs = [rec(c, depth + 1) for c in node.children]
        x = sum(xs) / len(xs)
        positions[id(node)] = {"x": x, "depth": depth, "w": w}
        return x

    rec(root, 0)
    total_width = max(cursor[0] - BASE_GAP, 1.0)
    maxdepth = max(p["depth"] for p in positions.values())
    return positions, total_width, maxdepth


def _axes_size_inches(ax):
    try:
        fig = ax.figure
        fig.canvas.draw()
        bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
        return max(bbox.width, 0.5), max(bbox.height, 0.5)
    except Exception:
        return 7.0, 5.0


def render_tree(root, ax, touched=None, axes_width_in=None, axes_height_in=None):
    touched = set(touched) if touched else set()
    positions, total_width, maxdepth = _layout(root)

    if axes_width_in is None or axes_height_in is None:
        w_in, h_in = _axes_size_inches(ax)
        if axes_width_in is not None:
            w_in = axes_width_in
        if axes_height_in is not None:
            h_in = axes_height_in
    else:
        w_in, h_in = axes_width_in, axes_height_in

    margin_x, margin_y = 0.05, 0.08
    usable_w = w_in * (1 - 2 * margin_x)
    usable_h = h_in * (1 - 2 * margin_y)

    layout_h = maxdepth * BASE_ROW_GAP + BASE_CELL_H
    layout_w = total_width

    scale_fit = min(
        usable_w / max(layout_w, 0.01),
        usable_h / max(layout_h, 0.01),
    )
    scale = min(scale_fit, TARGET_CELL_IN)   
    scale = max(scale, MIN_CELL_IN * 0.5)   

    cell_h = BASE_CELL_H
    row_gap = BASE_ROW_GAP
    gap = BASE_GAP

    cell_w_in = scale * 1.0
    fontsize = max(5.0, min(9.5, cell_w_in * 22))

    def center(node_id):
        p = positions[node_id]
        return p["x"], -p["depth"] * row_gap

    def draw_edges(node):
        if node.leaf or not node.children:
            return
        p = positions[id(node)]
        x, y, w = p["x"], -p["depth"] * row_gap, p["w"]
        left = x - w / 2.0
        y0 = y - cell_h / 2
        for idx, c in enumerate(node.children):
            anchor_x = left + idx
            cx, cy = center(id(c))
            y1 = cy + cell_h / 2
            ax.annotate(
                "",
                xy=(cx, y1),
                xytext=(anchor_x, y0),
                arrowprops=dict(
                    arrowstyle="-|>",
                    color=EDGE,
                    lw=1.0,
                    shrinkA=0,
                    shrinkB=0,
                    mutation_scale=7,
                ),
                zorder=1,
            )
            draw_edges(c)

    draw_edges(root)

    def draw_nodes(node):
        p = positions[id(node)]
        x, depth, w = p["x"], p["depth"], p["w"]
        y = -depth * row_gap
        left = x - w / 2.0
        n = len(node.keys)

        for j, key in enumerate(node.keys):
            cx0 = left + j
            is_hot = key in touched
            face = HILITE_BG if is_hot else BG
            edge = HILITE_BORDER if is_hot else BORDER
            lw = 2.0 if is_hot else 1.15

            if n == 1 or j == 0 or j == n - 1:
                boxstyle = "round,pad=0.015,rounding_size=0.10"
            else:
                boxstyle = "square,pad=0.015"

            rect = mpatches.FancyBboxPatch(
                (cx0 + CELL_INNER_PAD, y - cell_h / 2),
                1.0 - 2 * CELL_INNER_PAD,
                cell_h,
                boxstyle=boxstyle,
                facecolor=face,
                edgecolor=edge,
                linewidth=lw,
                zorder=2,
            )
            ax.add_patch(rect)
            ax.text(
                cx0 + 0.5, y, str(key),
                ha="center", va="center",
                fontsize=fontsize,
                family="DejaVu Sans",
                color=TEXT,
                fontweight="bold" if is_hot else "normal",
                zorder=3,
            )

        for c in node.children:
            draw_nodes(c)

    draw_nodes(root)

    view_w = max(layout_w, usable_w / scale)
    view_h = max(layout_h, usable_h / scale)

    mid_x = total_width / 2.0
    ax.set_xlim(mid_x - view_w / 2 - gap * 0.15, mid_x + view_w / 2 + gap * 0.15)

    top = cell_h * 0.55
    bottom = -maxdepth * row_gap - cell_h * 0.55
    content_h = top - bottom
    if view_h > content_h:
        extra = (view_h - content_h) / 2
        ax.set_ylim(bottom - extra, top + extra)
    else:
        ax.set_ylim(bottom, top)

    ax.set_aspect("equal")  
    ax.axis("off")


def save_single_png(root, path, touched=None, figsize=(9, 5)):
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_alpha(0)
    render_tree(
        root, ax, touched=touched,
        axes_width_in=figsize[0] * 0.92,
        axes_height_in=figsize[1] * 0.90,
    )
    fig.savefig(path, dpi=160, bbox_inches="tight", transparent=True)
    plt.close(fig)
