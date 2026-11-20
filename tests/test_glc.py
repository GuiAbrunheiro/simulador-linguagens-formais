from pathlib import Path

import pytest

from simulador import Alfabeto, Gramatica
from simulador.glc import LAMBDA

EXEMPLOS = Path(__file__).resolve().parent.parent / "exemplos"
SIGMA = Alfabeto(["a", "b"])


def test_exemplo_do_enunciado():
    g = Gramatica.de_texto("S -> aSb\nS -> λ")
    resultado = g.reconhecer("aaabbb")
    assert resultado.aceita
    assert resultado.derivacao_texto() == "S ⇒ aSb ⇒ aaSbb ⇒ aaaSbbb ⇒ aaabbb"


def test_anbn_contra_definicao():
    g = Gramatica.de_json(EXEMPLOS / "glc_anbn.json")
    for w in SIGMA.sigma_estrela(8):
        n = len(w) // 2
        assert g.aceita(w) == (w == "a" * n + "b" * n), w


def test_palindromos_contra_definicao():
    g = Gramatica.de_json(EXEMPLOS / "glc_palindromos.json")
    for w in SIGMA.sigma_estrela(8):
        assert g.aceita(w) == (w == w[::-1]), w


def test_cadeia_vazia():
    g = Gramatica.de_texto("S -> aSb | λ")
    resultado = g.reconhecer("")
    assert resultado.aceita
    assert resultado.derivacao_texto() == f"S ⇒ {LAMBDA}"


def test_recursao_a_esquerda_e_precedencia():
    g = Gramatica.de_json(EXEMPLOS / "glc_expressoes.json")
    resultado = g.reconhecer("x+x*x")
    assert resultado.aceita
    # a multiplicação fica mais funda na árvore que a soma
    assert resultado.derivacao[1].forma == "E+T"
    assert not g.aceita("x+*x")
    assert not g.aceita("(x")


def test_arvore_gera_exatamente_a_cadeia():
    g = Gramatica.de_json(EXEMPLOS / "glc_expressoes.json")
    for w in ["x", "x+x", "(x+x)*x", "x*(x+(x))"]:
        assert g.reconhecer(w).arvore.fronteira() == w


def test_derivacao_aplica_apenas_producoes_da_gramatica():
    g = Gramatica.de_json(EXEMPLOS / "glc_palindromos.json")
    derivacao = g.reconhecer("abbba").derivacao
    regras = {f"{v} -> {''.join(lado) or LAMBDA}" for v, lados in g.producoes.items() for lado in lados}
    assert all(p.producao in regras for p in derivacao[1:])
    assert derivacao[-1].forma == "abbba"


def test_gramatica_ambigua_com_ciclos_e_lambda():
    """Caso difícil: S -> SS, produções unitárias em ciclo (A -> B -> A) e λ."""
    g = Gramatica.de_texto("S -> SS | A | λ\nA -> aA | B\nB -> A | b | λ")
    for w in SIGMA.sigma_estrela(5):
        resultado = g.reconhecer(w)
        assert resultado.aceita, w                     # a gramática gera {a,b}*
        assert resultado.arvore.fronteira() == w
        assert resultado.derivacao[-1].forma == (w or LAMBDA)
    assert not g.aceita("abc")


def test_variavel_anulavel_no_meio_da_producao():
    g = Gramatica.de_texto("S -> aBc\nB -> b | λ")
    assert g.aceita("abc") and g.aceita("ac")
    assert not g.aceita("abbc")


def test_arvore_em_texto():
    g = Gramatica.de_texto("S -> aSb | λ")
    linhas = Gramatica.arvore_texto(g.reconhecer("ab").arvore)
    assert linhas == ["S", "├── a", "├── S", "│   └── λ", "└── b"]


def test_definicao_invalida():
    with pytest.raises(ValueError):
        Gramatica(["S"], ["a"], {"S": ["aX"]}, "S")     # X não é símbolo conhecido
    with pytest.raises(ValueError):
        Gramatica(["S"], ["a"], {"S": ["a"]}, "T")      # inicial fora de V
