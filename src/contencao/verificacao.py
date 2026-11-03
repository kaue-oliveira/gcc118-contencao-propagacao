"""Conferências independentes das tabelas, soluções e logs da etapa 2."""

import csv
import math
import re

from .artefatos import campos_metricas, linha_csv
from .grafos import reach
from .instancias import Instancia
from .propagacao import avaliar


def exigir(condicao, mensagem):
    if not condicao:
        raise RuntimeError(mensagem)


def conferir_csv(caminho, resultados, referencia=None):
    campos = campos_metricas(referencia or resultados)
    esperadas = []
    for r in resultados:
        esperadas.append({k: "" if v is None else str(v) for k, v in linha_csv(r, campos).items()})
    with caminho.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        exigir(reader.fieldnames == campos, f"Colunas divergentes: {caminho}.")
        exigir(list(reader) == esperadas, f"CSV diverge do JSON: {caminho}.")
    exigir(b"\r\n" not in caminho.read_bytes(), f"CSV deve usar LF para preservar hashes no Git: {caminho}.")


def conferir_resultado(cenario, r, grafo, protocolo):
    ident = r["id"]
    exigir(all(r.get(k) == v for k, v in cenario.items()), f"Metadados inconsistentes: {ident}.")
    instancia = Instancia(grafo, r["origens"], r["orcamento"])
    exigir(r["alcancados_sem_remocao"] == len(reach(grafo.adjacencia(), instancia.origens)), f"Baseline inconsistente: {ident}.")
    exigir(r["variaveis"] == 3 * r["vertices"], f"Contagem de variáveis: {ident}.")
    exigir(r["binarias"] == r["vertices"] and r["continuas"] == 2 * r["vertices"], f"Domínios: {ident}.")
    exigir(r["restricoes"] == r["vertices"] + r["arcos"] + 1, f"Contagem de restrições: {ident}.")
    exigir(r["nao_zeros"] == 4 * r["vertices"] + 3 * r["arcos"], f"Número de coeficientes: {ident}.")
    parametros = {"TimeLimit": protocolo["limite_tempo_s"], "MIPGap": protocolo["gap_alvo"],
                  "MIPGapAbs": 0.0, "Threads": protocolo["threads"], "Seed": protocolo["semente"], "NodeLimit": None}
    exigir(r["parametros"] == parametros, f"Parâmetros divergem da configuração: {ident}.")
    for campo in ("tempo_solver_s", "tempo_montagem_s", "tempo_total_s", "nos_branch_bound", "work"):
        exigir(math.isfinite(r[campo]) and r[campo] >= 0, f"Métrica inválida {campo}: {ident}.")
    exigir(r["tempo_total_s"] + 0.01 >= r["tempo_solver_s"] + r["tempo_montagem_s"], f"Tempos inconsistentes: {ident}.")
    exigir(r["status"] in {"OPTIMAL", "TIME_LIMIT"}, f"Status inesperado na grade: {ident}.")
    exigir(r["status_codigo"] == {"OPTIMAL": 2, "TIME_LIMIT": 9}[r["status"]], f"Código de status inconsistente: {ident}.")
    if not r["solucoes"]:
        exigir(all(r[k] is None for k in ("objetivo_solver", "objetivo_bfs", "gap", "gap_percentual", "removidos", "alcancados", "gap_bfs", "validacao_bfs", "objetivo_confere_bfs")), f"Ausência de incumbente incorreta: {ident}.")
        exigir(not r["otimo_comprovado"], f"Ótimo sem solução: {ident}.")
        return
    alcan = sorted(avaliar(instancia, r["removidos"]))
    exigir(alcan == r["alcancados"] and len(alcan) == r["objetivo_bfs"], f"BFS inconsistente: {ident}.")
    exigir(r["validacao_bfs"] is True, f"Solução não validada: {ident}.")
    exigir(len(instancia.origens) <= len(alcan) <= r["alcancados_sem_remocao"], f"Alcance fora dos limites: {ident}.")
    exigir(r["objetivo_solver"] >= len(alcan) - 1e-5, f"Objetivo menor que BFS: {ident}.")
    exigir(r["objetivo_confere_bfs"] == (abs(r["objetivo_solver"] - len(alcan)) < 1e-5), f"Concordância BFS incorreta: {ident}.")
    lb = r["limite_inferior"]
    if lb is not None:
        exigir(lb <= len(alcan) + 1e-5, f"Limite inferior inválido: {ident}.")
        gap = abs(r["objetivo_solver"] - lb) / abs(r["objetivo_solver"])
        exigir(math.isclose(gap, r["gap"], abs_tol=1e-8), f"Gap inconsistente: {ident}.")
        exigir(math.isclose(100 * gap, r["gap_percentual"], abs_tol=1e-6), f"Gap percentual inconsistente: {ident}.")
        exigir(math.isclose(max(0.0, (len(alcan) - lb) / len(alcan)), r["gap_bfs"], abs_tol=1e-8), f"Gap da BFS inconsistente: {ident}.")
    comprovado = r["status"] == "OPTIMAL" and lb is not None and abs(r["objetivo_solver"] - lb) < 1e-5 and r["objetivo_confere_bfs"]
    exigir(r["otimo_comprovado"] == comprovado, f"Certificação de ótimo inconsistente: {ident}.")
    if r["status"] == "OPTIMAL":
        exigir(r["objetivo_confere_bfs"], f"Ótimo diverge da BFS: {ident}.")
        if protocolo["gap_alvo"] == 0:
            exigir(comprovado and r["gap"] == 0, f"Ótimo sem fechar os limites: {ident}.")


