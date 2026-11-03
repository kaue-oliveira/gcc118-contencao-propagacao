"""Execução sequencial e auditável dos cenários do modelo exato."""

import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import time

from .grafos import reach
from .instancias import Grafo, Instancia, ler_grafo
from .artefatos import escrever_tabelas


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def carregar_grafos(raiz, config):
    grafos = {}
    for nome, spec in config["grafos"].items():
        arquivo_v, arquivo_a = raiz / spec["vertices"], raiz / spec["arcos"]
        if spec.get("vertices_coluna_id"):
            with arquivo_v.open(encoding="utf-8", newline="") as stream:
                vertices = tuple(int(row["id"]) for row in csv.DictReader(stream))
            with arquivo_a.open(encoding="utf-8", newline="") as stream:
                arcos = tuple((int(row["origem"]), int(row["destino"])) for row in csv.DictReader(stream))
            grafos[nome] = Grafo(vertices, arcos)
        else:
            grafos[nome] = ler_grafo(arquivo_v, arquivo_a)
    return grafos


def gerar_cenarios(config, grafos):
    cenarios = []
    for grupo in config["grupos"]:
        for nome in grupo["grafos"]:
            grafo = grafos[nome]
            adj = grafo.adjacencia()
            ranking = sorted(grafo.vertices, key=lambda v: (-len(adj[v]), v))
            for perfil in grupo["perfis"]:
                criterio = perfil["criterio"]
                if criterio == "fixo":
                    origens = perfil["origens"]
                    etiqueta = "fixo_" + "_".join(map(str, origens))
                elif criterio == "maior_saida":
                    origens = ranking[:perfil["k"]]
                    etiqueta = f"saida_k{perfil['k']}"
                elif criterio == "aleatorio":
                    origens = random.Random(perfil["semente"]).sample(list(grafo.vertices), perfil["k"])
                    etiqueta = f"aleatorio_{perfil['semente']}_k{perfil['k']}"
                else:
                    raise ValueError(f"Critério desconhecido: {criterio}.")
                inicial = len(reach(adj, origens))
                for c in grupo["orcamentos"]:
                    instancia = Instancia(grafo, tuple(origens), c)
                    cenarios.append({
                        "id": f"{nome}__{etiqueta}__c{c}", "grupo": grupo["nome"],
                        "escopo": "nucleo" if grupo["nome"] == "escala"
                        and nome in {"recorte_100", "recorte_300", "recorte_1000"}
                        and c in {1, 3, 5, 10} else "complementar",
                        "grafo": nome, "vertices": len(grafo.vertices), "arcos": len(grafo.arcos),
                        "origens": list(instancia.origens), "k": len(origens), "orcamento": c,
                        "criterio_origens": criterio, "semente_origens": perfil.get("semente"),
                        "alcancados_sem_remocao": inicial,
                    })
    ids = [c["id"] for c in cenarios]
    if len(set(ids)) != len(ids):
        raise ValueError("Cenários duplicados na configuração.")
    return cenarios


def salvar_json(path, data):
    path = Path(path)
    temporario = path.with_suffix(path.suffix + ".tmp")
    temporario.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporario.replace(path)


def salvar_resultados(saida, manifesto, resultados):
    salvar_json(saida / "execucao.json", {**manifesto, "resultados": resultados})
    escrever_tabelas(saida, resultados)


