# Desenho experimental da etapa 2

A etapa verifica a formulação e a capacidade do solver de obter soluções e provar otimalidade. O total de cenários resulta das comparações abaixo; não é uma exigência do enunciado nem um tamanho de amostra estatístico.

## Perguntas e grade

| Bloco | Pergunta | Comparação | Casos |
| --- | --- | --- | --- |
| Núcleo da etapa 1 | O modelo resolve as instâncias planejadas? | Recortes 100/300/1.000; S={2565}; c=1/3/5/10 | 12 |
| Escala e referência | A aplicação completa é viável? Os casos c=0 conferem? | c=0 nas quatro escalas e os quatro orçamentos na rede completa | 8 |
| Origens no recorte | Identidade e quantidade de origens alteram alcance e dificuldade? | Grafo fixo com 300 vértices; k=1/3/5; maior saída e três realizações aleatórias; quatro orçamentos | 44 adicionais |
| Origens na rede completa | A sensibilidade aparece fora do recorte? | Rede completa; k=3; maior saída e três realizações aleatórias; quatro orçamentos | 16 |
| Controle sem saída | O modelo respeita orçamento e proteção de S quando não há propagação? | S={5931}; c=0 e c=10; ótimo conhecido igual a 1 | 2 |

O núcleo contém 12 casos, e os complementos contêm 70. Os testes em grafos pequenos pertencem à validação de correção e não entram nessa soma.

## Justificativa dos fatores

**Tamanho e orçamento.** Os três recortes e os valores c=1/3/5/10 foram definidos na etapa 1. Mantê-los permite cumprir o planejamento e variar o orçamento com grafo e S fixos. A rede completa avalia a aplicação real, sem extrapolar o tempo dos recortes. Os orçamentos são absolutos: c/(n-k) varia entre tamanhos, portanto diferenças de redução não medem exclusivamente efeito de n ou da topologia.

**Origens no recorte de 300.** O tamanho intermediário permite fixar um grafo para comparar S. k=1/3/5 retoma as quantidades examinadas na etapa 1. As seleções são aninhadas: uma origem de um conjunto menor não é substituída quando k aumenta. Maior saída é calculado no próprio grafo, com desempate pelo menor ID. Aqui o grau escolhe origens protegidas, não remoções.

**Sorteios.** Usam-se random.Random(semente).sample sobre os IDs ordenados, com sementes 42, 123 e 2026 fixadas antes do primeiro lote. Seus valores são identificadores reprodutíveis, sem significado estrutural. Não há filtro por grau, alcance ou resultado do solver. Três realizações permitem observar casos diferentes, mas não estimar estatisticamente todas as origens. Os conjuntos aninhados não são amostras independentes.

**Comparações pareadas.** Todos os perfis usam os mesmos quatro orçamentos. No recorte de 300, o cruzamento contém 3 quantidades × (1 ranking + 3 sorteios) × 4 orçamentos = 48 casos. Os quatro casos de maior saída com k=1 coincidem com S={2565} do núcleo; restam 44 adicionais, sem duplicação.

**Extensão na rede completa.** Fixa-se k=3, quantidade já presente no diagnóstico da etapa 1, para comparar os mesmos critérios no grafo original. São quatro perfis e quatro orçamentos, ou 16 casos. O escopo não cobre todos os k na rede completa; a variação completa de k é estudada no recorte fixo.

**Controles.** c=0 verifica a concordância com a BFS da etapa 1. A origem 5931 já havia sido identificada sem saída; usar c=0 e c=10, extremos da grade, verifica também a igualdade de orçamento. Esses controles não são evidência de contenção bem-sucedida.

## Protocolo e critérios de aceitação

TimeLimit=30 s por cenário limita os recursos, com teto nominal de 41 minutos de resolução para a grade. Não existe garantia de que esse tempo prove qualquer ótimo. MIPGap=MIPGapAbs=0 buscam fechar os limites dentro das tolerâncias numéricas. Threads=1 fixa o paralelismo; Seed=42 fixa a semente do solver, separada das sementes das origens.

Os modelos são independentes e sequenciais, sem fornecer solução de outro cenário nem heurística própria. Há uma execução por caso. Os tempos são observações individuais, sem intervalos de confiança, médias ou alegação de significância.

A aceitação exige:

1. Instâncias e parâmetros válidos, com origem protegida e exatamente c remoções.
2. Contagens 3n e m+n+1 confirmadas antes do presolve.
3. Concordância do solver com enumeração completa nos grafos pequenos.
4. Alcance e remoções reais conferidos por BFS.
5. CSV, JSON, logs e modelos exportados consistentes entre si.
6. Preservação de TIME_LIMIT, limites e gap; ausência de incumbente representada por valores nulos.

Não se exige gap zero em todos os casos reais. O escopo do benchmark com ótimo conhecido fica restrito aos cenários comprovados; os demais oferecem limites para as próximas etapas.

## Relação com as etapas 1, 3 e 4

A auditoria reproduz a etapa 1 em pasta temporária e compara a base, os recortes, as tabelas e os campos analíticos. Os arquivos versionados permanecem preservados.

Na etapa 3, devem-se usar os mesmos IDs de S, grafos e orçamentos do manifesto. O campo otimo_comprovado permite separar comparação com ótimo conhecido de comparação com limites. A avaliação BFS é reutilizável pelas heurísticas. Repetições de desempenho, comparação consolidada e incertezas pertencem à etapa 4.

## Histórico metodológico

A grade foi ajustada após um piloto: acrescentou-se o orçamento 3 às comparações de origens e retiraram-se da grade principal orçamentos altos sem regra sistemática de seleção. A extensão da rede completa foi delimitada a k=3. Nenhum caso foi removido por ter resultado trivial ou gap alto.

Os lotes anteriores estão preservados em resultados/arquivo/etapa-2/, com configurações e evidências históricas. Após a vistoria, a grade principal foi executada integralmente de novo. As conclusões usam somente esse lote, sem escolher o melhor tempo entre execuções. O estudo é exploratório e não é apresentado como pré-registrado.
