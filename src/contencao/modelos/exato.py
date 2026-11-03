"""Formulação compacta IF da proposta: 3n variáveis e m+n+1 linhas.

v binária; y e z contínuas em [0,1]. As origens têm v=z=0 por
limites. Não se impõem binariedades desnecessárias a y e z.
"""

from contextlib import contextmanager
import math
from pathlib import Path
import time

import gurobipy as gp
from gurobipy import GRB

from ..artefatos import sanitizar_log
from ..instancias import Instancia
from ..propagacao import avaliar


@contextmanager
def ambiente():
    """Não imprime credenciais nem o cabeçalho de autenticação da licença."""
    with gp.Env(empty=True) as env:
        env.setParam("OutputFlag", 0)
        env.start()
        yield env


def construir_modelo(instancia: Instancia, env):
    grafo = instancia.grafo
    model = gp.Model("contencao_IF", env=env)
    v = model.addVars(grafo.vertices, vtype=GRB.BINARY, name="v")
    y = model.addVars(grafo.vertices, lb=0, ub=1, name="y")
    z = model.addVars(grafo.vertices, lb=0, ub=1, name="z")
    for origem in instancia.origens:
        v[origem].UB = z[origem].UB = 0
    model.setObjective(gp.quicksum(y.values()), GRB.MINIMIZE)
    model.addConstr(gp.quicksum(v.values()) == instancia.orcamento, "orcamento")
    model.addConstrs((z[i] + y[i] + v[i] >= 1 for i in grafo.vertices), name="cobertura")
    model.addConstrs((z[i] - z[j] + v[i] >= 0 for i, j in grafo.arcos), name="propagacao")
    model.update()
    return model, v, y, z


def _finito(valor):
    return float(valor) if math.isfinite(valor) and abs(valor) < GRB.INFINITY else None


def resolver(instancia, env, *, limite_tempo=30.0, gap_alvo=0.0,
             threads=1, semente=42, limite_nos=None, log=None, lp=None):
    """Retorna métricas originais e avaliação BFS, inclusive em TIME_LIMIT.

    Ausência de incumbente é representada por None, nunca objetivo/gap zero.
    O gap do solver se refere a ObjVal; gap_bfs usa o objetivo reavaliado.
    """
    if not math.isfinite(limite_tempo) or limite_tempo < 0:
        raise ValueError("Limite de tempo deve ser finito e não negativo.")
    if not math.isfinite(gap_alvo) or not 0 <= gap_alvo <= 1:
        raise ValueError("Gap alvo deve estar entre 0 e 1.")
    if type(threads) is not int or threads < 1:
        raise ValueError("threads deve ser inteiro positivo.")
    if type(semente) is not int or not 0 <= semente <= 2_000_000_000:
        raise ValueError("Semente inválida.")
    if limite_nos is not None and (type(limite_nos) is not int or limite_nos < 0):
        raise ValueError("Limite de nós deve ser inteiro não negativo.")
    inicio = time.perf_counter()
    model, v, _, _ = construir_modelo(instancia, env)
    try:
        model.Params.Threads = threads
        model.Params.Seed = semente
        model.Params.TimeLimit = limite_tempo
        model.Params.MIPGap = gap_alvo
        # Evita encerrar pelo gap absoluto padrão quando o alvo é zero.
        model.Params.MIPGapAbs = 0.0
        if limite_nos is not None:
            model.Params.NodeLimit = limite_nos
        if log:
            Path(log).parent.mkdir(parents=True, exist_ok=True)
            model.Params.LogToConsole = 0
            model.Params.OutputFlag = 1
            model.Params.LogFile = str(log)
        if lp:
            Path(lp).parent.mkdir(parents=True, exist_ok=True)
            model.write(str(lp))
        montagem = time.perf_counter() - inicio
        model.optimize()
        status = next((nome for nome in (
            "OPTIMAL", "INFEASIBLE", "INF_OR_UNBD", "UNBOUNDED", "CUTOFF",
            "ITERATION_LIMIT", "NODE_LIMIT", "TIME_LIMIT", "SOLUTION_LIMIT",
            "INTERRUPTED", "NUMERIC", "SUBOPTIMAL", "USER_OBJ_LIMIT",
            "WORK_LIMIT", "MEM_LIMIT",
        ) if getattr(GRB, nome, None) == model.Status), str(model.Status))
        result = {
            "status": status, "status_codigo": model.Status,
            "otimo_comprovado": False,
            "variaveis": model.NumVars, "binarias": model.NumBinVars,
            "continuas": model.NumVars - model.NumIntVars,
            "restricoes": model.NumConstrs, "nao_zeros": model.NumNZs,
            "tempo_montagem_s": montagem, "tempo_solver_s": model.Runtime,
            "tempo_total_s": time.perf_counter() - inicio,
            "nos_branch_bound": model.NodeCount, "work": model.Work,
            "solucoes": model.SolCount,
            "objetivo_solver": None, "limite_inferior": _finito(model.ObjBound),
            "gap": None, "gap_percentual": None,
            "removidos": None, "alcancados": None, "objetivo_bfs": None,
            "gap_bfs": None, "validacao_bfs": None,
            "objetivo_confere_bfs": None,
            "parametros": {"TimeLimit": limite_tempo, "MIPGap": gap_alvo,
                           "MIPGapAbs": 0.0, "Threads": threads, "Seed": semente,
                           "NodeLimit": limite_nos},
        }
        if model.SolCount:
            removidos = sorted(i for i in instancia.grafo.vertices if v[i].X > 0.5)
            alcancados = sorted(avaliar(instancia, removidos))
            objetivo = model.ObjVal
            bfs = len(alcancados)
            confere = abs(objetivo - bfs) < 1e-5
            if objetivo < bfs - 1e-5 or (status == "OPTIMAL" and not confere):
                raise RuntimeError(f"Objetivo do modelo {objetivo} diverge da BFS {bfs}.")
            limite = result["limite_inferior"]
            if limite is not None and limite > bfs + 1e-5:
                raise RuntimeError("Limite inferior maior que a solução viável BFS.")
            gap = _finito(model.MIPGap)
            result.update({
                "objetivo_solver": objetivo, "gap": gap,
                "gap_percentual": None if gap is None else 100 * gap,
                "removidos": removidos, "alcancados": alcancados,
                "objetivo_bfs": bfs, "validacao_bfs": True,
                "objetivo_confere_bfs": confere,
                "gap_bfs": None if limite is None else max(0.0, (bfs - limite) / bfs),
                "otimo_comprovado": status == "OPTIMAL" and limite is not None
                and abs(objetivo - limite) < 1e-5 and confere,
            })
        if status in {"INFEASIBLE", "INF_OR_UNBD", "UNBOUNDED", "NUMERIC"}:
            raise RuntimeError(f"Status inesperado em instância válida: {status}.")
        return result
    finally:
        model.dispose()
        if log:
            sanitizar_log(log)
