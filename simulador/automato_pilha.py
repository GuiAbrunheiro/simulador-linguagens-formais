"""Módulo 4 - Simulador de Autômato com Pilha (AP).

Um AP é a 7-upla M = (Q, Σ, Γ, δ, q0, Z0, F). Cada transição tem a forma::

    δ(estado, leitura, topo) -> (novo_estado, empilha)

* ``leitura`` pode ser λ (não consome entrada);
* ``topo`` é o símbolo desempilhado (λ = não desempilha nada);
* ``empilha`` é a cadeia empilhada; o primeiro símbolo fica no topo.

O AP pode ser não determinístico, então a simulação faz uma **busca em
largura** no espaço de configurações (estado, posição na entrada, pilha).
"""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

LAMBDA = "λ"
VAZIOS = {"", "λ", "ε", "&", "lambda", "epsilon"}


class Pilha:
    """Pilha (LIFO) sobre uma lista do Python: o topo é o fim da lista."""

    def __init__(self, itens=()):
        self._itens: list[str] = list(itens)

    def empilhar(self, simbolo: str) -> None:
        self._itens.append(simbolo)                 # O(1) amortizado

    def desempilhar(self) -> str:
        if not self._itens:
            raise IndexError("Pilha vazia.")
        return self._itens.pop()                    # O(1)

    def topo(self) -> str | None:
        return self._itens[-1] if self._itens else None

    def vazia(self) -> bool:
        return not self._itens

    def copia(self) -> "Pilha":
        return Pilha(self._itens)

    def como_tupla(self) -> tuple[str, ...]:
        """Conteúdo da base para o topo (usado como chave de configuração)."""
        return tuple(self._itens)

    def __len__(self) -> int:
        return len(self._itens)

    def __str__(self) -> str:
        """Exibe com o topo à esquerda, como nos livros: ``AAZ``."""
        return "".join(reversed(self._itens)) or LAMBDA


@dataclass
class PassoAP:
    leitura: str                  # símbolo consumido ("λ" se nenhum)
    estado: str                   # estado depois do passo
    pilha: tuple[str, ...]        # base -> topo, depois do passo
    restante: str                 # entrada ainda não lida
    acao: str                     # descrição da transição aplicada

    def pilha_texto(self) -> str:
        return "".join(reversed(self.pilha)) or LAMBDA


@dataclass
class ResultadoAP:
    cadeia: str
    aceita: bool
    passos: list[PassoAP] = field(default_factory=list)
    configuracoes_exploradas: int = 0
    motivo: str = ""


