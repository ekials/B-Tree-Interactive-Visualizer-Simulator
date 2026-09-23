import argparse
from btree_app.cli import run_cli, run_demo

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Ejecuta una demo automática y genera un PDF de ejemplo",
    )
    parser.add_argument("--out", default="btree_historial_demo.pdf")
    parser.add_argument("--t", type=int, default=3, help="Grado mínimo t para --demo")
    args = parser.parse_args()
    if args.demo:
        run_demo(t=args.t, out=args.out)
    else:
        run_cli()
