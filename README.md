# Contenção de propagação em redes

Trabalho prático de **GCC118 — Programação Matemática**, da Universidade Federal de Lavras (UFLA), semestre **2026/2**.

**Aluno:** Kauê de Oliveira Silva.

## Objetivo

Estudar como conter a propagação em uma rede por meio da remoção de vértices. Dado um grafo dirigido `G = (V, A)`, um conjunto de vértices inicialmente infectados ou ativados `S` e um orçamento `c`, o objetivo é remover exatamente `c` vértices fora de `S`, minimizando o número de vértices alcançáveis a partir de `S` no grafo restante.

Os vértices de `S` são protegidos contra remoção e entram na contagem dos alcançados. O orçamento deve respeitar `0 ≤ c ≤ |V| − |S|`.

A pergunta experimental é: **quando estratégias baseadas em centralidade se aproximam da solução ótima e quando a otimização encontra escolhas melhores para conter a propagação?**

## Abordagem planejada

- Implementar uma formulação exata de programação inteira/mista e testá-la com Gurobi em instâncias de tamanhos crescentes.
- Comparar o modelo exato com seleção por grau, centralidade de intermediação (*betweenness*) e seleção aleatória.
- Desenvolver uma heurística gulosa com busca local e uma metaheurística, considerando busca local iterada (ILS).
- Variar o orçamento de remoção, os conjuntos iniciais e as características das instâncias.
- Avaliar a propagação final, o tempo de execução, o gap do solver e a escalabilidade, com gráficos de qualidade versus tempo.

## Dados e interpretação

A base escolhida é a [Wiki-Vote, disponibilizada pelo SNAP](https://snap.stanford.edu/data/wiki-Vote.html). Segundo o relatório da etapa 1, a rede possui **7.115 vértices e 103.689 arcos dirigidos**; também foram estudados recortes induzidos com 100, 300 e 1.000 vértices.

Cada arco representa um voto entre usuários da Wikipédia. A propagação sobre essa topologia é uma hipótese experimental: os dados não registram contágio observado. A orientação original dos arcos será preservada nos experimentos.

## Organização do repositório

```text
.
├── README.md
├── .gitignore
└── docs/
    ├── enunciado.pdf
    ├── proposta-tema.pdf
    └── relatorios/
        └── etapa-1-wiki-vote.pdf
```

- [Enunciado do trabalho](docs/enunciado.pdf): requisitos e etapas da disciplina.
- [Proposta de tema](docs/proposta-tema.pdf): problema, artigo-base e metodologia inicial.
- [Relatório da etapa 1](docs/relatorios/etapa-1-wiki-vote.pdf): coleta, auditoria e estudo da rede Wiki-Vote.

## Estado atual e próximos passos

O repositório reúne os documentos disponíveis nesta organização inicial. Ainda não há código, arquivo da base ou resultados experimentais versionados. Os scripts `analisar.py` e `gerar_relatorio.py`, os dados e as tabelas mencionados no relatório da etapa 1 não estão presentes nesta pasta; a reprodução da análise depende de adicioná-los.

Os próximos passos são incorporar esses materiais, implementar e validar o modelo exato nos recortes menores e, depois, desenvolver e comparar as heurísticas e a metaheurística. As instruções de execução serão documentadas junto com o código.

## Etapas do trabalho

Conforme o enunciado da disciplina, as datas previstas para 2026 são:

| Etapa | Entrega | Data prevista |
| --- | --- | --- |
| 0 | Proposta e escolha do problema | 28/08 |
| 1 | Coleta e estudo dos dados | 09/10 |
| 2 | Modelagem matemática e testes com solver | 30/10 |
| 3 | Métodos heurísticos e comparação com o exato | 17/11 |
| 4 | Análise experimental e relatório consolidado | 04/12 |
| 5 | Apresentação final | 10/12 e 11/12 |

## Referência principal

AGRA, A.; SAMUCO, J. M. *Interdiction Models and Heuristics for Graph Propagation*. Networks, 2026. [DOI: 10.1002/net.70047](https://doi.org/10.1002/net.70047). Artigo-base indicado na proposta de tema.
