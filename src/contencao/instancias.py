"""Instâncias imutáveis; preserva isolados e rejeita dados inconsistentes."""

from dataclasses import dataclass
import csv
from pathlib import Path


@dataclass(frozen=True)
class Grafo:
    vertices: tuple[int, ...]
    arcos: tuple[tuple[int, int], ...]

    def __post_init__(self):
        vertices = tuple(self.vertices)
        arcos = tuple(tuple(arco) for arco in self.arcos)
        if not vertices or any(type(v) is not int or v < 0 for v in vertices):
            raise ValueError("O grafo deve conter IDs inteiros não negativos.")
        if len(set(vertices)) != len(vertices):
            raise ValueError("Vértices duplicados.")
        conjunto = set(vertices)
        for arco in arcos:
            if len(arco) != 2 or any(type(v) is not int or v not in conjunto for v in arco):
                raise ValueError(f"Arco com extremidade inválida: {arco}.")
            if arco[0] == arco[1]:
                raise ValueError("Laços não pertencem às instâncias deste trabalho.")
        if len(set(arcos)) != len(arcos):
            raise ValueError("Arcos duplicados.")
        object.__setattr__(self, "vertices", tuple(sorted(vertices)))
        object.__setattr__(self, "arcos", tuple(sorted(arcos)))

    def adjacencia(self):
        adj = {v: set() for v in self.vertices}
        for i, j in self.arcos:
            adj[i].add(j)
        return adj


@dataclass(frozen=True)
class Instancia:
    grafo: Grafo
    origens: tuple[int, ...]
    orcamento: int

    def __post_init__(self):
        origens = tuple(self.origens)
        if not origens or len(set(origens)) != len(origens):
            raise ValueError("S deve ser não vazio e não conter duplicatas.")
        if any(type(v) is not int or v not in self.grafo.vertices for v in origens):
            raise ValueError("As origens devem pertencer ao grafo.")
        if type(self.orcamento) is not int or not 0 <= self.orcamento <= len(self.grafo.vertices) - len(origens):
            raise ValueError("Exige-se 0 <= c <= |V| - |S| inteiro.")
        object.__setattr__(self, "origens", tuple(sorted(origens)))


def _ler_csv(caminho, cabecalho):
    with Path(caminho).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != cabecalho:
            raise ValueError(f"Cabeçalho inválido em {caminho}: esperado {cabecalho}.")
        for linha, row in enumerate(reader, 2):
            try:
                if None in row or any(row[chave] is None for chave in cabecalho):
                    raise ValueError("Número incorreto de colunas")
                yield tuple(int(row[chave]) for chave in cabecalho)
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Registro inválido em {caminho}, linha {linha}.") from exc


def ler_grafo(arquivo_vertices, arquivo_arcos):
    """Sempre lê V separadamente, inclusive os vértices ausentes em A."""
    vertices = tuple(row[0] for row in _ler_csv(arquivo_vertices, ["id"]))
    arcos = tuple(_ler_csv(arquivo_arcos, ["origem", "destino"]))
    return Grafo(vertices, arcos)