def executar(raiz, arquivo_config, saida, *, retomar=False, filtro=None):
    from .modelos.exato import ambiente, resolver
    import gurobipy as gp

    config = json.loads(arquivo_config.read_text(encoding="utf-8"))
    grafos = carregar_grafos(raiz, config)
    cenarios = gerar_cenarios(config, grafos)
    if filtro:
        cenarios = [c for c in cenarios if filtro in c["id"]]
    if not cenarios:
        raise ValueError("Nenhum cenário selecionado.")
    saida.mkdir(parents=True, exist_ok=True)
    arquivos = sorted({spec[chave] for spec in config["grafos"].values() for chave in ("vertices", "arcos")})
    modulos = sorted((raiz / "src/contencao").rglob("*.py")) + [raiz / "scripts/experimentar.py"]
    assinatura = {
        "configuracao": config, "cenarios": cenarios,
        "sha256_dados": {p: sha256(raiz / p) for p in arquivos},
        "sha256_codigo": {str(p.relative_to(raiz)): sha256(p) for p in modulos},
        "python": platform.python_version(), "gurobi": ".".join(map(str, gp.gurobi.version())),
    }
    manifesto = {
        **assinatura,
        "inicio_utc": datetime.now(timezone.utc).isoformat(),
        "plataforma": platform.platform(), "arquitetura": platform.machine(),
        "processadores_logicos": os.cpu_count(),
        "afinidade_cpus": len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None,
        "processador": next((linha.split(":", 1)[1].strip() for linha in
                              Path("/proc/cpuinfo").read_text().splitlines()
                              if linha.startswith("model name")), platform.processor())
                       if Path("/proc/cpuinfo").exists() else platform.processor(),
        "observacao_tempos": "Uma execução por cenário; tempos não são médias. Execução sequencial, Threads=1. Tempo total inclui montagem e optimize, não licença nem avaliação BFS.",
    }
    resultados = []
    existente = saida / "execucao.json"
    if existente.exists():
        if not retomar:
            raise ValueError(f"Já existe {existente}; use --retomar ou outra pasta --saida.")
        anterior = json.loads(existente.read_text(encoding="utf-8"))
        if any(anterior.get(k) != v for k, v in assinatura.items()):
            raise ValueError("Configuração, código, dados ou versões mudaram: use uma nova pasta de saída.")
        manifesto = {k: v for k, v in anterior.items() if k != "resultados"}
        resultados = anterior["resultados"]
    concluidos = {r["id"] for r in resultados}
    if concluidos == {c["id"] for c in cenarios} and "fim_utc" in manifesto:
        print("Execução já concluída; nenhum resultado foi alterado.", flush=True)
        return resultados
    manifesto.pop("fim_utc", None)
    if retomar and (manifesto["plataforma"] != platform.platform()
                    or manifesto["processadores_logicos"] != os.cpu_count()):
        raise ValueError("Ambiente diferente do lote original: use uma nova pasta de saída.")
    inicio = time.perf_counter()
    with ambiente() as env:
        for indice, cenario in enumerate(cenarios, 1):
            if cenario["id"] in concluidos:
                continue
            instancia = Instancia(grafos[cenario["grafo"]], tuple(cenario["origens"]), cenario["orcamento"])
            ident = cenario["id"]
            print(f"[{indice}/{len(cenarios)}] {ident}", flush=True)
            lp = saida / "evidencias/modelos" / f"{ident}.lp.gz" if cenario["criterio_origens"] == "fixo" and cenario["origens"] == [2565] and cenario["orcamento"] == 5 else None
            result = resolver(
                instancia, env, limite_tempo=config["solver"]["limite_tempo_s"],
                gap_alvo=config["solver"]["gap_alvo"], threads=config["solver"]["threads"],
                semente=config["solver"]["semente"], log=saida / "evidencias/logs" / f"{ident}.log", lp=lp,
            )
            if result["variaveis"] != 3 * cenario["vertices"] or result["restricoes"] != cenario["arcos"] + cenario["vertices"] + 1:
                raise RuntimeError("Contagens do modelo não conferem com a formulação.")
            result = {**cenario, **result}
            resultados.append(result)
            salvar_resultados(saida, manifesto, resultados)
            print(f"  {result['status']}: BFS={result['objetivo_bfs']}, LB={result['limite_inferior']}, gap={result['gap_percentual']}%, t={result['tempo_solver_s']:.3f}s", flush=True)
    manifesto["fim_utc"] = datetime.now(timezone.utc).isoformat()
    manifesto["tempo_lotes_s"] = manifesto.get("tempo_lotes_s", 0.0) + time.perf_counter() - inicio
    salvar_resultados(saida, manifesto, resultados)
    return resultados
