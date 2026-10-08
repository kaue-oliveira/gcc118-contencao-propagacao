"""Auditoria reprodutível da Wiki-Vote usando a biblioteca padrão Python."""

from collections import Counter, deque
import csv
import gzip
import hashlib
import json
from pathlib import Path
import platform
import random
import statistics
import time

from .grafos import components, reach, sccs

RAIZ = Path(__file__).resolve().parents[2]
FONTE = RAIZ / "dados/brutos/Wiki-Vote.txt.gz"
RESULTADOS = RAIZ / "resultados/etapa-1"
PROCESSADOS = RAIZ / "dados/processados/wiki-vote"
INSTANCIAS = RAIZ / "dados/instancias/wiki-vote"


def summary(values):
    """Resume graus com percentis interpolados e desvio populacional."""
    values = sorted(values)
    count = len(values)

    def quantile(percentile):
        position = (count - 1) * percentile
        index = int(position)
        fraction = position - index
        return (
            values[index] * (1 - fraction)
            + values[min(index + 1, count - 1)] * fraction
        )

    return {
        "min": min(values),
        "q25": quantile(0.25),
        "mediana": quantile(0.5),
        "q75": quantile(0.75),
        "q95": quantile(0.95),
        "max": max(values),
        "media": statistics.mean(values),
        "desvio_populacional": statistics.pstdev(values),
        "zeros": values.count(0),
    }