class AutomatoPilha:
    def __init__(self, estados, alfabeto, alfabeto_pilha, transicoes, inicial,
                 simbolo_inicial_pilha, finais, aceitacao="estado_final", nome="AP"):
        """``transicoes``: lista de tuplas (estado, leitura, topo, novo_estado, empilha).

        ``aceitacao``: "estado_final", "pilha_vazia" ou "ambos".
        """
        self.nome = nome
        self.estados = list(estados)
        self.alfabeto = list(alfabeto)
        self.alfabeto_pilha = list(alfabeto_pilha)
        self.inicial = inicial
        self.simbolo_inicial_pilha = simbolo_inicial_pilha
        self.finais = set(finais)
        if aceitacao not in ("estado_final", "pilha_vazia", "ambos"):
            raise ValueError("Critério de aceitação inválido.")
        self.aceitacao = aceitacao
        # δ indexada por (estado, leitura, topo) -> lista de (novo_estado, empilha)
        self.transicoes: dict[tuple[str, str, str], list[tuple[str, tuple[str, ...]]]] = {}
        for estado, leitura, topo, novo, empilha in transicoes:
            if estado not in self.estados or novo not in self.estados:
                raise ValueError(f"Transição usa estado inexistente: {estado} -> {novo}")
            self.transicoes.setdefault((estado, leitura, topo), []).append((novo, tuple(empilha)))

    # ------------------------------------------------------------------ #
    # Construção
    # ------------------------------------------------------------------ #
    @classmethod
    def de_dict(cls, dados: dict) -> "AutomatoPilha":
        def limpar(valor: str) -> str:
            return "" if valor in VAZIOS else valor

        transicoes = [(t["de"], limpar(t["leitura"]), limpar(t["topo"]), t["para"],
                       tuple(limpar(t["empilha"])))
                      for t in dados["transicoes"]]
        return cls(dados["estados"], dados["alfabeto"], dados["alfabeto_pilha"], transicoes,
                   dados["inicial"], dados["simbolo_inicial_pilha"], dados["finais"],
                   dados.get("aceitacao", "estado_final"), dados.get("nome", "AP"))

    @classmethod
    def de_json(cls, caminho: str | Path) -> "AutomatoPilha":
        with open(caminho, encoding="utf-8") as arquivo:
            return cls.de_dict(json.load(arquivo))

    @classmethod
    def anbn(cls) -> "AutomatoPilha":
        """AP da linguagem mínima do projeto: L = { aⁿbⁿ | n ≥ 1 }."""
        return cls(
            estados=["q0", "q1", "qf"], alfabeto=["a", "b"], alfabeto_pilha=["A", "Z"],
            transicoes=[
                ("q0", "a", "Z", "q0", "AZ"),   # 1º a: empilha A sobre Z
                ("q0", "a", "A", "q0", "AA"),   # demais a: empilha mais um A
                ("q0", "b", "A", "q1", ""),     # 1º b: desempilha um A
                ("q1", "b", "A", "q1", ""),     # demais b: desempilha um A
                ("q1", "", "Z", "qf", "Z"),     # sobrou só Z: quantidades iguais
            ],
            inicial="q0", simbolo_inicial_pilha="Z", finais=["qf"],
            nome="AP para { aⁿbⁿ | n ≥ 1 }")

    # ------------------------------------------------------------------ #
    # Simulação
    # ------------------------------------------------------------------ #
    def _aceitou(self, estado: str, posicao: int, pilha: tuple, n: int) -> bool:
        if posicao != n:
            return False
        if self.aceitacao == "estado_final":
            return estado in self.finais
        if self.aceitacao == "pilha_vazia":
            return not pilha
        return estado in self.finais and not pilha

    def _sucessores(self, estado: str, posicao: int, pilha: tuple, cadeia: str):
        """Gera (leitura, novo_estado, nova_posicao, nova_pilha, ação) aplicáveis."""
        leituras = [""]
        if posicao < len(cadeia):
            leituras.append(cadeia[posicao])
        topos = [""]
        if pilha:
            topos.append(pilha[-1])
        for leitura in leituras:
            for topo in topos:
                for novo, empilha in self.transicoes.get((estado, leitura, topo), ()):
                    p = Pilha(pilha)
                    if topo:
                        p.desempilhar()
                    for simbolo in reversed(empilha):   # 1º símbolo termina no topo
                        p.empilhar(simbolo)
                    acao = (f"δ({estado}, {leitura or LAMBDA}, {topo or LAMBDA}) = "
                            f"({novo}, {''.join(empilha) or LAMBDA})")
                    yield (leitura, novo, posicao + len(leitura), p.como_tupla(), acao)

    def simular(self, cadeia: str, limite: int = 200_000) -> ResultadoAP:
        """Busca em largura por uma computação de aceitação.

        ``limite`` evita laço infinito em APs com ciclos de transições λ que
        só fazem a pilha crescer.
        """
        resultado = ResultadoAP(cadeia, False)
        invalidos = [c for c in cadeia if c not in self.alfabeto]
        if invalidos:
            resultado.motivo = f"O símbolo '{invalidos[0]}' não pertence a Σ."
            return resultado

        n = len(cadeia)
        inicio = (self.inicial, 0, (self.simbolo_inicial_pilha,))
        # pai[config] = (config anterior, leitura, ação) para reconstruir o caminho
        pai: dict[tuple, tuple | None] = {inicio: None}
        fila = deque([inicio])
        mais_longe = inicio          # configuração que consumiu mais entrada
        final = None

        while fila:
            config = fila.popleft()
            estado, posicao, pilha = config
            if posicao > mais_longe[1]:
                mais_longe = config
            if self._aceitou(estado, posicao, pilha, n):
                final = config
                break
            if len(pai) >= limite:
                resultado.motivo = f"Limite de {limite} configurações atingido."
                break
            for leitura, novo, nova_pos, nova_pilha, acao in self._sucessores(estado, posicao, pilha, cadeia):
                proxima = (novo, nova_pos, nova_pilha)
                if proxima not in pai:
                    pai[proxima] = (config, leitura, acao)
                    fila.append(proxima)

        resultado.configuracoes_exploradas = len(pai)
        resultado.aceita = final is not None
        resultado.passos = self._caminho(pai, final or mais_longe, cadeia)
        if resultado.aceita:
            resultado.motivo = "Entrada toda lida e critério de aceitação satisfeito."
        elif not resultado.motivo:
            ultimo = resultado.passos[-1]
            resultado.motivo = (f"Nenhuma computação aceita: o autômato trava em {ultimo.estado} "
                                f"com entrada restante '{ultimo.restante or LAMBDA}' "
                                f"e pilha {ultimo.pilha_texto()}.")
        return resultado

    def _caminho(self, pai: dict, config: tuple, cadeia: str) -> list[PassoAP]:
        passos = []
        while config is not None:
            estado, posicao, pilha = config
            anterior = pai[config]
            leitura, acao = (anterior[1], anterior[2]) if anterior else ("", "configuração inicial")
            passos.append(PassoAP(leitura or LAMBDA if anterior else "-", estado, pilha,
                                  cadeia[posicao:], acao))
            config = anterior[0] if anterior else None
        passos.reverse()
        return passos

    def aceita(self, cadeia: str) -> bool:
        return self.simular(cadeia).aceita

    # ------------------------------------------------------------------ #
    # Exibição
    # ------------------------------------------------------------------ #
    def tabela_transicoes(self) -> list[str]:
        linhas = []
        for (estado, leitura, topo), destinos in self.transicoes.items():
            for novo, empilha in destinos:
                linhas.append(f"δ({estado}, {leitura or LAMBDA}, {topo or LAMBDA}) = "
                              f"({novo}, {''.join(empilha) or LAMBDA})")
        return linhas

    def para_dot(self, ativo: str | None = None) -> str:
        linhas = ["digraph AP {", "  rankdir=LR;", '  bgcolor="transparent";',
                  '  node [fontname="Helvetica", style=filled, fillcolor="#FFFFFF", color="#444444"];',
                  '  edge [fontname="Helvetica", color="#444444"];',
                  '  __inicio [shape=point, width=0.1];']
        for estado in self.estados:
            forma = "doublecircle" if estado in self.finais else "circle"
            cor = "#FFC53D" if estado == ativo else "#FFFFFF"
            linhas.append(f'  "{estado}" [shape={forma}, fillcolor="{cor}"];')
        linhas.append(f'  __inicio -> "{self.inicial}";')
        rotulos: dict[tuple[str, str], list[str]] = {}
        for (estado, leitura, topo), destinos in self.transicoes.items():
            for novo, empilha in destinos:
                rotulo = f"{leitura or LAMBDA}, {topo or LAMBDA} / {''.join(empilha) or LAMBDA}"
                rotulos.setdefault((estado, novo), []).append(rotulo)
        for (origem, destino), lista in rotulos.items():
            texto = "\\n".join(lista)
            linhas.append(f'  "{origem}" -> "{destino}" [label=" {texto} "];')
        linhas.append("}")
        return "\n".join(linhas)
