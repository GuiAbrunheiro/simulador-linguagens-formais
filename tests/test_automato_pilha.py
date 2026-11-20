from pathlib import Path

import pytest

from simulador import Alfabeto, AutomatoPilha, Pilha

EXEMPLOS = Path(__file__).resolve().parent.parent / "exemplos"
SIGMA = Alfabeto(["a", "b"])


def test_pilha_empilhar_e_desempilhar():
    pilha = Pilha()
    assert pilha.vazia()
    pilha.empilhar("Z")
    pilha.empilhar("A")
    assert pilha.topo() == "A" and len(pilha) == 2
    assert str(pilha) == "AZ"                           # topo à esquerda
    assert pilha.desempilhar() == "A"                   # LIFO
    assert pilha.desempilhar() == "Z"
    with pytest.raises(IndexError):
        pilha.desempilhar()


def test_anbn_contra_definicao():
    ap = AutomatoPilha.anbn()
    for w in SIGMA.sigma_estrela(9):
        n = len(w) // 2
        assert ap.aceita(w) == (n >= 1 and w == "a" * n + "b" * n), w


def test_passo_a_passo_mostra_leitura_estado_e_pilha():
    passos = AutomatoPilha.anbn().simular("aabb").passos
    assert [(p.leitura, p.estado, p.pilha_texto()) for p in passos] == [
        ("-", "q0", "Z"),
        ("a", "q0", "AZ"),
        ("a", "q0", "AAZ"),
        ("b", "q1", "AZ"),
        ("b", "q1", "Z"),
        ("λ", "qf", "Z"),
    ]


def test_cadeia_vazia_e_rejeitada_pois_n_maior_igual_a_1():
    assert not AutomatoPilha.anbn().aceita("")


def test_rejeicao_explica_onde_travou():
    resultado = AutomatoPilha.anbn().simular("aab")
    assert not resultado.aceita
    assert "trava em q1" in resultado.motivo


def test_json_equivale_ao_automato_embutido():
    ap = AutomatoPilha.de_json(EXEMPLOS / "ap_anbn.json")
    embutido = AutomatoPilha.anbn()
    for w in SIGMA.sigma_estrela(7):
        assert ap.aceita(w) == embutido.aceita(w), w


def test_ap_nao_deterministico_palindromos_pares():
    ap = AutomatoPilha.de_json(EXEMPLOS / "ap_palindromos_pares.json")
    for w in SIGMA.sigma_estrela(8):
        assert ap.aceita(w) == (len(w) % 2 == 0 and w == w[::-1]), w


def test_aceitacao_por_pilha_vazia():
    ap = AutomatoPilha(["q"], ["a", "b"], ["A", "Z"],
                       [("q", "a", "Z", "q", "A"), ("q", "a", "A", "q", "AA"), ("q", "b", "A", "q", "")],
                       "q", "Z", [], aceitacao="pilha_vazia")
    assert ap.aceita("aabb") and ap.aceita("ab")
    assert not ap.aceita("aab") and not ap.aceita("")


def test_limite_evita_laco_infinito():
    # transição λ que só empilha: sem o limite a busca nunca terminaria
    ap = AutomatoPilha(["q"], ["a"], ["Z"], [("q", "", "", "q", "Z")], "q", "Z", [])
    resultado = ap.simular("a", limite=500)
    assert not resultado.aceita
    assert "Limite" in resultado.motivo
