"""Módulo 2 - Simulador de Autômato Finito (AFD e AFN, com ou sem λ).

Um autômato finito é a 5-upla M = (Q, Σ, δ, q0, F). Aqui a função de
transição é guardada em um dicionário::

    transicoes[(estado, simbolo)] -> conjunto de estados de destino

* Em um **AFD** cada conjunto tem exatamente 0 ou 1 estado.
* Em um **AFN** o conjunto pode ter vários estados, e o símbolo pode ser a
  cadeia vazia (transição λ), representada internamente por ``""``.

A mesma classe simula os dois modelos: ela acompanha o *conjunto* de
estados ativos (para um AFD esse conjunto sempre tem 1 elemento).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

VAZIOS = {"", "λ", "ε", "&", "lambda", "epsilon"}  # formas aceitas para λ no JSON


@dataclass
class PassoAF:
    """Um passo da simulação: leitura de um símbolo."""
    indice: int
    simbolo: str
    origem: frozenset[str]     # estados ativos antes da leitura
    destino: frozenset[str]    # estados ativos depois (já com fecho-λ)


@dataclass
class ResultadoAF:
    cadeia: str
    aceita: bool
    passos: list[PassoAF]
    estados_iniciais: frozenset[str]
    caminho: list[str] = field(default_factory=list)  # um caminho q0 -> ... -> qn
    motivo: str = ""

    def caminho_texto(self) -> str:
        return " -> ".join(self.caminho)


class AutomatoFinito:
    def __init__(self, estados, alfabeto, transicoes, inicial, finais, nome="Autômato"):
        self.nome = nome
        self.estados: list[str] = list(estados)
        self.alfabeto: list[str] = list(alfabeto)
        self.inicial: str = inicial
        self.finais: set[str] = set(finais)
        self.transicoes: dict[tuple[str, str], set[str]] = {}
        for (origem, simbolo), destinos in transicoes.items():
            self.transicoes.setdefault((origem, simbolo), set()).update(destinos)
        self._validar()

    # ------------------------------------------------------------------ #
    # Construção
    # ------------------------------------------------------------------ #
    def _validar(self) -> None:
        conjunto = set(self.estados)
        if self.inicial not in conjunto:
            raise ValueError(f"Estado inicial {self.inicial!r} não está em Q.")
        fora = self.finais - conjunto
        if fora:
            raise ValueError(f"Estados finais fora de Q: {sorted(fora)}")
        for (origem, simbolo), destinos in self.transicoes.items():
            if origem not in conjunto or not destinos <= conjunto:
                raise ValueError(f"Transição usa estado inexistente: δ({origem}, {simbolo or 'λ'})")
            if simbolo and simbolo not in self.alfabeto:
                raise ValueError(f"Símbolo {simbolo!r} da transição não pertence a Σ.")

    @classmethod
    def de_dict(cls, dados: dict) -> "AutomatoFinito":
        """Monta o autômato a partir do dicionário lido do JSON."""
        transicoes: dict[tuple[str, str], set[str]] = {}
        for t in dados["transicoes"]:
            simbolo = "" if t["simbolo"] in VAZIOS else t["simbolo"]
            destinos = t["para"] if isinstance(t["para"], list) else [t["para"]]
            transicoes.setdefault((t["de"], simbolo), set()).update(destinos)
        return cls(dados["estados"], dados["alfabeto"], transicoes,
                   dados["inicial"], dados["finais"], dados.get("nome", "Autômato"))

    @classmethod
    def de_json(cls, caminho: str | Path) -> "AutomatoFinito":
        with open(caminho, encoding="utf-8") as arquivo:
            return cls.de_dict(json.load(arquivo))

    # ------------------------------------------------------------------ #
    # Propriedades
    # ------------------------------------------------------------------ #
    @property
    def deterministico(self) -> bool:
        """AFD: sem transições λ e no máximo um destino por (estado, símbolo)."""
        return all(simbolo != "" and len(destinos) <= 1
                   for (_, simbolo), destinos in self.transicoes.items())

    @property
    def tipo(self) -> str:
        return "AFD" if self.deterministico else "AFN"

    def fecho_lambda(self, estados) -> frozenset[str]:
        """Todos os estados alcançáveis usando apenas transições λ (busca em profundidade)."""
        fecho = set(estados)
        pilha = list(estados)
        while pilha:
            atual = pilha.pop()
            for proximo in self.transicoes.get((atual, ""), ()):
                if proximo not in fecho:
                    fecho.add(proximo)
                    pilha.append(proximo)
        return frozenset(fecho)

    def mover(self, estados, simbolo: str) -> frozenset[str]:
        """δ estendida para conjuntos: une os destinos de cada estado ativo."""
        destino: set[str] = set()
        for estado in estados:
            destino |= self.transicoes.get((estado, simbolo), set())
        return frozenset(destino)

    # ------------------------------------------------------------------ #
    # Simulação
    # ------------------------------------------------------------------ #
    def simular(self, cadeia: str) -> ResultadoAF:
        """Executa a cadeia e registra o passo a passo.

        Custo: Θ(n) para AFD e O(n · |Q|²) para AFN, com n = |cadeia|.
        """
        atuais = self.fecho_lambda({self.inicial})
        resultado = ResultadoAF(cadeia, False, [], atuais)
        historico = [atuais]

        for i, simbolo in enumerate(cadeia):
            if simbolo not in self.alfabeto:
                resultado.motivo = f"O símbolo '{simbolo}' (posição {i + 1}) não pertence a Σ."
                resultado.caminho = self._reconstruir(historico, cadeia[:i], None)
                return resultado
            proximos = self.fecho_lambda(self.mover(atuais, simbolo))
            resultado.passos.append(PassoAF(i, simbolo, atuais, proximos))
            historico.append(proximos)
            if not proximos:  # autômato "travou": não há transição definida
                resultado.motivo = (f"Não há transição para '{simbolo}' a partir de "
                                    f"{formatar_conjunto(atuais)}.")
                resultado.caminho = self._reconstruir(historico[:-1], cadeia[:i], None)
                return resultado
            atuais = proximos

        finais_atingidos = atuais & self.finais
        resultado.aceita = bool(finais_atingidos)
        alvo = sorted(finais_atingidos)[0] if finais_atingidos else None
        resultado.caminho = self._reconstruir(historico, cadeia, alvo)
        resultado.motivo = ("A leitura terminou em estado final." if resultado.aceita else
                            f"A leitura terminou em {formatar_conjunto(atuais)}, que não é final.")
        return resultado

    def _reconstruir(self, historico, cadeia: str, alvo: str | None) -> list[str]:
        """Recupera UM caminho concreto (de trás para frente) para exibição.

        ``historico[i]`` é o conjunto de estados ativos após ler i símbolos.
        Em um AFD o caminho é único; em um AFN escolhe-se um dos possíveis.
        """
        if alvo is None:
            alvo = sorted(historico[-1])[0]
        caminho = [alvo]
        for i in range(len(cadeia), 0, -1):
            simbolo = cadeia[i - 1]
            # estados em que o autômato "entra" ao ler o símbolo, antes das λ
            entradas = self.mover(historico[i - 1], simbolo)
            caminho = self._caminho_lambda(entradas, caminho[0]) + caminho[1:]
            anterior = next(e for e in sorted(historico[i - 1])
                            if caminho[0] in self.transicoes.get((e, simbolo), ()))
            caminho.insert(0, anterior)
        return self._caminho_lambda({self.inicial}, caminho[0]) + caminho[1:]

    def _caminho_lambda(self, entradas, alvo: str) -> list[str]:
        """Menor caminho só com transições λ de alguma entrada até ``alvo`` (busca em largura)."""
        anterior_de: dict[str, str | None] = {e: None for e in entradas}
        fila = sorted(entradas)
        while fila and alvo not in anterior_de:
            atual = fila.pop(0)
            for proximo in sorted(self.transicoes.get((atual, ""), ())):
                if proximo not in anterior_de:
                    anterior_de[proximo] = atual
                    fila.append(proximo)
        trecho = [alvo]
        while anterior_de[trecho[0]] is not None:
            trecho.insert(0, anterior_de[trecho[0]])
        return trecho

    def aceita(self, cadeia: str) -> bool:
        return self.simular(cadeia).aceita

    # ------------------------------------------------------------------ #
    # Conversão AFN -> AFD (construção de subconjuntos)
    # ------------------------------------------------------------------ #
    def para_afd(self) -> "AutomatoFinito":
        """Constrói o AFD equivalente. Pior caso: O(2^|Q| · |Σ|) estados/transições."""
        inicial = self.fecho_lambda({self.inicial})
        nomes = {inicial: formatar_conjunto(inicial)}
        fila = [inicial]
        transicoes: dict[tuple[str, str], set[str]] = {}
        while fila:
            conjunto = fila.pop(0)
            for simbolo in self.alfabeto:
                destino = self.fecho_lambda(self.mover(conjunto, simbolo))
                if not destino:
                    continue
                if destino not in nomes:
                    nomes[destino] = formatar_conjunto(destino)
                    fila.append(destino)
                transicoes[(nomes[conjunto], simbolo)] = {nomes[destino]}
        finais = [nome for conjunto, nome in nomes.items() if conjunto & self.finais]
        return AutomatoFinito(list(nomes.values()), self.alfabeto, transicoes,
                              nomes[inicial], finais, f"AFD equivalente a {self.nome}")

    # ------------------------------------------------------------------ #
    # Exibição
    # ------------------------------------------------------------------ #
    def tabela_transicoes(self) -> list[str]:
        linhas = []
        for (origem, simbolo), destinos in sorted(self.transicoes.items()):
            for destino in sorted(destinos):
                linhas.append(f"{origem} --{simbolo or 'λ'}--> {destino}")
        return linhas

    def para_dot(self, ativos=(), visitados=()) -> str:
        """Gera o diagrama de estados em Graphviz DOT, destacando os estados ativos."""
        ativos, visitados = set(ativos), set(visitados)
        linhas = ["digraph AF {", "  rankdir=LR;", '  bgcolor="transparent";',
                  '  node [fontname="Helvetica", style=filled, fillcolor="#FFFFFF", color="#444444"];',
                  '  edge [fontname="Helvetica", color="#444444"];',
                  '  __inicio [shape=point, width=0.1, color="#444444"];']
        for estado in self.estados:
            forma = "doublecircle" if estado in self.finais else "circle"
            cor = "#FFC53D" if estado in ativos else ("#D9ECEF" if estado in visitados else "#FFFFFF")
            largura = 2.5 if estado in ativos else 1.2
            linhas.append(f'  "{estado}" [shape={forma}, fillcolor="{cor}", penwidth={largura}];')
        linhas.append(f'  __inicio -> "{self.inicial}";')
        rotulos: dict[tuple[str, str], list[str]] = {}
        for (origem, simbolo), destinos in sorted(self.transicoes.items()):
            for destino in sorted(destinos):
                rotulos.setdefault((origem, destino), []).append(simbolo or "λ")
        for (origem, destino), simbolos in rotulos.items():
            linhas.append(f'  "{origem}" -> "{destino}" [label=" {", ".join(simbolos)} "];')
        linhas.append("}")
        return "\n".join(linhas)


def formatar_conjunto(estados) -> str:
    return "{" + ", ".join(sorted(estados)) + "}" if estados else "∅"
