"""Audita dados da etapa 1, métricas, logs, modelos LP e testes da etapa 2."""

import argparse
from contextlib import redirect_stdout
import csv
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from contencao.experimentos import carregar_grafos, gerar_cenarios, salvar_json, sha256
from contencao.instancias import Instancia
from contencao.verificacao import (
    conferir_csv, conferir_log, conferir_modelo_lp, conferir_resultado, exigir,
)


def conferir_etapa1(raiz, destino):
    """Reproduz os derivados em diretório temporário, sem alterar a etapa 1."""
    from contencao.analise import analisar

    original = json.loads((raiz / "resultados/etapa-1/auditoria.json").read_text(encoding="utf-8"))
    arquivos = []
    with tempfile.TemporaryDirectory(prefix="contencao-etapa1-") as pasta:
        temporario = Path(pasta)
        resumo = analisar(
            source=raiz / "dados/brutos/Wiki-Vote.txt.gz",
            out=temporario / "auditoria",
            processed=temporario / "processados",
            instances=temporario / "instancias",
        )
        resumo = json.loads(json.dumps(resumo))
        ignorar = {"python", "tempo_auditoria_segundos"}
        exigir({k: v for k, v in original.items() if k not in ignorar}
               == {k: v for k, v in resumo.items() if k not in ignorar},
               "A reprodução da etapa 1 divergiu da auditoria versionada.")
        grupos = [
            (temporario / "auditoria", raiz / "resultados/etapa-1"),
            (temporario / "processados", raiz / "dados/processados/wiki-vote"),
            (temporario / "instancias", raiz / "dados/instancias/wiki-vote"),
        ]
        for novo, antigo in grupos:
            for arquivo in sorted(novo.glob("*.csv")):
                outro = antigo / arquivo.name
                with arquivo.open(encoding="utf-8", newline="") as a, outro.open(encoding="utf-8", newline="") as b:
                    exigir(list(csv.reader(a)) == list(csv.reader(b)),
                           f"Derivado da etapa 1 diverge: {outro}.")
                arquivos.append(str(outro.relative_to(raiz)))
    evidencia = {
        "confere": True, "vertices": original["vertices"], "arcos": original["arcos_utilizados"],
        "sha256_base_bruta": sha256(raiz / "dados/brutos/Wiki-Vote.txt.gz"),
        "sha256_arquivos_conferidos": {p: sha256(raiz / p) for p in arquivos},
        "recortes": original["recortes"],
        "criterio": "Reprodução integral em pasta temporária; comparação de todas as tabelas e dos campos analíticos da auditoria.",
    }
    salvar_json(destino, evidencia)
    return evidencia


