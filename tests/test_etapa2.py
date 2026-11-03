"""Verificação do modelo contra enumeração, sem usar o modelo como oráculo."""

from itertools import combinations
from pathlib import Path
import random
import sys
import tempfile
import unittest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from contencao.experimentos import carregar_grafos, gerar_cenarios
from contencao.instancias import Grafo, Instancia, ler_grafo
from contencao.propagacao import avaliar
from contencao.artefatos import escrever_tabelas, sanitizar_log
from contencao.verificacao import conferir_csv, conferir_resultado


def enumerar(instancia):
    """Enumera todos os subconjuntos de remoção e avalia caminhos por BFS."""
    candidatos = sorted(set(instancia.grafo.vertices) - set(instancia.origens))
    return min(len(avaliar(instancia, r)) for r in combinations(candidatos, instancia.orcamento))


class TestInstancias(unittest.TestCase):
    def test_grafo_rejeita_inconsistencias(self):
        for vertices, arcos in [([], []), ([1, 1], []), ([-1], []), ([True], []),
                                 ([1, 2], [(1, 3)]), ([1], [(1, 1)]),
                                 ([1, 2], [(1, 2), (1, 2)])]:
            with self.subTest(vertices=vertices, arcos=arcos), self.assertRaises(ValueError):
                Grafo(vertices, arcos)

    def test_origens_e_orcamento(self):
        grafo = Grafo([1, 2], [(1, 2)])
        for origens, c in [([], 0), ([3], 0), ([1, 1], 0), ([1], -1),
                           ([1], 2), ([1], 0.5), ([1], True)]:
            with self.subTest(origens=origens, c=c), self.assertRaises(ValueError):
                Instancia(grafo, origens, c)

    def test_csv_preserva_isolados(self):
        with tempfile.TemporaryDirectory() as pasta:
            v, a = Path(pasta) / "v.csv", Path(pasta) / "a.csv"
            v.write_text("id\n1\n2\n3\n", encoding="utf-8")
            a.write_text("origem,destino\n1,2\n", encoding="utf-8")
            grafo = ler_grafo(v, a)
            self.assertEqual(grafo.vertices, (1, 2, 3))
            self.assertEqual(len(avaliar(Instancia(grafo, [1], 0), [])), 2)

    def test_csv_rejeita_cabecalho_e_linha(self):
        with tempfile.TemporaryDirectory() as pasta:
            v, a = Path(pasta) / "v.csv", Path(pasta) / "a.csv"
            a.write_text("origem,destino\n1,2\n", encoding="utf-8")
            for conteudo in ["vertices\n1\n2\n", "id\n1\ninvalido\n", "id\n1,2\n"]:
                v.write_text(conteudo, encoding="utf-8")
                with self.assertRaises(ValueError):
                    ler_grafo(v, a)

    def test_remocoes_invalidas(self):
        instancia = Instancia(Grafo([1, 2, 3], [(1, 2), (2, 3)]), [1], 1)
        for removidos in [[], [2, 2], [1], [4], [2, 3], [2.0]]:
            with self.subTest(removidos=removidos), self.assertRaises(ValueError):
                avaliar(instancia, removidos)

    def test_remocao_nao_aceita_booleano_como_id(self):
        instancia = Instancia(Grafo(range(3), [(0, 1), (1, 2)]), [0], 1)
        with self.assertRaises(ValueError):
            avaliar(instancia, [True])

    def test_direcao_e_corte_de_caminhos(self):
        grafo = Grafo([1, 2, 3, 4], [(1, 2), (2, 3)])
        self.assertEqual(avaliar(Instancia(grafo, [3], 0), []), {3})
        self.assertEqual(avaliar(Instancia(grafo, [1], 1), [2]), {1})
        self.assertEqual(avaliar(Instancia(grafo, [1, 4], 1), [2]), {1, 4})

    def test_configuracao_e_recortes(self):
        import json
        config = json.loads((RAIZ / "experimentos/etapa-2.json").read_text(encoding="utf-8"))
        grafos = carregar_grafos(RAIZ, config)
        self.assertEqual([(len(g.vertices), len(g.arcos)) for g in grafos.values()],
                         [(100, 961), (300, 6962), (1000, 32207), (7115, 103689)])
        cenarios = gerar_cenarios(config, grafos)
        self.assertEqual(len(cenarios), 82)
        self.assertEqual(cenarios, gerar_cenarios(config, grafos))
        self.assertEqual(len({c['id'] for c in cenarios}), 82)
        nucleo = [c for c in cenarios if c['escopo'] == 'nucleo']
        self.assertEqual(len(nucleo), 12)
        self.assertTrue(all(c['origens'] == [2565] and c['orcamento'] in {1, 3, 5, 10} for c in nucleo))
        # Todos os perfis de origens usam os mesmos quatro orçamentos.
        familias = {}
        for c in cenarios:
            if c['grupo'] in ('sensibilidade_origens', 'origens_rede_completa'):
                familias.setdefault((c['grafo'], tuple(c['origens'])), set()).add(c['orcamento'])
        self.assertTrue(all(orcamentos == {1, 3, 5, 10} for orcamentos in familias.values()))
        # No recorte de 300, maior saída k=1 é o núcleo S={2565};
        # cada k e cada realização aleatória tem quatro comparações pareadas.
        recorte = [c for c in cenarios if c['grafo'] == 'recorte_300' and c['orcamento'] > 0]
        self.assertEqual(len(recorte), 3 * 4 * (1 + 3))
        for semente in (42, 123, 2026):
            origens_por_k = {c['k']: set(c['origens']) for c in recorte if c['semente_origens'] == semente}
            self.assertLessEqual(origens_por_k[1], origens_por_k[3])
            self.assertLessEqual(origens_por_k[3], origens_por_k[5])


