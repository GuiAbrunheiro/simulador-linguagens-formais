from itertools import product
from pathlib import Path

import pytest

from simulador import MaquinaTuring

EXEMPLOS = Path(__file__).resolve().parent.parent / "exemplos"


def pertence_w_hash_w(cadeia: str) -> bool:
    partes = cadeia.split("#")
    return len(partes) == 2 and partes[0] == partes[1]


# ----------------------------- Opção A --------------------------------- #
def test_opcao_a_exemplos():
    mt = MaquinaTuring.w_hash_w()
    for w in ["#", "a#a", "ab#ab", "abba#abba"]:
        assert mt.aceita(w), w
    for w in ["", "a", "ab", "a#b", "ab#ba", "ab#a", "a#ab", "a##a", "#a"]:
        assert not mt.aceita(w), w


def test_opcao_a_contra_definicao_em_todas_as_cadeias_curtas():
    mt = MaquinaTuring.w_hash_w()
    for n in range(8):
        for letras in product("ab#", repeat=n):
            w = "".join(letras)
            assert mt.aceita(w) == pertence_w_hash_w(w), w


@pytest.mark.parametrize("m", [0, 1, 2, 5, 10, 20])
def test_opcao_a_numero_de_passos_e_quadratico(m):
    resultado = MaquinaTuring.w_hash_w().executar("a" * m + "#" + "a" * m)
    assert resultado.total_passos == 2 * (m + 1) ** 2


# ----------------------------- Opção B --------------------------------- #
def test_opcao_b_exemplo_do_enunciado():
    resultado = MaquinaTuring.soma_unaria().executar("000100")     # 3 + 2
    assert resultado.aceita
    assert resultado.saida == "00000"


def test_opcao_b_todas_as_somas_pequenas():
    mt = MaquinaTuring.soma_unaria()
    for m in range(7):
        for n in range(7):
            resultado = mt.executar("0" * m + "1" + "0" * n)
            assert resultado.aceita
            assert resultado.saida == "0" * (m + n), (m, n)
            assert resultado.total_passos == 2 * (m + n + 1) + 2    # linear


def test_opcao_b_rejeita_entrada_sem_separador():
    assert not MaquinaTuring.soma_unaria().aceita("000")
    assert not MaquinaTuring.soma_unaria().aceita("0101")


# ----------------------------- Geral ----------------------------------- #
def test_passo_a_passo_registra_fita_e_cabeca():
    resultado = MaquinaTuring.soma_unaria().executar("010")
    primeiro, ultimo = resultado.passos[0], resultado.passos[-1]
    assert primeiro.estado == "q0" and primeiro.cabeca == 0
    assert primeiro.fita == {0: "0", 1: "1", 2: "0"}
    assert ultimo.estado == "qaceita"
    assert len(resultado.passos) == resultado.total_passos + 1
    assert "[0]" in primeiro.fita_texto()


def test_simbolo_fora_do_alfabeto():
    resultado = MaquinaTuring.w_hash_w().executar("a#c")
    assert not resultado.aceita
    assert "não pertence" in resultado.motivo


def test_limite_de_passos_detecta_laco():
    mt = MaquinaTuring(["q", "ok"], ["a"], ["a", "_"], {("q", "a"): ("q", "a", "P")}, "q", "ok")
    resultado = mt.executar("a", limite=50)
    assert not resultado.parou and not resultado.aceita
    assert resultado.total_passos == 50


@pytest.mark.parametrize("arquivo,embutida", [("mt_w_hash_w.json", MaquinaTuring.w_hash_w),
                                               ("mt_soma_unaria.json", MaquinaTuring.soma_unaria)])
def test_json_equivale_a_maquina_embutida(arquivo, embutida):
    assert MaquinaTuring.de_json(EXEMPLOS / arquivo).transicoes == embutida().transicoes


def test_movimento_invalido():
    with pytest.raises(ValueError):
        MaquinaTuring(["q"], ["a"], ["a"], {("q", "a"): ("q", "a", "X")}, "q", "q")