def verificar(saida, licenca=None):
    if licenca:
        os.environ["GRB_LICENSE_FILE"] = str(licenca.expanduser().resolve())
    pasta_validacao = saida / "validacao"
    pasta_validacao.mkdir(parents=True, exist_ok=True)
    arquivo_validacao = pasta_validacao / "auditoria.json"
    arquivo_validacao.unlink(missing_ok=True)
    execucao = json.loads((saida / "execucao.json").read_text(encoding="utf-8"))
    exigir("fim_utc" in execucao, "Execução incompleta.")
    for categoria in ("sha256_codigo", "sha256_dados"):
        for caminho, esperado in execucao[categoria].items():
            exigir(sha256(RAIZ / caminho) == esperado,
                   f"Arquivo mudou após o experimento: {caminho}.")
    config = execucao["configuracao"]
    exigir(config == json.loads((RAIZ / "experimentos/etapa-2.json").read_text(encoding="utf-8")),
           "Configuração atual diferente da executada.")
    grafos = carregar_grafos(RAIZ, config)
    cenarios = gerar_cenarios(config, grafos)
    exigir(cenarios == execucao["cenarios"], "Manifesto de cenários divergente.")
    resultados = execucao["resultados"]
    exigir([r["id"] for r in resultados] == [c["id"] for c in cenarios],
           "Faltam cenários ou há duplicatas.")
    arquivos_auditados = [saida / "execucao.json", saida / "metricas.csv"]
    conferir_csv(saida / "metricas.csv", resultados)
    for escopo in ("nucleo", "complementar"):
        arquivo = saida / "tabelas" / f"{escopo}.csv"
        conferir_csv(arquivo, [r for r in resultados if r["escopo"] == escopo], resultados)
        arquivos_auditados.append(arquivo)
    logs = saida / "evidencias/logs"
    exigir({p.name for p in logs.glob("*.log")} == {r["id"] + ".log" for r in resultados},
           "Há logs ausentes ou fora da grade.")
    for cenario, r in zip(cenarios, resultados):
        conferir_resultado(cenario, r, grafos[r["grafo"]], config["solver"])
        log = logs / f"{r['id']}.log"
        conferir_log(log, r)
        texto_log = log.read_text(encoding="utf-8")
        for parametro in ("TimeLimit", "MIPGap", "MIPGapAbs", "Threads", "Seed"):
            valor = re.search(rf"^{parametro}\s+([\d.eE+-]+)\s*$", texto_log, flags=re.MULTILINE)
            exigir(valor is not None and float(valor.group(1)) == r["parametros"][parametro],
                   f"Parâmetro {parametro} no log diverge: {r['id']}.")
        quantidade = re.search(r"Solution count (\d+):", texto_log)
        if r["solucoes"]:
            exigir(quantidade is not None and int(quantidade.group(1)) == r["solucoes"],
                   f"Número de soluções no log diverge: {r['id']}.")
        arquivos_auditados.append(log)
    familias = {}
    for r in resultados:
        familias.setdefault((r["grafo"], tuple(r["origens"])), []).append(r)
    pares = 0
    for familia in familias.values():
        ordenada = sorted((r for r in familia if r["otimo_comprovado"]),
                          key=lambda r: r["orcamento"])
        for a, b in zip(ordenada, ordenada[1:]):
            exigir(b["objetivo_bfs"] <= a["objetivo_bfs"],
                   f"Monotonicidade violada: {a['id']}, {b['id']}.")
            pares += 1
    nucleo = [r for r in resultados if r["escopo"] == "nucleo"]
    exigir(len(nucleo) == 12, "A grade deve preservar os 12 cenários previstos na etapa 1.")
    modelos = saida / "evidencias/modelos"
    representativos = [r for r in resultados if r["grupo"] == "escala"
                      and r["origens"] == [2565] and r["orcamento"] == 5]
    exigir({p.name for p in modelos.glob("*.lp.gz")}
           == {r["id"] + ".lp.gz" for r in representativos}, "LPs representativos ausentes ou excedentes.")
    from contencao.modelos.exato import ambiente
    conferencias_lp = {}
    with ambiente() as env:
        for r in representativos:
            arquivo = modelos / f"{r['id']}.lp.gz"
            instancia = Instancia(grafos[r["grafo"]], r["origens"], r["orcamento"])
            conferencias_lp[arquivo.name] = conferir_modelo_lp(arquivo, instancia, env)
            arquivos_auditados.append(arquivo)
    arquivo_etapa1 = pasta_validacao / "etapa-1.json"
    etapa1 = conferir_etapa1(RAIZ, arquivo_etapa1)
    arquivos_auditados.append(arquivo_etapa1)
    buffer = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(RAIZ / "tests"))
    with redirect_stdout(buffer):
        testes = unittest.TextTestRunner(stream=buffer, verbosity=2).run(suite)
    texto_testes = buffer.getvalue()
    arquivo_testes = pasta_validacao / "testes.txt"
    arquivo_testes.write_text(texto_testes, encoding="utf-8")
    exigir(testes.wasSuccessful() and not testes.skipped,
           "Testes falharam ou foram ignorados; consulte validacao/testes.txt.")
    comparacoes = re.search(r"Comparações solver x enumeração completa: (\d+)", texto_testes)
    exigir(comparacoes is not None, "Comparações por enumeração não foram executadas.")
    arquivos_auditados.append(arquivo_testes)
    evidencia = {
        "validado": True, "data_utc": datetime.now(timezone.utc).isoformat(),
        "cenarios": len(resultados), "nucleo": len(nucleo),
        "solucoes_validadas_bfs": sum(bool(r["solucoes"]) for r in resultados),
        "otimos": sum(r["otimo_comprovado"] for r in resultados),
        "nucleo_otimos": sum(r["otimo_comprovado"] for r in nucleo),
        "pares_orcamentos_monotonos": pares,
        "testes": testes.testsRun, "testes_ignorados": len(testes.skipped),
        "comparacoes_enumeracao": int(comparacoes.group(1)),
        "etapa_1_confere": etapa1["confere"], "modelos_lp": conferencias_lp,
        "sha256_configuracao": sha256(RAIZ / "experimentos/etapa-2.json"),
        "sha256_testes": sha256(RAIZ / "tests/test_etapa2.py"),
        "sha256_verificador": sha256(Path(__file__)),
        "sha256_arquivos": {str(p.relative_to(saida)): sha256(p) for p in arquivos_auditados},
    }
    salvar_json(arquivo_validacao, evidencia)
    print(texto_testes)
    print(f"Auditoria aprovada: {len(resultados)} cenários; {evidencia['otimos']} ótimos; "
          f"{len(conferencias_lp)} modelos LP; integração com etapa 1 conferida.")
    return evidencia


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, default=RAIZ / "resultados/etapa-2")
    parser.add_argument("--licenca", type=Path)
    args = parser.parse_args()
    verificar(args.saida.resolve(), args.licenca)