class TestArtefatos(unittest.TestCase):
    def test_tabelas_separam_escopos_e_rejeitam_adulteracao(self):
        resultados = [
            {"id": "a", "escopo": "nucleo", "origens": [1], "objetivo_bfs": 2, "gap": 0.0},
            {"id": "b", "escopo": "complementar", "origens": [3], "objetivo_bfs": None, "gap": None},
        ]
        with tempfile.TemporaryDirectory() as pasta:
            saida = Path(pasta)
            escrever_tabelas(saida, resultados)
            conferir_csv(saida / 'metricas.csv', resultados)
            conferir_csv(saida / 'tabelas/nucleo.csv', resultados[:1], resultados)
            conferir_csv(saida / 'tabelas/complementar.csv', resultados[1:], resultados)
            tabela = saida / 'metricas.csv'
            tabela.write_text(tabela.read_text().replace(',2,0.0', ',9,0.0'), encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError, 'CSV diverge'):
                conferir_csv(tabela, resultados)

    def test_log_remove_identificacao_sem_alterar_evidencia(self):
        with tempfile.TemporaryDirectory() as pasta:
            log = Path(pasta) / 'teste.log'
            log.write_text('Academic license 123 - registered to exemplo\nSet parameter LogFile to value "/pasta/privada/teste.log"\nBest objective 2.0, best bound 2.0, gap 0.0000%\n', encoding='utf-8')
            sanitizar_log(log)
            texto = log.read_text()
            self.assertNotIn('registered to', texto)
            self.assertNotIn('/pasta/privada', texto)
            self.assertIn('Best objective 2.0, best bound 2.0, gap 0.0000%', texto)
            sanitizar_log(log)
            self.assertEqual(texto, log.read_text())


try:
    from contencao.modelos.exato import ambiente, construir_modelo, resolver
    TEM_GUROBI = True
except ImportError:
    TEM_GUROBI = False


