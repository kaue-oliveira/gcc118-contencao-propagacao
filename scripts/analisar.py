"""Executa a análise da etapa 1 a partir de qualquer diretório de trabalho."""

import json
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from contencao.analise import analisar


if __name__ == "__main__":
    print(json.dumps(analisar(), ensure_ascii=False, indent=2))
