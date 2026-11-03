# Arquivo histórico da etapa 2

Os arquivos desta pasta preservam os lotes anteriores à vistoria final. Não integram as tabelas nem as conclusões da entrega atual, localizada em ../../etapa-2/.

- **piloto-inicial.tar.gz:** primeiro lote exploratório, anterior à correção da grade pareada.
- **grade-revisada-anterior.tar.gz:** lote com a grade revisada, anterior às melhorias de auditoria, organização e portabilidade dos hashes no Git.

Cada pacote mantém integralmente os resultados, logs, LPs e registros de testes que existiam naquele lote. A configuração efetiva e os hashes do código original estão dentro do respectivo execucao.json. Esses hashes são históricos e não devem ser substituídos pelos do código final. O verificador atual audita a entrega final, não esses esquemas antigos.

| Pacote | Cenários | SHA-256 do pacote |
| --- | --- | --- |
| grade-revisada-anterior.tar.gz | 82 | 296b3f0fa6d16871f79f6d1665f60e8633b1e166ad106010247be90fe7ca055a |
| piloto-inicial.tar.gz | 74 | f5538dcdbffedb94a5cbc74f58f095f292d4cff95fb9e7f7453e23a948d0027c |

Para listar um pacote sem extrair: tar -tzf resultados/arquivo/etapa-2/piloto-inicial.tar.gz. Se precisar consultá-lo, extraia em uma pasta local separada. Não misture suas medições com as da entrega final nem escolha o menor tempo entre lotes.