def write_csv(path, headers, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(rows)


def analisar(
    source=FONTE,
    out=RESULTADOS,
    processed=PROCESSADOS,
    instances=INSTANCIAS,
):
    """Audita a Wiki-Vote, escreve as tabelas e retorna o resumo da execução.

    Os diretórios de saída podem ser substituídos para conferir uma execução
    sem sobrescrever os resultados versionados. A rotina é específica da
    Wiki-Vote e mantém os cenários e recortes definidos na etapa 1.
    """
    started = time.perf_counter()
    for directory in (out, processed, instances):
        directory.mkdir(parents=True, exist_ok=True)

    compressed = source.read_bytes()
    raw = gzip.decompress(compressed)
    edges = []
    invalid = []
    comments = []
    blank = 0
    for lineno, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        text = line.strip()
        if not text:
            blank += 1
            continue
        if text.startswith("#"):
            comments.append(text)
            continue
        fields = text.split()
        try:
            if len(fields) != 2:
                raise ValueError("esperadas duas colunas")
            origin, destination = map(int, fields)
            if origin < 0 or destination < 0:
                raise ValueError("ID negativo")
            edges.append((origin, destination))
        except ValueError as error:
            invalid.append([lineno, str(error), text])

    unique = set(edges)
    nodes = sorted({vertex for edge in unique for vertex in edge})
    loops = sum(origin == destination for origin, destination in edges)
    clean = {(origin, destination) for origin, destination in unique if origin != destination}
    adj = {vertex: set() for vertex in nodes}
    rev = {vertex: set() for vertex in nodes}
    weak = {vertex: set() for vertex in nodes}
    for origin, destination in clean:
        adj[origin].add(destination)
        rev[destination].add(origin)
        weak[origin].add(destination)
        weak[destination].add(origin)

    wcc = components(weak)
    scc = sccs(adj, rev)
    reciprocal = sum((destination, origin) in clean for origin, destination in clean) // 2
    n = len(nodes)
    m = len(clean)

    component_records = []
    for kind, partitions in [("WCC", wcc), ("SCC", scc)]:
        for index, component in enumerate(partitions, 1):
            internal_edges = sum(
                destination in component
                for origin in component
                for destination in adj[origin]
            )
            component_records.append([kind, index, len(component), internal_edges, min(component)])
    write_csv(
        out / "componentes.csv",
        ["tipo", "indice", "vertices", "arcos_internos", "menor_id"],
        component_records,
    )
    write_csv(
        out / "graus.csv",
        ["id", "grau_entrada", "grau_saida", "grau_total"],
        [
            [vertex, len(rev[vertex]), len(adj[vertex]), len(rev[vertex]) + len(adj[vertex])]
            for vertex in nodes
        ],
    )
    write_csv(processed / "arestas_utilizadas.csv", ["origem", "destino"], sorted(clean))
    write_csv(out / "linhas_invalidas.csv", ["linha", "motivo", "conteudo"], invalid)

    # Cenários diagnósticos sem remoções; não são resultados de otimização.
    ranking = sorted(nodes, key=lambda vertex: (-len(adj[vertex]), vertex))
    initial_random = random.Random(42).sample(nodes, 5)
    scenarios = []
    for method, seeds in [
        ("maior_grau_saida", ranking[:5]),
        ("aleatorio_semente_42", initial_random),
    ]:
        for size in [1, 3, 5]:
            initial = seeds[:size]
            reached = reach(adj, initial)
            scenarios.append({
                "criterio": method,
                "S": initial,
                "k": size,
                "alcancados_sem_intervencao": len(reached),
                "percentual": 100 * len(reached) / n,
            })

    # BFS sem orientação seleciona IDs; os recortes mantêm os arcos dirigidos.
    root = ranking[0]
    seen = {root}
    queue = deque([root])
    bfs = []
    while queue:
        origin = queue.popleft()
        bfs.append(origin)
        for destination in sorted(weak[origin]):
            if destination not in seen:
                seen.add(destination)
                queue.append(destination)

    samples = []
    for size in [100, 300, 1000]:
        selected = set(bfs[:size])
        sample_edges = {
            (origin, destination)
            for origin, destination in clean
            if origin in selected and destination in selected
        }
        sample_adj = {vertex: adj[vertex] & selected for vertex in selected}
        sample_rev = {vertex: rev[vertex] & selected for vertex in selected}
        sample_weak = {vertex: weak[vertex] & selected for vertex in selected}
        samples.append({
            "vertices": len(selected),
            "arcos": len(sample_edges),
            "densidade": len(sample_edges) / (size * (size - 1)),
            "wcc": len(components(sample_weak)),
            "scc": len(sccs(sample_adj, sample_rev)),
            "S": [root],
            "alcancados_sem_intervencao": len(reach(sample_adj, [root])),
            "orcamentos_planejados": [1, 3, 5, 10],
        })
        write_csv(
            instances / f"recorte_{size}_vertices.csv", ["id"],
            [[vertex] for vertex in sorted(selected)],
        )
        write_csv(
            instances / f"recorte_{size}_arcos.csv", ["origem", "destino"],
            sorted(sample_edges),
        )

    result = {
        "fonte": "https://snap.stanford.edu/data/wiki-Vote.txt.gz",
        "obtencao": "2026-10-08",
        "arquivo": source.name,
        "bytes_gzip": len(compressed),
        "bytes_descompactados": len(raw),
        "sha256_gzip": hashlib.sha256(compressed).hexdigest(),
        "sha256_descompactado": hashlib.sha256(raw).hexdigest(),
        "sha256_script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "sha256_modulos": {
            f"src/contencao/{name}": hashlib.sha256(
                Path(__file__).with_name(name).read_bytes()
            ).hexdigest()
            for name in ("analise.py", "grafos.py")
        },
        "python": platform.python_version(),
        "cabecalho": comments,
        "linhas_em_branco": blank,
        "registros_validos": len(edges),
        "linhas_invalidas": len(invalid),
        "registros_duplicados_excedentes": len(edges) - len(unique),
        "registros_lacos": loops,
        "arcos_lacos_distintos": sum(origin == destination for origin, destination in unique),
        "vertices": n,
        "arcos_distintos_brutos": len(unique),
        "arcos_utilizados": m,
        "densidade": m / (n * (n - 1)),
        "pares_reciprocos": reciprocal,
        "arcos_reciprocos": 2 * reciprocal,
        "wcc_quantidade": len(wcc),
        "wcc_tamanhos": [len(component) for component in wcc],
        "maior_wcc_arcos": sum(
            destination in wcc[0] for origin in wcc[0] for destination in adj[origin]
        ),
        "scc_quantidade": len(scc),
        "maior_scc_vertices": len(scc[0]),
        "maior_scc_arcos": sum(
            destination in scc[0] for origin in scc[0] for destination in adj[origin]
        ),
        "scc_distribuicao_tamanhos": dict(sorted(Counter(map(len, scc)).items(), reverse=True)),
        "graus_entrada": summary([len(rev[vertex]) for vertex in nodes]),
        "graus_saida": summary([len(adj[vertex]) for vertex in nodes]),
        "top5_saida": [[vertex, len(adj[vertex])] for vertex in ranking[:5]],
        "cenarios_diagnosticos": scenarios,
        "recortes": samples,
        "tempo_auditoria_segundos": time.perf_counter() - started,
    }

    # Toda partição cobre V e cada arco contribui um grau em cada direção.
    assert sum(map(len, wcc)) == sum(map(len, scc)) == n
    assert set().union(*wcc) == set().union(*scc) == set(nodes)
    assert sum(map(len, adj.values())) == sum(map(len, rev.values())) == m
    assert result["vertices"] == 7115 and result["arcos_distintos_brutos"] == 103689

    (out / "auditoria.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result
