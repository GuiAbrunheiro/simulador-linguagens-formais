"""Módulo 1 - Linguagens Formais.

Define as duas estruturas básicas da disciplina:

* ``Alfabeto``  -> conjunto finito e não vazio de símbolos (Σ);
* ``Linguagem`` -> conjunto de cadeias sobre Σ (L ⊆ Σ*).

Uma cadeia é representada por uma ``str`` do Python em que cada caractere
é um símbolo. A cadeia vazia (λ) é a string ``""``.
"""

from __future__ import annotations

import re
from itertools import product
from typing import Iterable, Iterator

LAMBDA = "λ"  # usado apenas para EXIBIR a cadeia vazia


def exibir(cadeia: str) -> str:
    """Devolve a cadeia pronta para impressão (λ no lugar da cadeia vazia)."""
    return cadeia if cadeia else LAMBDA


class Alfabeto:
    """Alfabeto Σ: conjunto finito e não vazio de símbolos de 1 caractere."""

    def __init__(self, simbolos: Iterable[str]):
        simbolos = list(simbolos)
        if not simbolos:
            raise ValueError("O alfabeto não pode ser vazio.")
        for s in simbolos:
            if len(s) != 1:
                raise ValueError(f"Símbolo inválido {s!r}: cada símbolo deve ter 1 caractere.")
        # sorted() garante que Σ* seja sempre gerado na mesma ordem
        self.simbolos: tuple[str, ...] = tuple(sorted(set(simbolos)))

    @classmethod
    def de_texto(cls, texto: str) -> "Alfabeto":
        """Cria o alfabeto a partir de um texto como ``"a,b"`` ou ``"{a, b}"``."""
        limpo = texto.replace("{", "").replace("}", "")
        return cls(p.strip() for p in limpo.split(",") if p.strip())

    # ------------------------------------------------------------------ #
    # Operações sobre cadeias
    # ------------------------------------------------------------------ #
    def simbolos_invalidos(self, cadeia: str) -> list[tuple[int, str]]:
        """Lista (posição, símbolo) de tudo que não pertence a Σ. Θ(n)."""
        conjunto = set(self.simbolos)
        return [(i, c) for i, c in enumerate(cadeia) if c not in conjunto]

    def valida(self, cadeia: str) -> bool:
        """True se todos os símbolos da cadeia pertencem a Σ (cadeia ∈ Σ*)."""
        conjunto = set(self.simbolos)
        return all(c in conjunto for c in cadeia)

    @staticmethod
    def tamanho(cadeia: str) -> int:
        """|w|: quantidade de símbolos da cadeia."""
        return len(cadeia)

    @staticmethod
    def concatenar(u: str, v: str) -> str:
        """Concatenação u·v."""
        return u + v

    # ------------------------------------------------------------------ #
    # Fechos
    # ------------------------------------------------------------------ #
    def sigma_estrela(self, tamanho_max: int) -> Iterator[str]:
        """Gera Σ* em ordem de tamanho (e lexicográfica) até ``tamanho_max``.

        Σ* é infinito, então o simulador enumera somente um prefixo dele.
        A quantidade de cadeias geradas é (k^(m+1) - 1)/(k - 1), k = |Σ|.
        """
        if tamanho_max < 0:
            raise ValueError("O tamanho máximo deve ser >= 0.")
        for n in range(tamanho_max + 1):
            for tupla in product(self.simbolos, repeat=n):
                yield "".join(tupla)

    def sigma_mais(self, tamanho_max: int) -> Iterator[str]:
        """Gera Σ+ = Σ* − {λ} até ``tamanho_max``."""
        for cadeia in self.sigma_estrela(tamanho_max):
            if cadeia:
                yield cadeia

    def __contains__(self, simbolo: str) -> bool:
        return simbolo in self.simbolos

    def __len__(self) -> int:
        return len(self.simbolos)

    def __str__(self) -> str:
        return "{" + ", ".join(self.simbolos) + "}"


class Linguagem:
    """Linguagem L ⊆ Σ*.

    Pode ser definida de duas formas:

    * por **enumeração** (conjunto finito de cadeias), ou
    * por **expressão regular** (linguagem possivelmente infinita).
    """

    def __init__(self, alfabeto: Alfabeto, cadeias: Iterable[str] | None = None,
                 regex: str | None = None, descricao: str = ""):
        if (cadeias is None) == (regex is None):
            raise ValueError("Informe as cadeias OU uma expressão regular.")
        self.alfabeto = alfabeto
        self.descricao = descricao
        self._cadeias: frozenset[str] | None = None
        self._regex: re.Pattern | None = None
        self.regex_texto = regex

        if cadeias is not None:
            cadeias = [c.replace(LAMBDA, "") for c in cadeias]
            for c in cadeias:
                if not alfabeto.valida(c):
                    raise ValueError(f"A cadeia {c!r} usa símbolos fora de Σ = {alfabeto}.")
            self._cadeias = frozenset(cadeias)
        else:
            self._regex = re.compile(regex)

    @property
    def finita(self) -> bool:
        return self._cadeias is not None

    def pertence(self, cadeia: str) -> bool:
        """Teste de pertinência w ∈ L."""
        if not self.alfabeto.valida(cadeia):
            return False
        if self._cadeias is not None:
            return cadeia in self._cadeias          # busca em hash: Θ(|w|)
        return self._regex.fullmatch(cadeia) is not None

    def enumerar(self, tamanho_max: int) -> list[str]:
        """Cadeias de L com tamanho até ``tamanho_max`` (filtra Σ*)."""
        return [w for w in self.alfabeto.sigma_estrela(tamanho_max) if self.pertence(w)]

    def concatenar(self, outra: "Linguagem") -> "Linguagem":
        """L1·L2 = { uv | u ∈ L1, v ∈ L2 } (somente linguagens finitas)."""
        if not (self.finita and outra.finita):
            raise ValueError("A concatenação só está disponível para linguagens finitas.")
        alfabeto = Alfabeto(self.alfabeto.simbolos + outra.alfabeto.simbolos)
        return Linguagem(alfabeto, cadeias={u + v for u in self._cadeias for v in outra._cadeias})

    def __str__(self) -> str:
        if self._cadeias is not None:
            ordenadas = sorted(self._cadeias, key=lambda c: (len(c), c))
            return "{" + ", ".join(exibir(c) for c in ordenadas) + "}"
        return f"L(/{self.regex_texto}/)"
