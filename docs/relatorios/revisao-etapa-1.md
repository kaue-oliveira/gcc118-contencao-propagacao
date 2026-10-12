# Revisão da entrega da etapa 1

Revisão realizada em 12/10/2026 sobre o repositório local e a versão original de seis páginas do relatório. A imagem fornecida reproduz corretamente o requisito da etapa 1 da seção 2 do [enunciado](../enunciado.pdf).

**Parecer:** a entrega atende ao conteúdo solicitado: tamanho da instância, qualidade e viabilidade dos dados. Os resultados numéricos conferem com os dados brutos, as tabelas e o código. A versão original tinha inconsistências de reprodução e não incluía o link do repositório; esses pontos foram corrigidos no [PDF](etapa-1-wiki-vote.pdf) e na [fonte editável](etapa-1-wiki-vote.md).

## Correspondência com o enunciado

| Requisito | Evidência na entrega | Avaliação |
| --- | --- | --- |
| Coleta e origem dos dados | Seção 2: SNAP, arquivo original, significado dos IDs e dos arcos, cobertura temporal e coleta registrada | Atendido |
| Tamanho da instância | Seções 2, 4 e 7: vértices, arcos, bytes, densidade, componentes e recortes | Atendido |
| Qualidade dos dados | Seção 3: validação de colunas, duplicatas, laços, reciprocidade e limitações de completude | Atendido |
| Análise exploratória | Seções 4 a 6: conectividade, graus, figura e seis cenários de alcançabilidade | Atendido |
| Viabilidade dos dados | Seção 7: processamento executado, recortes crescentes e dimensões teóricas do modelo | Atendido, sem confundir com viabilidade de resolução do PLI |
| Disponibilizar GitHub aos docentes | Link no início do PDF e no README | Link adicionado; envio aos docentes não foi realizado nesta revisão |
| Documentação clara do código | Docstrings, README, caminhos e comandos reproduzíveis | Atendido após as correções de documentação |

O enunciado exige formulação exata e testes em solver na etapa 2, heurísticas e comparação ao exato na etapa 3, análise experimental consolidada na etapa 4 e apresentação na etapa 5. A ausência dessas implementações não torna a entrega da etapa 1 incompleta. As estimativas de variáveis e restrições são um planejamento adicional, identificado como teórico.

## Conferência dos resultados

Foi executada a rotina `analisar()` em diretórios temporários, preservando os resultados versionados. Após normalizar as chaves JSON, somente o tempo de execução diferiu: os demais campos, inclusive os checksums dos módulos, coincidiram. Os dez CSVs gerados reproduziram exatamente as linhas e cabeçalhos dos arquivos versionados, desconsiderando apenas a representação das quebras de linha.

Uma segunda implementação, com NetworkX 3.7 e NumPy no ambiente temporário de revisão, conferiu diretamente o arquivo bruto e os arquivos derivados:

| Medida | Resultado confirmado |
| --- | --- |
| Vértices / arcos | 7.115 / 103.689 |
| Registros inválidos / duplicatas / laços | 0 / 0 / 0 |
| Pares recíprocos / arcos recíprocos | 2.927 / 5.854 |
| Densidade | 0,0020485375110809584 |
| Componentes fracas / fortes | 24 / 5.816 |
| Maior componente fraca | 7.066 vértices / 103.663 arcos |
| Maior componente forte | 1.300 vértices / 39.456 arcos |
| Demais componentes fracas | 3 de tamanho 3 / 20 de tamanho 2 |
| Demais componentes fortes | 5.815 de tamanho 1 |
| Graus, percentis e desvios | Todos os valores do JSON e cada linha de graus.csv confirmados |
| Cenários por maior saída | 2.316 / 2.320 / 2.325 alcançados |
| Cenários aleatórios, semente 42 | 1 / 2.317 / 2.318 alcançados |
| Recorte de 100 vértices | 961 arcos / 47 SCCs / 77 alcançados |
| Recorte de 300 vértices | 6.962 arcos / 100 SCCs / 256 alcançados |
| Recorte de 1.000 vértices | 32.207 arcos / 399 SCCs / 867 alcançados |

Também foram conferidos todos os registros de `componentes.csv`, a origem dos arcos processados, a ordem BFS de seleção, o aninhamento dos recortes, a igualdade de cada recorte com o subgrafo induzido original, as densidades e a validade dos orçamentos planejados. Os conjuntos de origens e as porcentagens dos seis cenários coincidiram com o JSON.

As funções de alcançabilidade, componentes fracas e componentes fortes de `src/contencao/grafos.py` foram comparadas com NetworkX nos 4.096 grafos dirigidos sem laços possíveis sobre quatro vértices. A alcançabilidade foi conferida a partir de cada vértice. Também foi verificado o grafo vazio. Todos os casos passaram. Essas verificações foram executadas no ambiente temporário; NetworkX não foi adicionado como dependência do projeto.