def conferir_log(caminho, r):
    texto = caminho.read_text(encoding="utf-8")
    exigir(not re.search(r"Academic license|Restricted license|registered to", texto), f"Identificação da licença no log: {caminho}.")
    tamanho = re.search(r"Optimize a model with (\d+) rows, (\d+) columns and (\d+) nonzeros", texto)
    exigir(tamanho and tuple(map(int, tamanho.groups())) == (r["restricoes"], r["variaveis"], r["nao_zeros"]), f"Tamanho no log diverge: {caminho}.")
    variaveis = re.search(r"Variable types: (\d+) continuous, (\d+) integer \((\d+) binary\)", texto)
    exigir(variaveis and tuple(map(int, variaveis.groups())) == (r["continuas"], r["binarias"], r["binarias"]), f"Domínios no log divergem: {caminho}.")
    terminacao = "Optimal solution found" if r["status"] == "OPTIMAL" else "Time limit reached"
    exigir(terminacao in texto, f"Status no log diverge: {caminho}.")
    if r["solucoes"]:
        resumo = re.findall(r"Best objective ([\d.eE+-]+), best bound ([\d.eE+-]+), gap ([\d.eE+-]+)%", texto)
        exigir(bool(resumo), f"Resumo final ausente: {caminho}.")
        obj, lb, gap = map(float, resumo[-1])
        exigir(abs(obj - r["objetivo_solver"]) < 1e-6 and abs(lb - r["limite_inferior"]) < 1e-6, f"Objetivo/limite do log diverge: {caminho}.")
        exigir(abs(gap - r["gap_percentual"]) <= 0.00006, f"Gap no log diverge: {caminho}.")
    tempos = re.findall(r"Explored \d+ nodes .*? in ([\d.]+) seconds", texto)
    exigir(tempos and abs(float(tempos[-1]) - r["tempo_solver_s"]) < 0.02, f"Tempo no log diverge: {caminho}.")


def conferir_modelo_lp(caminho, instancia, env):
    """Reabre LP/LP.gz e compara cada coeficiente, domínio, limite e RHS."""
    import gurobipy as gp
    from .modelos.exato import construir_modelo

    esperado, _, _, _ = construir_modelo(instancia, env)
    try:
        with gp.read(str(caminho), env=env) as lido:
            def variaveis(model):
                return {v.VarName: (v.VType, v.LB, v.UB, v.Obj) for v in model.getVars()}

            exigir(lido.ModelSense == esperado.ModelSense and lido.ObjCon == esperado.ObjCon,
                   f"Objetivo do LP diverge: {caminho}.")
            exigir(variaveis(lido) == variaveis(esperado), f"Variáveis do LP divergem: {caminho}.")
            restricoes_lidas = {c.ConstrName: c for c in lido.getConstrs()}
            exigir(len(restricoes_lidas) == lido.NumConstrs == esperado.NumConstrs,
                   f"Contagem de restrições do LP diverge: {caminho}.")
            for c in esperado.getConstrs():
                outro = restricoes_lidas.get(c.ConstrName)
                exigir(outro is not None and (outro.Sense, outro.RHS) == (c.Sense, c.RHS),
                       f"Restrição do LP diverge: {c.ConstrName}.")
                def coeficientes(model, restricao):
                    row = model.getRow(restricao)
                    return {row.getVar(i).VarName: row.getCoeff(i) for i in range(row.size())}
                exigir(coeficientes(lido, outro) == coeficientes(esperado, c),
                       f"Coeficientes do LP divergem: {c.ConstrName}.")
            return {"variaveis": lido.NumVars, "restricoes": lido.NumConstrs,
                    "coeficientes": lido.NumNZs, "conteudo_confere": True}
    finally:
        esperado.dispose()
