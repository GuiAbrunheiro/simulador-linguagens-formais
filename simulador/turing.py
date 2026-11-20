"""Módulo 5 - Máquina de Turing (MT) determinística de fita única.

M = (Q, Σ, Γ, δ, q0, q_aceita, q_rejeita), com

    δ(estado, símbolo lido) -> (novo estado, símbolo escrito, movimento)

Movimentos: ``D`` (direita), ``E`` (esquerda) e ``P`` (parado).
A fita é infinita nos dois sentidos e guardada em um dicionário
``posição -> símbolo`` (só as células não brancas ocupam memória).

O módulo traz prontas as duas máquinas pedidas no projeto:

* **Opção A** - ``MaquinaTuring.w_hash_w()``: reconhece L = { w#w | w ∈ {a,b}* };
* **Opção B** - ``MaquinaTuring.soma_unaria()``: soma dois números em unário.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

BRANCO = "_"
MOVIMENTOS = {"D": 1, "R": 1, "E": -1, "L": -1, "P": 0, "S": 0}


@dataclass
class PassoMT:
    numero: int
    estado: str
    fita: dict[int, str]          # cópia da fita neste instante
    cabeca: int
    acao: str = ""                # transição que LEVOU a esta configuração

    def janela(self, margem: int = 1) -> tuple[int, int]:
        """Intervalo [início, fim] que cobre o conteúdo e a cabeça."""
        posicoes = list(self.fita) + [self.cabeca]
        return min(posicoes) - margem, max(posicoes) + margem

    def fita_texto(self) -> str:
        """Fita em uma linha, com a célula sob a cabeça entre colchetes."""
        inicio, fim = self.janela()
        return "".join(f"[{self.fita.get(i, BRANCO)}]" if i == self.cabeca
                       else f" {self.fita.get(i, BRANCO)} " for i in range(inicio, fim + 1))


@dataclass
class ResultadoMT:
    entrada: str
    aceita: bool
    parou: bool                   # False se estourou o limite de passos
    passos: list[PassoMT] = field(default_factory=list)
    saida: str = ""               # conteúdo final da fita, sem brancos nas pontas
    total_passos: int = 0         # quantidade de transições executadas
    motivo: str = ""


class MaquinaTuring:
    def __init__(self, estados, alfabeto, alfabeto_fita, transicoes, inicial,
                 aceitacao, rejeicao=None, branco=BRANCO, nome="Máquina de Turing",
                 descricao=""):
        """``transicoes``: dict {(estado, símbolo): (novo_estado, escreve, movimento)}."""
        self.nome = nome
        self.descricao = descricao
        self.estados = list(estados)
        self.alfabeto = list(alfabeto)
        self.alfabeto_fita = list(alfabeto_fita)
        self.inicial = inicial
        self.aceitacao = aceitacao
        self.rejeicao = rejeicao
        self.branco = branco
        self.transicoes: dict[tuple[str, str], tuple[str, str, str]] = {}
        for (estado, simbolo), (novo, escreve, movimento) in transicoes.items():
            movimento = movimento.upper()
            if movimento not in MOVIMENTOS:
                raise ValueError(f"Movimento inválido: {movimento!r} (use E, D ou P).")
            if estado not in self.estados or novo not in self.estados:
                raise ValueError(f"Transição usa estado inexistente: {estado} -> {novo}")
            self.transicoes[(estado, simbolo)] = (novo, escreve, movimento)

    # ------------------------------------------------------------------ #
    # Construção
    # ------------------------------------------------------------------ #
    @classmethod
    def de_dict(cls, dados: dict) -> "MaquinaTuring":
        transicoes = {(t["de"], t["le"]): (t["para"], t["escreve"], t["move"])
                      for t in dados["transicoes"]}
        return cls(dados["estados"], dados["alfabeto"], dados["alfabeto_fita"], transicoes,
                   dados["inicial"], dados["aceitacao"], dados.get("rejeicao"),
                   dados.get("branco", BRANCO), dados.get("nome", "Máquina de Turing"),
                   dados.get("descricao", ""))

    @classmethod
    def de_json(cls, caminho: str | Path) -> "MaquinaTuring":
        with open(caminho, encoding="utf-8") as arquivo:
            return cls.de_dict(json.load(arquivo))

    @classmethod
    def w_hash_w(cls) -> "MaquinaTuring":
        """Opção A: reconhece L = { w#w | w ∈ {a,b}* }.

        Ideia: marca com X o primeiro símbolo não marcado à esquerda do #,
        guarda-o no estado (qa ou qb), atravessa o # e confere se o primeiro
        símbolo não marcado à direita é igual. Repete até acabar o lado
        esquerdo; no fim o lado direito também precisa estar todo marcado.
        """
        t: dict[tuple[str, str], tuple[str, str, str]] = {
            # q0: escolhe o próximo símbolo do lado esquerdo
            ("q0", "a"): ("qa", "X", "D"),
            ("q0", "b"): ("qb", "X", "D"),
            ("q0", "#"): ("qfim", "#", "D"),
            # qfim: lado esquerdo acabou; à direita só pode haver X
            ("qfim", "X"): ("qfim", "X", "D"),
            ("qfim", BRANCO): ("qaceita", BRANCO, "P"),
            # qvolta / qvolta2: retorna ao primeiro símbolo não marcado da esquerda
            ("qvolta", "X"): ("qvolta", "X", "E"),
            ("qvolta", "#"): ("qvolta2", "#", "E"),
            ("qvolta2", "a"): ("qvolta2", "a", "E"),
            ("qvolta2", "b"): ("qvolta2", "b", "E"),
            ("qvolta2", "X"): ("q0", "X", "D"),
        }
        for letra in "ab":
            ida, confere = f"q{letra}", f"q{letra}2"
            t[(ida, "a")] = (ida, "a", "D")           # anda até o #
            t[(ida, "b")] = (ida, "b", "D")
            t[(ida, "#")] = (confere, "#", "D")
            t[(confere, "X")] = (confere, "X", "D")   # pula os já conferidos
            t[(confere, letra)] = ("qvolta", "X", "E")  # igual: marca e volta
        return cls(
            estados=["q0", "qa", "qb", "qa2", "qb2", "qvolta", "qvolta2", "qfim",
                     "qaceita", "qrejeita"],
            alfabeto=["a", "b", "#"], alfabeto_fita=["a", "b", "#", "X", BRANCO],
            transicoes=t, inicial="q0", aceitacao="qaceita", rejeicao="qrejeita",
            nome="MT Opção A: L = { w#w }",
            descricao="Reconhece cadeias formadas por duas cópias de w separadas por #.")

    @classmethod
    def soma_unaria(cls) -> "MaquinaTuring":
        """Opção B: soma em unário. Entrada ``0^m 1 0^n``; saída ``0^(m+n)``.

        Ideia: troca o separador 1 por 0 (ficam m+n+1 zeros) e apaga o
        último zero da fita.
        """
        t = {
            ("q0", "0"): ("q0", "0", "D"),            # percorre a 1ª parcela
            ("q0", "1"): ("q1", "0", "D"),            # separador vira 0
            ("q1", "0"): ("q1", "0", "D"),            # percorre a 2ª parcela
            ("q1", BRANCO): ("q2", BRANCO, "E"),      # fim da entrada: volta 1
            ("q2", "0"): ("q3", BRANCO, "E"),         # apaga o zero excedente
            ("q3", "0"): ("q3", "0", "E"),            # rebobina a cabeça
            ("q3", BRANCO): ("qaceita", BRANCO, "D"),
        }
        return cls(
            estados=["q0", "q1", "q2", "q3", "qaceita", "qrejeita"],
            alfabeto=["0", "1"], alfabeto_fita=["0", "1", BRANCO],
            transicoes=t, inicial="q0", aceitacao="qaceita", rejeicao="qrejeita",
            nome="MT Opção B: soma em unário",
            descricao="Entrada 0^m 1 0^n (m + n). Resultado na fita: 0^(m+n).")

    # ------------------------------------------------------------------ #
    # Simulação
    # ------------------------------------------------------------------ #
    def executar(self, entrada: str, limite: int = 100_000, guardar_passos: bool = True) -> ResultadoMT:
        """Executa a máquina até parar (ou até ``limite`` passos).

        A máquina para quando entra em q_aceita/q_rejeita ou quando não há
        transição definida para (estado, símbolo) - o que conta como rejeição.
        """
        resultado = ResultadoMT(entrada, False, False)
        invalidos = [c for c in entrada if c not in self.alfabeto]
        if invalidos:
            resultado.parou = True
            resultado.motivo = f"O símbolo '{invalidos[0]}' não pertence ao alfabeto de entrada."
            resultado.passos = [PassoMT(0, self.inicial, dict(enumerate(entrada)), 0, "configuração inicial")]
            resultado.saida = entrada
            return resultado

        fita: dict[int, str] = dict(enumerate(entrada))
        estado, cabeca, numero = self.inicial, 0, 0
        resultado.passos.append(PassoMT(0, estado, dict(fita), cabeca, "configuração inicial"))

        while estado not in (self.aceitacao, self.rejeicao):
            if numero >= limite:
                resultado.motivo = f"Limite de {limite} passos atingido (possível laço infinito)."
                break
            lido = fita.get(cabeca, self.branco)
            transicao = self.transicoes.get((estado, lido))
            if transicao is None:
                resultado.parou = True
                resultado.motivo = f"Sem transição para δ({estado}, {lido}): a máquina para e rejeita."
                break
            novo, escreve, movimento = transicao
            if escreve == self.branco:
                fita.pop(cabeca, None)               # branco não ocupa memória
            else:
                fita[cabeca] = escreve
            cabeca += MOVIMENTOS[movimento]
            numero += 1
            if guardar_passos:                       # desligado nas medições de desempenho
                resultado.passos.append(PassoMT(
                    numero, novo, dict(fita), cabeca,
                    f"δ({estado}, {lido}) = ({novo}, {escreve}, {movimento})"))
            estado = novo
        else:
            resultado.parou = True
            resultado.aceita = estado == self.aceitacao
            resultado.motivo = ("A máquina parou no estado de aceitação." if resultado.aceita
                                else "A máquina parou no estado de rejeição.")

        resultado.total_passos = numero
        resultado.saida = self._conteudo(fita)
        return resultado

    def _conteudo(self, fita: dict[int, str]) -> str:
        if not fita:
            return ""
        return "".join(fita.get(i, self.branco) for i in range(min(fita), max(fita) + 1))

    def aceita(self, entrada: str) -> bool:
        return self.executar(entrada).aceita

    # ------------------------------------------------------------------ #
    # Exibição
    # ------------------------------------------------------------------ #
    def tabela_transicoes(self) -> list[str]:
        return [f"δ({e}, {s}) = ({n}, {w}, {m})"
                for (e, s), (n, w, m) in self.transicoes.items()]

    def para_dot(self, ativo: str | None = None) -> str:
        linhas = ["digraph MT {", "  rankdir=LR;", '  bgcolor="transparent";',
                  '  node [fontname="Helvetica", style=filled, fillcolor="#FFFFFF", color="#444444"];',
                  '  edge [fontname="Helvetica", color="#444444"];',
                  '  __inicio [shape=point, width=0.1];']
        usados = {self.inicial, self.aceitacao}
        for (e, _), (n, _, _) in self.transicoes.items():
            usados |= {e, n}
        if ativo:
            usados.add(ativo)
        for estado in self.estados:
            if estado not in usados:
                continue
            forma = "doublecircle" if estado == self.aceitacao else "circle"
            cor = "#FFC53D" if estado == ativo else "#FFFFFF"
            linhas.append(f'  "{estado}" [shape={forma}, fillcolor="{cor}"];')
        linhas.append(f'  __inicio -> "{self.inicial}";')
        rotulos: dict[tuple[str, str], list[str]] = {}
        for (e, s), (n, w, m) in self.transicoes.items():
            rotulos.setdefault((e, n), []).append(f"{s} → {w}, {m}")
        for (origem, destino), lista in rotulos.items():
            texto = "\\n".join(lista)
            linhas.append(f'  "{origem}" -> "{destino}" [label=" {texto} "];')
        linhas.append("}")
        return "\n".join(linhas)