A entrada `scripts/analisar.py` também foi executada em uma cópia temporária, com diretório de trabalho diferente da raiz: o JSON reproduziu os mesmos resultados e os arquivos foram escritos nos caminhos previstos. A compilação de `src/` e `scripts/` passou com `compileall`, assim como `git diff --check`. A versão atual do PDF foi reaberta, com cinco páginas, resultados e metadados de execução conferidos, e link clicável do GitHub verificado na primeira página. Os hashes permanecem disponíveis no JSON e na documentação do repositório.

## Consistência da interpretação

- O arquivo descreve votação dirigida. Usá-lo para propagação por caminhos é uma hipótese experimental explicitada, adequada à proposta da modalidade B; não permite concluir eficácia real contra epidemias ou malware.
- A referência numérica é a rede completa, não apenas a maior componente fraca. A divergência entre a descrição e a tabela do SNAP foi tratada corretamente.
- Arcos recíprocos são relações dirigidas diferentes, não duplicatas. A orientação foi preservada.
- A figura usa a fração de todos os vértices com grau maior ou igual a x. Os graus zero ficam fora do eixo horizontal logarítmico, mas permanecem no denominador. A regeneração agora está disponível.
- A origem 5931 não tem saída. O cenário unitário é um controle trivial; o relatório corretamente evita tratá-lo como evidência de desempenho de métodos.
- A seleção BFS garante conexão fraca e recortes crescentes, mas concentra vizinhos do vértice de maior saída. O viés e a densidade elevada estão explicitados.
- A conta de 3|V| variáveis e |A| + |V| + 1 restrições principais corresponde à formulação compacta apresentada na proposta, com fixações de S em limites de variáveis. Os quatro tamanhos previstos estão aritmeticamente corretos. Só a etapa 2 medirá o modelo efetivamente construído e a dificuldade de resolução.
- A [Tabela 1 do artigo-base](https://onlinelibrary.wiley.com/doi/10.1002/net.70047) lista seis redes reais, sem Wiki-Vote. Usar outra rede sustenta a adaptação proposta, mas não prova ineditismo na literatura.

## Problemas encontrados e correções

| Local na versão original | Problema | Correção |
| --- | --- | --- |
| PDF, seção 8 | `python3 analisar.py` não funciona na raiz atual | Substituído por `python3 scripts/analisar.py` |
| PDF, seção 8 | JSON e tabelas descritos em caminhos anteriores à organização do repositório | Caminhos reais de resultados, dados processados e instâncias documentados |
| PDF, legenda da Figura 1 | Fonte indicada como `resultados/graus.csv` | Corrigida para `resultados/etapa-1/graus.csv` |
| PDF, seção 7 | 0,64 s e Python 3.12.14 não correspondem ao JSON incluído | Tempo e Python agora são preenchidos a partir do JSON: 0,37 s e 3.12.3 nesta versão |
| PDF, seção 8 | Menção a gerar_relatorio.py e DOCX ausentes | Adicionados o gerador real em scripts/, a fonte Markdown e dependências opcionais; removida a instrução de DOCX |
| PDF | Link do GitHub não informado | Link clicável na primeira página e no README |
| PDF, referências | Referências a atividade/comentário do Campus Virtual sem cópia no repositório | Mantidas apenas as referências ao SNAP e ao artigo-base; metaheurística mantida como planejamento |

A data original de coleta e de elaboração foi preservada, com identificação explícita da revisão em 12/10/2026. Os dados brutos, as tabelas e os algoritmos de análise não precisaram de alteração. A figura foi regenerada a partir dos graus conferidos; o PDF foi regenerado e revisado visualmente em todas as páginas.

Na edição solicitada pelo autor, a seção técnica de reprodução foi retirada do relatório. Comandos, caminhos e hashes continuam documentados no repositório. A escrita foi simplificada, mantendo os resultados e as limitações da análise. O enunciado e a proposta foram removidos das referências do PDF, e a conclusão passou a ser a seção 8.

## Limitações e próximas entregas

A revisão não acessou o Campus Virtual nem verificou o envio da atividade, aprovação da proposta ou o comentário docente mencionado na versão original. A data de coleta é o registro existente no projeto, não uma data inferida do conteúdo de 2008. O enunciado prevê a etapa 1 até 09/10/2026; a existência do PDF não comprova quando ocorreu a submissão.

O enunciado contém uma inconsistência editorial: o cabeçalho dos critérios menciona 20 pontos, mas os pesos somam 30 e o início do documento indica 30. Isso pertence ao enunciado e não deve ser convertido em requisito adicional para a etapa 1.

Ainda será necessário implementar e avaliar o solver, heurísticas e metaheurística nas fases correspondentes, registrar tempo/gap/status, comparar qualidade versus tempo e discutir incertezas. A revisão atual não garante que o solver resolva a rede completa em tempo hábil, nem que os recortes BFS representem todas as dificuldades da rede. Para a etapa 1, não há lacuna técnica identificada nos três itens solicitados.
