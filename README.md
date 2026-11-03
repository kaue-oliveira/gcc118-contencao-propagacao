# Contenção de propagação em redes

Trabalho de **GCC118 - Programação Matemática**, UFLA, semestre **2026/2**. Aluno: **Kauê de Oliveira Silva**.

Dado um grafo dirigido G=(V,A), um conjunto inicial não vazio S e um orçamento inteiro c, escolher **exatamente c vértices fora de S** para remover e minimizar o número de vértices alcançáveis a partir de S. As origens são protegidas e entram na contagem; exige-se 0 ≤ c ≤ |V|-|S|.

A pergunta do trabalho é: **quando estratégias baseadas em centralidade se aproximam do ótimo e quando a otimização encontra remoções melhores para conter a propagação?**

## Entregas

| Etapa | Conteúdo e acesso |
| --- | --- |
| 1 - Dados | [Relatório](docs/relatorios/etapa-1-wiki-vote.pdf), [análise editável](docs/relatorios/etapa-1-wiki-vote.md) e [revisão](docs/relatorios/revisao-etapa-1.md). |
| 2 - Modelo exato | [Relatório](docs/relatorios/etapa-2-modelo-exato.pdf), [versão Markdown](docs/relatorios/etapa-2-modelo-exato.md), [desenho experimental](docs/relatorios/desenho-experimental-etapa-2.md) e [vistoria](docs/relatorios/revisao-etapa-2.md). |
| Resultados da etapa 2 | [Índice dos arquivos](resultados/etapa-2/README.md), [12 casos do núcleo](resultados/etapa-2/tabelas/nucleo.csv), [complementos](resultados/etapa-2/tabelas/complementar.csv) e [auditoria](resultados/etapa-2/validacao/auditoria.json). |

O modelo exato está implementado e validado. As heurísticas, a busca local e a metaheurística serão desenvolvidas na etapa 3.

## Organização

~~~text
dados/
  brutos/                    Base original preservada
  processados/wiki-vote/     Arcos auditados da rede completa
  instancias/wiki-vote/      CSVs de vértices e arcos dos recortes
src/contencao/               Grafos, instâncias, propagação, modelo e auditoria
scripts/                    Entradas para executar, conferir e relatar
experimentos/etapa-2.json    Cenários e parâmetros do solver
requirements/               Dependências do solver
tests/                      Testes e oráculo por enumeração
resultados/
  etapa-1/                  Auditoria e tabelas da coleta
  etapa-2/                  Entrega atual: métricas, soluções e evidências
  arquivo/etapa-2/           Lotes anteriores compactados, fora da análise principal
  locais/                   Reexecuções particulares, ignoradas pelo Git
docs/
  enunciado.pdf
  proposta-tema.pdf
  figuras/
  relatorios/
~~~

O [índice de resultados](resultados/etapa-2/README.md) explica a função de cada arquivo e os campos necessários às próximas etapas. Os arquivos históricos não se misturam com a entrega atual.

## Reproduzir a etapa 1

Requer Python 3.10 ou superior e usa somente a biblioteca padrão:

~~~bash
python3 scripts/analisar.py
~~~

O comando sobrescreve os derivados da etapa 1 e os recortes, preservando a base bruta. São esperados 7.115 vértices, 103.689 arcos, 24 componentes fracas e 5.816 fortes.

A vistoria da etapa 2 também reproduz os dados da etapa 1 em diretório temporário, sem sobrescrever os arquivos versionados.

## Reproduzir a etapa 2

O solver requer Python 3.10 ou superior e **licença válida do Gurobi**. A execução entregue utiliza Python 3.12.3 e Gurobi 12.0.3.

Na raiz do projeto:

~~~bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements/solver.txt
.venv/bin/python scripts/experimentar.py --saida resultados/locais/reexecucao
.venv/bin/python scripts/verificar_etapa2.py --saida resultados/locais/reexecucao
~~~

