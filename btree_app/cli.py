from .model import BTree
from .pdf_export import export_pdf


def _parse_key(s):
    try:
        return int(s)
    except ValueError:
        return s


def run_cli():
    print("=== Simulador interactivo de Árbol B ===")
    while True:
        try:
            t = int(input("Grado mínimo t (entero >= 2, ej. 2 o 3): ") or "2")
            if t >= 2:
                break
        except ValueError:
            pass
        print("Valor inválido, intenta de nuevo.")
    bt = BTree(t)
    print(
        "\nComandos disponibles:\n"
        "  insertar <clave>   -> inserta una clave y muestra la explicación\n"
        "  eliminar <clave>   -> elimina una clave y muestra la explicación\n"
        "  buscar <clave>     -> busca una clave y muestra la explicación\n"
        "  pdf <archivo.pdf>  -> exporta TODO el historial a un PDF\n"
        "  salir\n"
    )
    while True:
        try:
            cmd = input(">> ").strip().split()
        except EOFError:
            break
        if not cmd:
            continue
        op = cmd[0].lower()
        if op in ("insertar", "i") and len(cmd) > 1:
            bt.insert(_parse_key(cmd[1]))
            print("\n" + bt.history[-1]["text"] + "\n")
        elif op in ("eliminar", "e") and len(cmd) > 1:
            bt.delete(_parse_key(cmd[1]))
            print("\n" + bt.history[-1]["text"] + "\n")
        elif op in ("buscar", "b") and len(cmd) > 1:
            bt.search(_parse_key(cmd[1]))
            print("\n" + bt.history[-1]["text"] + "\n")
        elif op == "pdf":
            fname = cmd[1] if len(cmd) > 1 else "btree_historial.pdf"
            export_pdf(bt, fname)
            print(f"PDF generado: {fname} ({len(bt.history)} páginas)")
        elif op in ("salir", "q", "exit"):
            break
        else:
            print("Comando no reconocido.")


def run_demo(t=3, out="btree_historial_demo.pdf"):
    bt = BTree(t)
    inserts = [10, 20, 5, 6, 12, 30, 7, 17, 3, 8, 25, 40, 1, 15, 22, 28, 2, 18, 35, 9]
    deletes = [6, 20]
    for k in inserts:
        bt.insert(k)
    bt.search(17)
    for k in deletes:
        bt.delete(k)
    export_pdf(bt, out)
    print(
        f"Demo completada: {len(inserts)} inserciones + 1 búsqueda + "
        f"{len(deletes)} eliminaciones = {len(bt.history)} páginas -> {out}"
    )
