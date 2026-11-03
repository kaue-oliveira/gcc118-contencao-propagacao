# Vistoria da etapa 2

## Parecer

A etapa 2 cumpre o entregável do enunciado: **formulação exata e testes em solver, com tempo, gap e número de variáveis e restrições**, incluindo diferentes cenários. O núcleo planejado na etapa 1 foi preservado. As limitações dos cenários reais estão explícitas e não foram tratadas como falhas de viabilidade ou provas de ótimo.

## Conferência por requisito

| Requisito | Evidência conferida | Resultado |
| --- | --- | --- |
| Problema e objetivo da proposta | Remover exatamente c vértices fora de S, minimizar alcançabilidade dirigida e incluir S na contagem | Atendido no modelo, avaliador e testes. |
| Formulação exata | Objetivo, orçamento, cobertura, restrições de arco, domínios e fixações; argumento de equivalência com BFS | Atendido; y e z contínuas são suficientes. |
| Tamanho do modelo | Atributos antes do presolve: 3n variáveis, n binárias, 2n contínuas e m+n+1 restrições | Conferido nos 82 casos e nos logs. |
| Tempo e gap | Runtime, montagem, tempo total, ObjVal, ObjBound, MIPGap e status | Registrados por cenário no CSV e JSON e confrontados com os logs. |
| Continuidade com a etapa 1 | Base original, todos os campos analíticos da auditoria e dez tabelas reproduzidas em pasta temporária | 7.115 vértices e 103.689 arcos; derivados idênticos, sem sobrescrever os originais. |
| Cenários planejados | Três recortes, S={2565} e quatro orçamentos | Os 12 casos do núcleo chegaram ao ótimo. |
| Diferentes cenários | Escala, orçamento, quantidade e identidade de origens e controles | Grade pareada e justificada; 70 complementos separados do núcleo. |
| Correção das soluções | Orçamento, proteção de S e conjunto alcançado reavaliados por BFS | Todas as 82 soluções conferem. |
| Validação independente da formulação | Enumeração de subconjuntos em todos os grafos simples dirigidos de três vértices, grafos aleatórios de oito vértices e controles estruturais | 1.196 comparações com o solver, sem divergência. |
| Modelos exportados | Quatro LP.gz reabertos e comparados com os modelos construídos | Objetivo, domínios, limites, RHS, sentidos e todos os coeficientes conferem. |
| Reprodutibilidade e organização | Configuração, ambiente, hashes, tabelas por escopo, logs, modelos e testes | Evidências auditadas e caminhos documentados; CSVs usam LF para preservar hashes no Git. |
| Próximas etapas | Manifesto com grafo, S e c; avaliador comum e identificação de ótimos | Benchmark disponível para heurísticas sem antecipar sua implementação. |

## Verificações executadas

- Suíte completa: **19 testes aprovados**, nenhum ignorado, incluindo as **1.196 comparações por enumeração**.
- Grade final: **82 cenários**, com **76 ótimos** e **6 TIME_LIMIT**. Os seis possuem solução viável validada; o maior gap foi **45,6468%**.
- Integração da etapa 1: reprodução em diretório temporário e comparação sem alteração dos arquivos originais.
- Consistência de todos os campos das três tabelas CSV com o JSON; comparação de tamanho, domínios, objetivo, limite, gap, tempo e status com os 82 logs.
- Conferência estrutural dos quatro modelos LP exportados, sem depender somente das contagens.
- Testes de adulteração de métricas e parâmetros, remoções inválidas, tempo zero sem incumbente e retomada de lote concluído sem alterar os arquivos.
- Relatório reduzido de nove para **quatro páginas**, com revisão visual de todas as páginas. Detalhes operacionais ficam no README e na documentação técnica.
- Os hashes de 114 arquivos científicos e de auditoria também foram conferidos nas versões preparadas para o Git. Uma cópia feita a partir do índice passou novamente na auditoria completa, confirmando a portabilidade após checkout.

A evidência de execução está em resultados/etapa-2/validacao/auditoria.json; a saída dos testes fica em validacao/testes.txt. O relatório apresenta os resultados do lote final; os históricos compactados não são misturados à análise principal.

## Correções e organização realizadas

O verificador passou a conferir cada célula dos CSVs, os parâmetros efetivos, métricas percentuais, a terminologia de otimalidade, os resumos dos logs e o conteúdo dos LPs. A auditoria também compara novamente os derivados da etapa 1.

Foram corrigidas a aceitação de IDs de remoção com tipo incorreto e a retomada de execução já concluída, que antes alterava metadados. A identificação da licença e caminhos locais passaram a ser removidos no encerramento de cada modelo. Os CSVs são escritos com LF, evitando que a normalização do Git invalide os hashes após publicação.

As dependências do solver ficam em requirements/. A entrega atual separa tabelas, evidências e validação. Os lotes anteriores foram compactados, com verificação de integridade antes de retirar as cópias expandidas. Reexecuções particulares têm uma pasta ignorada pelo Git.

## Limitações e continuidade

O limite de 30 s é uma restrição de recursos. Os seis casos TIME_LIMIT não oferecem ótimo conhecido, e o gap elevado de um deles impede uma afirmação forte sobre a qualidade da solução. Isso está declarado no relatório e deve ser mantido na comparação com heurísticas.

Há uma execução por caso e três realizações aleatórias de origens; a etapa não oferece inferência estatística de desempenho. Os recortes são enviesados e a propagação é uma hipótese sobre votos da Wiki-Vote. Repetições, análise consolidada e incertezas ficam para a etapa 4. A construtiva, a busca local/metaheurística e o gráfico de comparação com o exato ficam para a etapa 3 e a consolidação final.
