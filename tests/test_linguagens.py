import pytest

from simulador import Alfabeto, Linguagem


def test_exemplo_do_enunciado():
    sigma = Alfabeto.de_texto("{a,b}")
    assert sigma.valida("abba")
    assert sigma.tamanho("abba") == 4


def test_cadeia_invalida_indica_posicao():
    sigma = Alfabeto(["a", "b"])
    assert not sigma.valida("abca")
    assert sigma.simbolos_invalidos("abca") == [(2, "c")]


def test_cadeia_vazia_pertence_a_sigma_estrela():
    assert Alfabeto(["a"]).valida("")


def test_sigma_estrela_e_sigma_mais():
    sigma = Alfabeto(["a", "b"])
    assert list(sigma.sigma_estrela(2)) == ["", "a", "b", "aa", "ab", "ba", "bb"]
    assert list(sigma.sigma_mais(2)) == ["a", "b", "aa", "ab", "ba", "bb"]


def test_quantidade_de_cadeias_segue_a_formula():
    sigma = Alfabeto(["a", "b", "c"])
    m, k = 4, 3
    assert len(list(sigma.sigma_estrela(m))) == (k ** (m + 1) - 1) // (k - 1)


def test_concatenacao():
    assert Alfabeto.concatenar("ab", "ba") == "abba"
    assert Alfabeto.concatenar("ab", "") == "ab"      # λ é o elemento neutro


def test_alfabeto_vazio_ou_simbolo_longo_e_erro():
    with pytest.raises(ValueError):
        Alfabeto([])
    with pytest.raises(ValueError):
        Alfabeto(["ab"])


def test_linguagem_finita():
    sigma = Alfabeto(["a", "b"])
    linguagem = Linguagem(sigma, cadeias=["ab", "abba", "λ"])
    assert linguagem.pertence("abba") and linguagem.pertence("")
    assert not linguagem.pertence("ba")
    assert str(linguagem) == "{λ, ab, abba}"


def test_linguagem_por_expressao_regular():
    linguagem = Linguagem(Alfabeto(["a", "b"]), regex="(ab)*")
    assert linguagem.enumerar(4) == ["", "ab", "abab"]
    assert not linguagem.pertence("abc")              # fora de Σ nunca pertence


def test_linguagem_rejeita_cadeia_fora_do_alfabeto():
    with pytest.raises(ValueError):
        Linguagem(Alfabeto(["a"]), cadeias=["ab"])


def test_concatenacao_de_linguagens():
    sigma = Alfabeto(["a", "b"])
    l1, l2 = Linguagem(sigma, cadeias=["a", "ab"]), Linguagem(sigma, cadeias=["b", ""])
    assert l1.concatenar(l2).enumerar(3) == ["a", "ab", "abb"]
