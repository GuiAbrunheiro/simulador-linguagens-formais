from simulador.complexidade import ANALISE, medir


def test_todos_os_modulos_tem_analise():
    modulos = {a.modulo[0] for a in ANALISE}
    assert modulos == {"1", "2", "3", "4", "5"}
    for a in ANALISE:
        assert "Ω" in a.melhor and "O(" in a.pior and a.justificativa


def test_medicao_confirma_as_ordens_de_crescimento():
    pequeno, grande = medir((16, 32))
    razao = lambda chave: grande[chave] / pequeno[chave]
    for linear in ("afd", "earley", "ap", "mt_soma"):
        assert 1.8 <= razao(linear) <= 2.2, linear          # dobra  -> Θ(n)
    for quadratica in ("mt_wsw", "earley_amb"):
        assert 3.5 <= razao(quadratica) <= 4.2, quadratica  # 4x     -> Θ(n²)
