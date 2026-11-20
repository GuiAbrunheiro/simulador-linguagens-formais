from pathlib import Path

import pytest

from simulador import Alfabeto, AutomatoFinito

EXEMPLOS = Path(__file__).resolve().parent.parent / "exemplos"
SIGMA = Alfabeto(["a", "b"])


def test_exemplo_do_enunciado():
    afd = AutomatoFinito.de_json(EXEMPLOS / "afd_ab.json")
    resultado = afd.simular("ab")
    assert afd.tipo == "AFD"
    assert resultado.caminho_texto() == "q0 -> q1 -> q2"
    assert resultado.aceita


def test_afd_trava_sem_transicao():
    afd = AutomatoFinito.de_json(EXEMPLOS / "afd_ab.json")
    resultado = afd.simular("aa")
    assert not resultado.aceita
    assert resultado.caminho == ["q0", "q1"]
    assert "Não há transição" in resultado.motivo


def test_afd_rejeita_simbolo_fora_do_alfabeto():
    afd = AutomatoFinito.de_json(EXEMPLOS / "afd_ab.json")
    assert "não pertence a Σ" in afd.simular("ac").motivo


def test_afd_par_de_a_contra_definicao():
    afd = AutomatoFinito.de_json(EXEMPLOS / "afd_par_de_a.json")
    for w in SIGMA.sigma_estrela(7):
        assert afd.aceita(w) == (w.count("a") % 2 == 0), w


def test_afn_termina_em_ab_contra_definicao():
    afn = AutomatoFinito.de_json(EXEMPLOS / "afn_termina_ab.json")
    assert afn.tipo == "AFN"
    for w in SIGMA.sigma_estrela(7):
        assert afn.aceita(w) == w.endswith("ab"), w


def test_afn_mostra_conjuntos_de_estados_e_um_caminho():
    afn = AutomatoFinito.de_json(EXEMPLOS / "afn_termina_ab.json")
    resultado = afn.simular("aab")
    assert [sorted(p.destino) for p in resultado.passos] == [["q0", "q1"], ["q0", "q1"], ["q0", "q2"]]
    assert resultado.caminho == ["q0", "q0", "q1", "q2"]


def test_afn_com_transicao_lambda():
    afn = AutomatoFinito.de_json(EXEMPLOS / "afn_lambda.json")
    for w in SIGMA.sigma_estrela(6):
        esperado = "ba" not in w                       # a*b*
        assert afn.aceita(w) == esperado, w
    assert afn.simular("").caminho == ["q0", "q1"]     # aceita λ usando só a transição λ


@pytest.mark.parametrize("arquivo", ["afn_termina_ab.json", "afn_lambda.json"])
def test_conversao_para_afd_preserva_a_linguagem(arquivo):
    afn = AutomatoFinito.de_json(EXEMPLOS / arquivo)
    afd = afn.para_afd()
    assert afd.deterministico
    for w in SIGMA.sigma_estrela(7):
        assert afd.aceita(w) == afn.aceita(w), w


def test_caminho_e_sempre_valido():
    """Todo caminho devolvido usa apenas transições que existem em δ."""
    afn = AutomatoFinito.de_json(EXEMPLOS / "afn_lambda.json")
    for w in SIGMA.sigma_estrela(5):
        resultado = afn.simular(w)
        if not resultado.aceita:
            continue
        restante = w
        for origem, destino in zip(resultado.caminho, resultado.caminho[1:]):
            if restante and destino in afn.transicoes.get((origem, restante[0]), ()):
                restante = restante[1:]
            else:
                assert destino in afn.transicoes.get((origem, ""), ()), (w, resultado.caminho)
        assert restante == ""


def test_definicao_invalida():
    with pytest.raises(ValueError):
        AutomatoFinito(["q0"], ["a"], {}, "q9", [])
    with pytest.raises(ValueError):
        AutomatoFinito(["q0"], ["a"], {("q0", "b"): {"q0"}}, "q0", [])
