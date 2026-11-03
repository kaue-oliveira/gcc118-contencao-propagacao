"""Executa e registra os cenários de programação inteira da etapa 2."""

import argparse
import os
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=RAIZ / "experimentos/etapa-2.json")
    parser.add_argument("--saida", type=Path, default=RAIZ / "resultados/etapa-2")
    parser.add_argument("--licenca", type=Path, help="Caminho para gurobi.lic existente; não é copiado nem versionado.")
    parser.add_argument("--retomar", action="store_true", help="Continua uma execução com código/dados/configuração idênticos.")
    parser.add_argument("--filtro", help="Seleciona IDs que contêm este texto; use saída separada para pilotos.")
    args = parser.parse_args()
    if args.licenca:
        os.environ["GRB_LICENSE_FILE"] = str(args.licenca.expanduser().resolve())
    try:
        from contencao.experimentos import executar
        executar(RAIZ, args.config.resolve(), args.saida.resolve(), retomar=args.retomar, filtro=args.filtro)
    except (ImportError, ValueError, RuntimeError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        # Mantém visível a causa (por exemplo, licença ou rede) sem inventar resultados.
        print(f"Falha do solver/ambiente ({type(exc).__name__}): {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
