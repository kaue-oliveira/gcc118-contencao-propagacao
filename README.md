# Contenção de propagação em redes

Trabalho prático de **GCC118 — Programação Matemática**, da Universidade Federal de Lavras (UFLA), semestre **2026/2**. Aluno: **Kauê de Oliveira Silva**.

## Objetivo

Dado um grafo dirigido `G = (V, A)`, um conjunto de vértices inicialmente infectados ou ativados `S` e um orçamento `c`, escolher exatamente `c` vértices fora de `S` para remover, minimizando o número de vértices alcançáveis a partir de `S` no grafo restante.

Os vértices de `S` são protegidos contra remoção e entram na contagem dos alcançados. O orçamento deve respeitar `0 ≤ c ≤ |V| − |S|`.

A pergunta experimental é: **quando estratégias baseadas em centralidade se aproximam da solução ótima e quando a otimização encontra escolhas melhores para conter a propagação?**

## O que já está disponível

A etapa 1 contém a base original Wiki-Vote, a rotina de análise e os resultados necessários para reproduzir a caracterização da rede:

- Auditoria dos registros, duplicatas, laços e pares recíprocos.
- Graus de entrada e saída, componentes fracas e componentes fortes.
- Seis cenários de alcançabilidade sem remoção, com origens por maior grau de saída e seleção aleatória de semente 42.
- Recortes induzidos e crescentes de 100, 300 e 1.000 vértices.
- Relatório em PDF e figura de distribuição dos graus já produzidos.

**O modelo exato, as heurísticas de contenção e a metaheurística ainda não estão implementados.** A análise atual mede alcançabilidade sem intervenção (`c = 0`).

## Estrutura atual

```text
.
├── README.md
├── .gitignore
├── .gitattributes
├── src/
│   └── contencao/
│       ├── __init__.py
│       ├── grafos.py                   # Alcançabilidade e componentes
│       └── analise.py                  # Auditoria, cenários e recortes da etapa 1
├── scripts/
│   └── analisar.py                     # Entrada para executar a análise
├── dados/
│   ├── brutos/
│   │   └── Wiki-Vote.txt.gz             # Arquivo original do SNAP
│   ├── processados/
│   │   └── wiki-vote/
│   │       └── arestas_utilizadas.csv   # Arcos dirigidos após a auditoria
│   └── instancias/
│       └── wiki-vote/
│           ├── recorte_100_vertices.csv
│           ├── recorte_100_arcos.csv
│           ├── recorte_300_vertices.csv
│           ├── recorte_300_arcos.csv
│           ├── recorte_1000_vertices.csv
│           └── recorte_1000_arcos.csv
├── resultados/
│   └── etapa-1/
│       ├── auditoria.json
│       ├── graus.csv
│       ├── componentes.csv
│       └── linhas_invalidas.csv
└── docs/
    ├── enunciado.pdf
    ├── proposta-tema.pdf
    ├── figuras/
    │   └── distribuicao_graus.png
    └── relatorios/
        └── etapa-1-wiki-vote.pdf
```

O código reutilizável fica em `src/contencao/`; `scripts/` contém apenas entradas de execução. Os dados brutos ficam separados dos arquivos derivados e das instâncias destinadas aos próximos experimentos. Resultados são agrupados por etapa, e documentos e figuras finais ficam em `docs/`.

## Executar a etapa 1

Requer **Python 3.10 ou superior**. A análise usa somente a biblioteca padrão; não é necessário instalar pacotes ou solver.

Na raiz do repositório:

```bash
python3 scripts/analisar.py
```

No Windows, use `py -3 scripts/analisar.py` se `python3` não estiver disponível. Os caminhos são resolvidos a partir do código, permitindo executar o script por caminho absoluto a partir de outro diretório.

A execução imprime o resumo JSON e **sobrescreve** as tabelas em `resultados/etapa-1/`, a lista de arcos em `dados/processados/wiki-vote/` e os recortes em `dados/instancias/wiki-vote/`. Ela preserva a base comprimida, os PDFs e a figura existente.

Resultados esperados: **7.115 vértices, 103.689 arcos, 24 componentes fracas e 5.816 componentes fortes**, sem registros inválidos, duplicatas ou laços. Todos os CSVs usam cabeçalho; `linhas_invalidas.csv` contém somente o cabeçalho nessa base.

