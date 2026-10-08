"""Algoritmos de grafos usados na análise, sem dependências externas."""

from collections import deque


def reach(adj, seeds):
    """Encontra os vértices alcançáveis a partir das origens, incluindo-as."""
    seen = set(seeds)
    queue = deque(sorted(seen))
    while queue:
        for vertex in adj[queue.popleft()]:
            if vertex not in seen:
                seen.add(vertex)
                queue.append(vertex)
    return seen


def components(adj):
    """Encontra componentes em uma adjacência sem orientação."""
    unseen = set(adj)
    result = []
    while unseen:
        component = reach(adj, [min(unseen)])
        unseen.difference_update(component)
        result.append(component)
    return sorted(result, key=lambda component: (-len(component), min(component)))


def sccs(adj, rev):
    """Encontra componentes fortes por Kosaraju iterativo.

    Recebe as adjacências dirigida e reversa. A implementação iterativa evita
    depender do limite de recursão em redes grandes.
    """
    seen = set()
    order = []
    for start in sorted(adj):
        if start in seen:
            continue
        seen.add(start)
        stack = [(start, iter(sorted(adj[start])))]
        while stack:
            vertex, neighbors = stack[-1]
            neighbor = next(neighbors, None)
            if neighbor is None:
                order.append(vertex)
                stack.pop()
            elif neighbor not in seen:
                seen.add(neighbor)
                stack.append((neighbor, iter(sorted(adj[neighbor]))))

    seen = set()
    result = []
    for start in reversed(order):
        if start in seen:
            continue
        component = {start}
        seen.add(start)
        stack = [start]
        while stack:
            for neighbor in rev[stack.pop()]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        result.append(component)
    return sorted(result, key=lambda component: (-len(component), min(component)))
