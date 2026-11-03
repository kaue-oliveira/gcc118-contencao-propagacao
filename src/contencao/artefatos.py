"""Arquivos derivados e organização das evidências dos experimentos."""

import csv
import json
from pathlib import Path
import re


def campos_metricas(resultados):
    return [k for k in resultados[0] if k not in {"alcancados", "parametros"}]


def linha_csv(resultado, campos):
    return {
        k: json.dumps(resultado[k], ensure_ascii=False)
        if isinstance(resultado[k], (list, dict)) else resultado[k]
        for k in campos
    }


def escrever_csv(caminho, resultados, campos):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(caminho.suffix + ".tmp")
    with temporario.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=campos, lineterminator="\n")
        writer.writeheader()
        writer.writerows(linha_csv(r, campos) for r in resultados)
    temporario.replace(caminho)


def escrever_tabelas(saida, resultados):
    if not resultados:
        return
    campos = campos_metricas(resultados)
    escrever_csv(saida / "metricas.csv", resultados, campos)
    for escopo in ("nucleo", "complementar"):
        selecionados = [r for r in resultados if r["escopo"] == escopo]
        escrever_csv(saida / "tabelas" / f"{escopo}.csv", selecionados, campos)


def sanitizar_log(caminho):
    """Remove somente identificação da licença e o caminho local do log."""
    caminho = Path(caminho)
    if not caminho.exists():
        return
    texto = caminho.read_text(encoding="utf-8")
    texto = re.sub(
        r"^.*(?:Academic license|Restricted license|registered to).*$",
        "[Identificação da licença omitida.]", texto, flags=re.MULTILINE,
    )
    texto = re.sub(
        r'^Set parameter LogFile to value .*$',
        f'Set parameter LogFile to value "{caminho.name}"', texto, flags=re.MULTILINE,
    )
    caminho.write_text(texto, encoding="utf-8")