O JSON registra os checksums dos dados e dos módulos da análise, a versão do Python, as origens selecionadas e o tempo de execução. Ao reproduzir a análise, os metadados de código, ambiente e tempo podem mudar; confira os IDs das origens aleatórias ao comparar versões de Python.

## Dados e convenções das instâncias

A [Wiki-Vote do SNAP](https://snap.stanford.edu/data/wiki-Vote.html) registra votos entre usuários da Wikipédia. A propagação sobre essa topologia é uma hipótese experimental: os dados não registram contágio observado. Mantêm-se os IDs originais e a orientação dos arcos.

O arquivo [Wiki-Vote.txt.gz](https://snap.stanford.edu/data/wiki-Vote.txt.gz), obtido em 08/10/2026, está incluído no repositório. SHA-256 do arquivo comprimido:

```text
7d3e53626e14b8b09fb3b396bece9d481ad606bd64ceab066349ff57d4ada7fc
```

Cada recorte é descrito por um CSV de vértices (coluna `id`) e um CSV de arcos (colunas `origem` e `destino`). O arquivo de vértices deve ser lido mesmo quando um vértice não aparece nos arcos, para preservar vértices isolados do recorte.

A seleção dos IDs usa BFS sem orientação a partir do vértice 2565, visitando vizinhos em ordem crescente. O grafo induzido mantém os sentidos originais. Para os testes planejados, `S = {2565}` e `c ∈ {1, 3, 5, 10}`; essas informações também estão em `resultados/etapa-1/auditoria.json`. Os recortes não são amostras representativas da rede inteira.

## Expansão nas próximas etapas

Os caminhos abaixo são **planejados** e devem ser criados conforme a implementação avançar:

| Caminho | Responsabilidade |
| --- | --- |
| `src/contencao/instancias.py` | Leitura e validação dos grafos, origens `S` e orçamento `c`. |
| `src/contencao/propagacao.py` | Avaliação da alcançabilidade após remoções, reutilizando os algoritmos de `grafos.py`. |
| `src/contencao/modelos/` | Formulação exata de programação inteira/mista e integração com Gurobi. |
| `src/contencao/heuristicas/` | Seleção por grau, betweenness, aleatória, gulosa e busca local. |
| `src/contencao/metaheuristicas/` | Busca local iterada (ILS), prevista na metodologia. |
| `scripts/experimentar.py` | Execução das comparações entre métodos nas mesmas instâncias. |
| `experimentos/` | Configurações dos experimentos: instância, origens, orçamento, método, semente e limites de execução. |
| `resultados/etapa-2/`, `resultados/etapa-3/`, `resultados/etapa-4/` | Saídas da modelagem, heurísticas e análise experimental, respectivamente. |
| `tests/` | Validação dos algoritmos, das restrições de remoção e da concordância entre avaliação e modelo exato em grafos pequenos. |

A sequência prevista é validar as instâncias e a avaliação de remoções, implementar o modelo exato nos recortes menores e desenvolver as heurísticas e a ILS. A comparação deve registrar vértices removidos, propagação final, tempo de execução, status e gap do solver quando aplicável. As configurações e sementes devem acompanhar os resultados para permitir reprodução.

Novas bases devem ficar em `dados/brutos/`, com seus derivados e instâncias em subpastas próprias. A rotina `analise.py` atual é específica da Wiki-Vote; ela não deve ser tratada como analisador genérico de outras redes. Dependências adicionais e instruções de instalação serão registradas quando os métodos que precisarem delas forem implementados.

## Documentos e cronograma

- [Enunciado](docs/enunciado.pdf): requisitos e etapas da disciplina.
- [Proposta de tema](docs/proposta-tema.pdf): problema, artigo-base e metodologia inicial.
- [Relatório da etapa 1](docs/relatorios/etapa-1-wiki-vote.pdf): coleta, auditoria e estudo da Wiki-Vote.
- [Figura de distribuição dos graus](docs/figuras/distribuicao_graus.png): figura pronta da etapa 1.

Datas previstas no enunciado, para 2026:

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
