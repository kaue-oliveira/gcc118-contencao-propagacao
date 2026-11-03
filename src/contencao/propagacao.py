"""Avaliação independente do solver por busca no grafo remanescente."""

from .grafos import reach
from .instancias import Instancia


def avaliar(instancia: Instancia, removidos):
    lista = tuple(removidos)
    if any(type(v) is not int for v in lista):
        raise ValueError("Os IDs removidos devem ser inteiros.")
    conjunto = set(lista)
    if len(lista) != len(conjunto) or len(conjunto) != instancia.orcamento:
        raise ValueError("A solução deve remover exatamente c vértices distintos.")
    if not conjunto <= set(instancia.grafo.vertices):
        raise ValueError("Remoção de vértice inexistente.")
    if conjunto & set(instancia.origens):
        raise ValueError("Não se pode remover uma origem.")
    adj = {v: set() for v in instancia.grafo.vertices if v not in conjunto}
    for i, j in instancia.grafo.arcos:
        if i not in conjunto and j not in conjunto:
            adj[i].add(j)
    return reach(adj, instancia.origens)
