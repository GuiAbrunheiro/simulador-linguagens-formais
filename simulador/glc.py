"""Módulo 3 - Simulador de Gramática Livre de Contexto (GLC).

Uma GLC é a 4-upla G = (V, T, P, S). O reconhecimento usa o **algoritmo de
Earley**, que funciona para qualquer GLC (com recursão à esquerda,
ambiguidade e produções λ), sem exigir conversão para a Forma Normal de
Chomsky. A partir da tabela de Earley o simulador monta a **árvore de
derivação** e, percorrendo a árvore, a **derivação mais à esquerda** passo
a passo.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

LAMBDA = "λ"
VAZIOS = {"", "λ", "ε", "&", "lambda", "epsilon"}


@dataclass
class No:
    """Nó da árvore de derivação. Folhas são terminais ou λ."""
    simbolo: str
    filhos: list["No"] = field(default_factory=list)
    producao: tuple[str, ...] | None = None   # lado direito usado (só em variáveis)

    def fronteira(self) -> str:
        """Concatenação das folhas = cadeia gerada pela subárvore."""
        if not self.filhos:
            return "" if self.simbolo == LAMBDA else self.simbolo
        return "".join(filho.fronteira() for filho in self.filhos)


@dataclass
class PassoDerivacao:
    forma: str            # forma sentencial depois do passo
    producao: str         # produção aplicada ("" no passo inicial)


@dataclass
class ResultadoGLC:
    cadeia: str
    aceita: bool
    arvore: No | None = None
    derivacao: list[PassoDerivacao] = field(default_factory=list)
    itens_earley: int = 0     # itens criados na tabela (medida de trabalho)
    motivo: str = ""

    def derivacao_texto(self) -> str:
        return " ⇒ ".join(p.forma for p in self.derivacao)


class Gramatica:
    def __init__(self, variaveis, terminais, producoes, inicial, nome="Gramática"):
        """``producoes``: dict {variável: [lado direito, ...]}.

        Cada lado direito pode ser uma string (``"aSb"``, ``"λ"``) ou uma lista
        de símbolos já separados.
        """
        self.nome = nome
        self.variaveis: list[str] = list(variaveis)
        self.terminais: list[str] = list(terminais)
        self.inicial: str = inicial
        if inicial not in self.variaveis:
            raise ValueError(f"O símbolo inicial {inicial!r} não é uma variável.")
        if set(self.variaveis) & set(self.terminais):
            raise ValueError("V e T devem ser conjuntos disjuntos.")
        self.producoes: dict[str, list[tuple[str, ...]]] = {v: [] for v in self.variaveis}
        for variavel, lados in producoes.items():
            if variavel not in self.producoes:
                raise ValueError(f"{variavel!r} aparece à esquerda de uma produção mas não está em V.")
            for lado in lados:
                simbolos = self._separar(lado) if isinstance(lado, str) else tuple(lado)
                if simbolos not in self.producoes[variavel]:
                    self.producoes[variavel].append(simbolos)
        self.anulaveis = self._calcular_anulaveis()

    # ------------------------------------------------------------------ #
    # Construção
    # ------------------------------------------------------------------ #
    def _separar(self, texto: str) -> tuple[str, ...]:
        """Quebra ``"aSb"`` em ('a', 'S', 'b'); aceita símbolos com mais de 1 caractere."""
        texto = texto.strip()
        if texto in VAZIOS:
            return ()
        simbolos = sorted(self.variaveis + self.terminais, key=len, reverse=True)
        resultado, i = [], 0
        while i < len(texto):
            if texto[i].isspace():
                i += 1
                continue
            for s in simbolos:                       # casamento do símbolo mais longo
                if texto.startswith(s, i):
                    resultado.append(s)
                    i += len(s)
                    break
            else:
                raise ValueError(f"Símbolo desconhecido em {texto!r} na posição {i + 1}: {texto[i]!r}")
        return tuple(resultado)

    @classmethod
    def de_dict(cls, dados: dict) -> "Gramatica":
        return cls(dados["variaveis"], dados["terminais"], dados["producoes"],
                   dados["inicial"], dados.get("nome", "Gramática"))

    @classmethod
    def de_json(cls, caminho: str | Path) -> "Gramatica":
        with open(caminho, encoding="utf-8") as arquivo:
            return cls.de_dict(json.load(arquivo))

    @classmethod
    def de_texto(cls, texto: str, inicial: str | None = None) -> "Gramatica":
        """Lê produções no formato ``S -> aSb | λ`` (uma variável por linha).

        Variáveis são os símbolos à esquerda das setas; todo o resto é terminal.
        """
        regras: list[tuple[str, list[str]]] = []
        for linha in texto.splitlines():
            linha = linha.strip()
            if not linha:
                continue
            for seta in ("->", "→"):
                if seta in linha:
                    esquerda, direita = linha.split(seta, 1)
                    break
            else:
                raise ValueError(f"Produção sem seta '->': {linha!r}")
            regras.append((esquerda.strip(), [p.strip() for p in direita.split("|")]))
        if not regras:
            raise ValueError("Nenhuma produção informada.")
        variaveis = list(dict.fromkeys(v for v, _ in regras))
        terminais: list[str] = []
        for _, lados in regras:
            for lado in lados:
                resto = lado
                for v in sorted(variaveis, key=len, reverse=True):
                    resto = resto.replace(v, " ")
                for c in resto:
                    if not c.isspace() and c not in VAZIOS and c not in terminais:
                        terminais.append(c)
        producoes: dict[str, list[str]] = {}
        for v, lados in regras:
            producoes.setdefault(v, []).extend(lados)
        return cls(variaveis, terminais, producoes, inicial or variaveis[0])

    def _calcular_anulaveis(self) -> dict[str, No]:
        """Variáveis que derivam λ, cada uma com uma árvore que comprova isso.

        Iteração de ponto fixo: uma variável é anulável se alguma produção
        tem todos os símbolos do lado direito já anuláveis.
        """
        anulaveis: dict[str, No] = {}
        mudou = True
        while mudou:
            mudou = False
            for variavel, lados in self.producoes.items():
                if variavel in anulaveis:
                    continue
                for lado in lados:
                    if all(s in anulaveis for s in lado):
                        filhos = [anulaveis[s] for s in lado] or [No(LAMBDA)]
                        anulaveis[variavel] = No(variavel, filhos, lado)
                        mudou = True
                        break
        return anulaveis

    # ------------------------------------------------------------------ #
    # Reconhecimento - algoritmo de Earley
    # ------------------------------------------------------------------ #
    def reconhecer(self, cadeia: str) -> ResultadoGLC:
        """Decide se cadeia ∈ L(G) e, se sim, devolve árvore e derivação.

        Um item de Earley é (variável, lado direito, ponto, origem): a
        produção ``variável -> lado`` já reconheceu ``lado[:ponto]`` a partir
        da posição ``origem``. ``tabela[k]`` guarda os itens válidos depois de
        ler k símbolos. Para cada item guardamos os filhos já reconhecidos,
        o que permite montar a árvore sem um segundo passe.

        Custo: O(n³) no pior caso, O(n²) para gramáticas não ambíguas.
        """
        resultado = ResultadoGLC(cadeia, False)
        simbolos = self._tokenizar(cadeia)
        if simbolos is None:
            resultado.motivo = "A cadeia contém símbolos que não são terminais da gramática."
            return resultado

        n = len(simbolos)
        # tabela[k]: item -> nós filhos já reconhecidos; ordem[k]: fila de processamento
        tabela: list[dict[tuple, list[No]]] = [dict() for _ in range(n + 1)]
        ordem: list[list[tuple]] = [[] for _ in range(n + 1)]

        def adicionar(k: int, item: tuple, filhos: list[No]) -> None:
            if item not in tabela[k]:        # guarda só a 1ª derivação encontrada
                tabela[k][item] = filhos
                ordem[k].append(item)

        for lado in self.producoes[self.inicial]:
            adicionar(0, (self.inicial, lado, 0, 0), [])

        for k in range(n + 1):
            i = 0
            while i < len(ordem[k]):         # a fila cresce durante o laço
                item = ordem[k][i]
                i += 1
                variavel, lado, ponto, origem = item
                filhos = tabela[k][item]

                if ponto < len(lado):
                    proximo = lado[ponto]
                    if proximo in self.producoes:
                        # PREVISÃO: abre as produções da variável esperada
                        for alternativa in self.producoes[proximo]:
                            adicionar(k, (proximo, alternativa, 0, k), [])
                        # variável anulável: também avança o ponto sobre ela
                        if proximo in self.anulaveis:
                            adicionar(k, (variavel, lado, ponto + 1, origem),
                                      filhos + [self.anulaveis[proximo]])
                    elif k < n and simbolos[k] == proximo:
                        # LEITURA: o terminal esperado é o próximo da entrada
                        adicionar(k + 1, (variavel, lado, ponto + 1, origem),
                                  filhos + [No(proximo)])
                else:
                    # CONCLUSÃO: variável reconhecida; avança quem esperava por ela
                    no = No(variavel, filhos or [No(LAMBDA)], lado)
                    for pai in list(ordem[origem]):
                        v2, lado2, ponto2, origem2 = pai
                        if ponto2 < len(lado2) and lado2[ponto2] == variavel:
                            adicionar(k, (v2, lado2, ponto2 + 1, origem2),
                                      tabela[origem][pai] + [no])

        resultado.itens_earley = sum(len(conjunto) for conjunto in tabela)
        for item, filhos in tabela[n].items():
            variavel, lado, ponto, origem = item
            if variavel == self.inicial and ponto == len(lado) and origem == 0:
                resultado.aceita = True
                resultado.arvore = No(variavel, filhos or [No(LAMBDA)], lado)
                resultado.derivacao = self.derivacao_esquerda(resultado.arvore)
                resultado.motivo = f"Existe uma derivação {self.inicial} ⇒* w."
                return resultado
        resultado.motivo = "Nenhuma derivação a partir do símbolo inicial gera a cadeia."
        return resultado

    def _tokenizar(self, cadeia: str) -> list[str] | None:
        terminais = sorted(self.terminais, key=len, reverse=True)
        resultado, i = [], 0
        while i < len(cadeia):
            for t in terminais:
                if cadeia.startswith(t, i):
                    resultado.append(t)
                    i += len(t)
                    break
            else:
                return None
        return resultado

    def aceita(self, cadeia: str) -> bool:
        return self.reconhecer(cadeia).aceita

    # ------------------------------------------------------------------ #
    # Derivação e árvore
    # ------------------------------------------------------------------ #
    def derivacao_esquerda(self, arvore: No) -> list[PassoDerivacao]:
        """Derivação mais à esquerda obtida da árvore (percurso em pré-ordem)."""
        # forma sentencial como lista de nós; variável ainda não expandida
        # é o nó que tem ``producao`` (terminais não têm)
        forma: list[No] = [arvore]
        passos = [PassoDerivacao(arvore.simbolo, "")]
        while True:
            indice = next((i for i, no in enumerate(forma) if no.producao is not None), None)
            if indice is None:
                return passos
            no = forma[indice]
            # o filho λ some da forma sentencial
            forma[indice:indice + 1] = [f for f in no.filhos if f.simbolo != LAMBDA]
            texto = "".join(x.simbolo for x in forma) or LAMBDA
            passos.append(PassoDerivacao(texto, formatar_producao(no.simbolo, no.producao)))

    @staticmethod
    def arvore_texto(no: No, prefixo: str = "", ultimo: bool = True, raiz: bool = True) -> list[str]:
        """Desenha a árvore de derivação com caracteres de caixa."""
        if raiz:
            linhas = [no.simbolo]
        else:
            linhas = [prefixo + ("└── " if ultimo else "├── ") + no.simbolo]
            prefixo += "    " if ultimo else "│   "
        for i, filho in enumerate(no.filhos):
            linhas += Gramatica.arvore_texto(filho, prefixo, i == len(no.filhos) - 1, False)
        return linhas

    @staticmethod
    def arvore_dot(arvore: No) -> str:
        """Árvore de derivação em Graphviz DOT."""
        linhas = ["digraph Arvore {", '  bgcolor="transparent";',
                  '  node [fontname="Helvetica", shape=circle, style=filled, color="#444444"];',
                  '  edge [arrowhead=none, color="#444444"];']
        contador = [0]

        def visitar(no: No) -> str:
            ident = f"n{contador[0]}"
            contador[0] += 1
            cor = "#D9ECEF" if no.filhos else ("#EEEEEE" if no.simbolo == LAMBDA else "#FFC53D")
            linhas.append(f'  {ident} [label="{no.simbolo}", fillcolor="{cor}"];')
            for filho in no.filhos:
                linhas.append(f"  {ident} -> {visitar(filho)};")
            return ident

        visitar(arvore)
        linhas.append("}")
        return "\n".join(linhas)

    def producoes_texto(self) -> list[str]:
        return [f"{v} -> " + " | ".join("".join(lado) or LAMBDA for lado in lados)
                for v, lados in self.producoes.items() if lados]


def formatar_producao(variavel: str, lado) -> str:
    return f"{variavel} -> {''.join(lado) or LAMBDA}"