Configure a licença pelo mecanismo normal do Gurobi ou acrescente o argumento --licenca /caminho/para/gurobi.lic aos comandos experimentar.py e verificar_etapa2.py. A licença acadêmica existente foi usada na entrega; nenhuma credencial integra o repositório. Licenças com autenticação externa precisam acessar o serviço de licenças. A licença gratuita de tamanho limitado não cobre a grade completa.

No Windows, substitua .venv/bin/python por .venv\Scripts\python.exe. Os caminhos padrão são resolvidos a partir do projeto. Sem --saida, os comandos usam resultados/etapa-2/.

O executor recusa sobrescrever uma execução existente. --retomar continua um lote com configuração, código, dados e versões idênticos; se já estiver concluído, preserva os arquivos. --filtro seleciona IDs de cenários para pilotos em outra pasta. A auditoria de entrega exige a grade completa.

## Modelo e experimentos

A formulação compacta tem **3n variáveis** (n binárias e 2n contínuas) e **m+n+1 restrições** antes do presolve. As fixações das origens são limites de variáveis. A formulação e a justificativa de exatidão estão no relatório.

O núcleo preserva os **12 casos planejados na etapa 1**: recortes de 100, 300 e 1.000 vértices, S={2565} e c=1/3/5/10. Os 70 complementos cruzam origens e orçamentos no mesmo grafo, verificam a rede completa e incluem controles. A seleção é justificada no desenho experimental; o total não é um tamanho de amostra estatístico.

O protocolo usa TimeLimit=30 s, MIPGap=MIPGapAbs=0, uma thread e semente do solver 42. Cada cenário tem uma execução; os tempos não são médias. TIME_LIMIT preserva solução, limite inferior e gap, sem afirmar otimalidade.

O verificador compara as tabelas com o JSON, confronta métricas com os logs, reavalia remoções por BFS, reabre os quatro LPs compactados e compara seus coeficientes e limites com o modelo. Também reproduz a etapa 1 e executa a suíte de testes, incluindo 1.196 comparações com enumeração completa.

## Dados e convenções

A [Wiki-Vote do SNAP](https://snap.stanford.edu/data/wiki-Vote.html) registra votos entre usuários da Wikipédia. Mantêm-se IDs e sentidos originais; a propagação é uma hipótese sobre a topologia, não um contágio observado.

A base comprimida fica em dados/brutos/Wiki-Vote.txt.gz. Sua origem, checksums e auditoria estão em resultados/etapa-1/auditoria.json. Os recortes são induzidos sobre IDs selecionados por BFS sem orientação, a partir de 2565, visitando vizinhos em ordem crescente. Não são amostras representativas da rede inteira.

Cada recorte tem um CSV de vértices, coluna id, e outro de arcos, colunas origem e destino. Ambos são necessários para preservar isolados. A rede completa usa os IDs da tabela de graus e os arcos auditados. A configuração de cada execução registra os IDs efetivos de S e os hashes dos dados.

## Próximas etapas

Na etapa 3, as heurísticas devem usar os mesmos grafos, origens e orçamentos registrados no manifesto, além do avaliador de propagação existente. O campo otimo_comprovado distingue referências ótimas de soluções interrompidas; nestas, devem-se manter os limites inferior e superior ao comparar qualidade.

A etapa 4 acrescentará repetições de desempenho, comparação consolidada e discussão de incertezas. O gráfico heurística versus exato e a análise de métodos não são antecipados pela etapa 2.

O [enunciado](docs/enunciado.pdf) e a [proposta](docs/proposta-tema.pdf) registram os requisitos. Datas previstas: etapa 2 em 30/10; etapa 3 em 17/11; entrega final em 04/12; apresentação em 10/12 e 11/12, no semestre 2026/2.

## Referência principal

AGRA, A.; SAMUCO, J. M. Interdiction Models and Heuristics for Graph Propagation. Networks, 2026. [DOI: 10.1002/net.70047](https://doi.org/10.1002/net.70047).
