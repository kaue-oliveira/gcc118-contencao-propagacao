# Resultados da etapa 2

Esta pasta contém a **execução final auditada**. O núcleo tem 12 casos previstos na etapa 1; os complementos têm 70 casos. Os lotes anteriores estão compactados em [arquivo histórico](../arquivo/etapa-2/README.md) e não entram nas conclusões principais.

## Onde encontrar cada informação

| Arquivo ou pasta | Conteúdo |
| --- | --- |
| [metricas.csv](metricas.csv) | Todos os 82 cenários, uma linha por caso. |
| [tabelas/nucleo.csv](tabelas/nucleo.csv) | Os 12 casos planejados: três recortes e quatro orçamentos. |
| [tabelas/complementar.csv](tabelas/complementar.csv) | Os demais 70 casos, incluindo referências c=0, origens e controles. |
| [execucao.json](execucao.json) | Registro de referência: configuração, ambiente, hashes, origens, remoções e conjuntos alcançados. |
| evidencias/logs/ | Um log por cenário, sem identificação da licença nem caminho absoluto local. |
| evidencias/modelos/ | Quatro modelos LP.gz, um por tamanho, com S={2565} e c=5. O Gurobi lê esses arquivos diretamente; também podem ser descompactados como gzip. |
| [validacao/auditoria.json](validacao/auditoria.json) | Resultado da vistoria, testes e hashes de todas as evidências conferidas. |
| [validacao/etapa-1.json](validacao/etapa-1.json) | Conferência da base, auditoria e dez tabelas da etapa 1, reproduzidas em pasta temporária. |
| [validacao/testes.txt](validacao/testes.txt) | Saída completa dos testes automatizados. |

## Como ler as métricas

- **id, grafo, origens e orcamento:** identificam o problema efetivamente resolvido. origens e removidos são listas JSON dentro do CSV. Use os IDs gravados, sem sortear novamente.
- **escopo e grupo:** separam núcleo e complementos e indicam a pergunta experimental.
- **objetivo_bfs:** alcance real após as remoções, incluindo S. É a avaliação usada nas comparações futuras.
- **objetivo_solver e limite_inferior:** ObjVal e ObjBound do Gurobi. O ótimo está entre o limite inferior e uma solução viável. Nesta entrega, objetivo_solver coincide com objetivo_bfs em todas as soluções.
- **gap e gap_percentual:** MIPGap do Gurobi em fração e porcentagem; 0,01 corresponde a 1%. O gap usa o objetivo do solver. gap_bfs usa a solução reavaliada por BFS.
- **status e otimo_comprovado:** registram o encerramento e se os limites fecharam, dentro das tolerâncias numéricas. TIME_LIMIT não é prova de ótimo.
- **tempo_solver_s:** Runtime de optimize(). tempo_montagem_s inclui construção, configuração e eventual exportação LP. tempo_total_s cobre montagem e resolução; exclui autenticação da licença e avaliação BFS. Os tempos são individuais, em segundos.
- **variaveis, binarias, continuas e restricoes:** tamanho original do modelo antes do presolve. Limites de variáveis e fixações de S não contam como linhas.
- **nao_zeros, nos_branch_bound e work:** coeficientes da matriz, nós da busca e unidades de trabalho do solver, preservados como informação complementar.

Sem incumbente, os campos de solução e gap são nulos. Um gap residual limita a conclusão de qualidade, mesmo quando a solução satisfaz todas as restrições.

## Uso na etapa 3

Para comparar uma heurística, mantenha grafo, IDs de S, orçamento e direção dos arcos. Confira os hashes dos dados no manifesto e avalie as remoções com contencao.propagacao.avaliar. Somente casos com otimo_comprovado=true permitem calcular desvio em relação a um ótimo conhecido; nos demais, utilize os limites e identifique a incerteza restante.

CSV e tabelas são derivados do JSON. Não os edite manualmente. Os comandos de execução e verificação dos experimentos ficam no [README principal](../../README.md). Reexecuções próprias devem usar resultados/locais/ para preservar a entrega auditada.