@unittest.skipUnless(TEM_GUROBI, "Instale requirements-solver.txt para validar o solver.")
class TestExato(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contexto = ambiente()
        cls.env = cls.contexto.__enter__()
        cls.comparacoes = 0

    @classmethod
    def tearDownClass(cls):
        cls.contexto.__exit__(None, None, None)
        print(f"\nComparações solver x enumeração completa: {cls.comparacoes}", flush=True)

    def conferir(self, instancia):
        esperado = enumerar(instancia)
        result = resolver(instancia, self.env)
        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual(result["objetivo_bfs"], esperado)
        self.assertAlmostEqual(result["objetivo_solver"], esperado)
        self.assertAlmostEqual(result["limite_inferior"], esperado)
        self.assertEqual(result["gap"], 0)
        self.assertTrue(result["otimo_comprovado"])
        self.assertTrue(result["validacao_bfs"])
        self.assertTrue(result["objetivo_confere_bfs"])
        self.assertEqual(result["variaveis"], 3 * len(instancia.grafo.vertices))
        self.assertEqual(result["restricoes"], len(instancia.grafo.arcos) + len(instancia.grafo.vertices) + 1)
        type(self).comparacoes += 1
        return result

    def test_todos_grafos_dirigidos_tres_vertices(self):
        vertices = (0, 1, 2)
        possiveis = [(i, j) for i in vertices for j in vertices if i != j]
        for mascara in range(1 << len(possiveis)):
            grafo = Grafo(vertices, [a for indice, a in enumerate(possiveis) if mascara & (1 << indice)])
            for k in range(1, 4):
                for origens in combinations(vertices, k):
                    for c in range(4 - k):
                        with self.subTest(mascara=mascara, S=origens, c=c):
                            self.conferir(Instancia(grafo, origens, c))

    def test_grafos_aleatorios_oito_vertices(self):
        for semente in range(12):
            rng = random.Random(semente)
            vertices = tuple(range(8))
            arcos = [(i, j) for i in vertices for j in vertices if i != j and rng.random() < 0.25]
            grafo = Grafo(vertices, arcos)
            for k in [1, 3]:
                origens = tuple(rng.sample(list(vertices), k))
                for c in range(9 - k):
                    with self.subTest(semente=semente, S=origens, c=c):
                        self.conferir(Instancia(grafo, origens, c))

    def test_gargalo_e_caminhos_alternativos(self):
        grafo = Grafo(range(7), [(0, 1), (1, 2), (1, 3), (2, 4), (3, 4), (4, 5)])
        result = self.conferir(Instancia(grafo, [0], 1))
        self.assertEqual(result["removidos"], [1])
        grafo2 = Grafo(range(4), [(0, 1), (0, 2), (1, 3), (2, 3)])
        self.assertEqual(self.conferir(Instancia(grafo2, [0], 1))["objetivo_bfs"], 3)

    def test_somente_origens_e_grafo_sem_arcos(self):
        self.assertEqual(self.conferir(Instancia(Grafo([99], []), [99], 0))["objetivo_bfs"], 1)
        self.assertEqual(self.conferir(Instancia(Grafo(range(5), []), [0, 1], 3))["objetivo_bfs"], 2)

    def test_tempo_zero_sem_incumbente(self):
        instancia = Instancia(Grafo(range(4), [(0, 1), (1, 2), (2, 3)]), [0], 1)
        result = resolver(instancia, self.env, limite_tempo=0)
        self.assertEqual(result["status"], "TIME_LIMIT")
        self.assertEqual(result["solucoes"], 0)
        for campo in ["objetivo_solver", "objetivo_bfs", "gap", "gap_percentual", "removidos", "validacao_bfs"]:
            self.assertIsNone(result[campo])

    def test_dominios_e_fixacoes_do_modelo(self):
        from gurobipy import GRB
        instancia = Instancia(Grafo(range(4), [(0, 1)]), [0], 1)
        model, v, y, z = construir_modelo(instancia, self.env)
        try:
            self.assertEqual(model.NumBinVars, 4)
            self.assertEqual(v[0].UB, 0)
            self.assertEqual(z[0].UB, 0)
            self.assertTrue(all(y[i].VType == z[i].VType == GRB.CONTINUOUS for i in range(4)))
            from contencao.verificacao import conferir_modelo_lp
            with tempfile.TemporaryDirectory() as pasta:
                arquivo = Path(pasta) / 'modelo.lp.gz'
                model.write(str(arquivo))
                evidencia = conferir_modelo_lp(arquivo, instancia, self.env)
                self.assertTrue(evidencia['conteudo_confere'])
                self.assertEqual(evidencia['variaveis'], 12)
        finally:
            model.dispose()

    def test_limites_invalidos(self):
        instancia = Instancia(Grafo([0], []), [0], 0)
        for parametros in [{"limite_tempo": -1}, {"limite_tempo": float("nan")},
                           {"gap_alvo": -0.1}, {"threads": 0}, {"semente": -1}, {"limite_nos": -1}]:
            with self.assertRaises(ValueError):
                resolver(instancia, self.env, **parametros)

    def test_auditoria_rejeita_parametros_e_metricas_adulterados(self):
        from copy import deepcopy
        from contencao.grafos import reach
        grafo = Grafo(range(4), [(0, 1), (1, 2), (2, 3)])
        instancia = Instancia(grafo, [0], 1)
        cenario = {'id': 'teste', 'vertices': 4, 'arcos': 3, 'origens': [0], 'orcamento': 1,
                   'alcancados_sem_remocao': len(reach(grafo.adjacencia(), [0]))}
        result = {**cenario, **resolver(instancia, self.env)}
        protocolo = {'limite_tempo_s': 30.0, 'gap_alvo': 0.0, 'threads': 1, 'semente': 42}
        conferir_resultado(cenario, result, grafo, protocolo)
        for campo, valor in [('gap_percentual', 100), ('restricoes', 99), ('objetivo_bfs', 99), ('otimo_comprovado', False)]:
            adulterado = deepcopy(result)
            adulterado[campo] = valor
            with self.subTest(campo=campo), self.assertRaises(RuntimeError):
                conferir_resultado(cenario, adulterado, grafo, protocolo)
        adulterado = deepcopy(result)
        adulterado['parametros']['Threads'] = 4
        with self.assertRaisesRegex(RuntimeError, 'Parâmetros'):
            conferir_resultado(cenario, adulterado, grafo, protocolo)

    def test_retomar_lote_concluido_preserva_arquivos(self):
        import json
        from contextlib import redirect_stdout
        import io
        from unittest.mock import patch
        from contencao.experimentos import executar
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            v, a, arquivo_config = raiz/'v.csv', raiz/'a.csv', raiz/'config.json'
            v.write_text('id\n1\n2\n3\n', encoding='utf-8')
            a.write_text('origem,destino\n1,2\n2,3\n', encoding='utf-8')
            config = {'solver': {'limite_tempo_s': 30, 'gap_alvo': 0.0, 'threads': 1, 'semente': 42},
                      'grafos': {'teste': {'vertices': str(v), 'arcos': str(a)}},
                      'grupos': [{'nome': 'teste', 'grafos': ['teste'], 'perfis': [{'criterio': 'fixo', 'origens': [1]}], 'orcamentos': [0, 1]}]}
            arquivo_config.write_text(json.dumps(config), encoding='utf-8')
            saida = raiz/'resultados'
            with redirect_stdout(io.StringIO()):
                executar(RAIZ, arquivo_config, saida)
                antes = {str(p.relative_to(saida)): p.read_bytes() for p in saida.rglob('*') if p.is_file()}
                with patch('contencao.modelos.exato.ambiente', side_effect=AssertionError('Não deve reabrir licença')):
                    executar(RAIZ, arquivo_config, saida, retomar=True)
                depois = {str(p.relative_to(saida)): p.read_bytes() for p in saida.rglob('*') if p.is_file()}
            self.assertEqual(antes, depois)
            config['solver']['threads'] = 2
            arquivo_config.write_text(json.dumps(config), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'mudaram'):
                executar(RAIZ, arquivo_config, saida, retomar=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
