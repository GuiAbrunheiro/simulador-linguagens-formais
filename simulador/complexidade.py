"""Módulo 6 - Complexidade Computacional.

Duas partes:

1. ``ANALISE``: a análise assintótica (teórica) de cada algoritmo do
   simulador, com melhor caso, caso médio e pior caso em Ω, Θ e O;
2. ``medir()``: uma medição empírica que conta operações reais do simulador
   para entradas cada vez maiores, para conferir a teoria na prática.

Convenções: n = tamanho da cadeia de entrada, |Q| = número de estados,
k = |Σ|, m = tamanho máximo pedido para Σ*, |G| = tamanho da gramática.
"""

from __future__ import annotations

from dataclasses import dataclass

from .automato_finito import AutomatoFinito
from .automato_pilha import AutomatoPilha
from .glc import Gramatica
from .turing import MaquinaTuring


@dataclass(frozen=True)
class Analise:
    modulo: str
    algoritmo: str
    melhor: str        # limite inferior do melhor caso
    medio: str         # caso médio
    pior: str          # limite superior do pior caso
    espaco: str
    justificativa: str


ANALISE: list[Analise] = [
    Analise("1. Linguagens", "Validar cadeia em Σ (varredura linear)",
            "Ω(1)", "Θ(n)", "O(n)", "O(k)",
            "Percorre a cadeia consultando um conjunto hash (O(1) por símbolo). Para no "
            "primeiro símbolo inválido: melhor caso quando ele é o 1º; cadeias válidas "
            "sempre custam n consultas."),
    Analise("1. Linguagens", "Tamanho |w| e concatenação u·v",
            "Ω(1) / Ω(|u|+|v|)", "Θ(1) / Θ(|u|+|v|)", "O(1) / O(|u|+|v|)", "O(|u|+|v|)",
            "O tamanho já fica guardado na string (acesso direto). A concatenação copia "
            "os símbolos das duas cadeias para uma nova."),
    Analise("1. Linguagens", "Enumerar Σ* / Σ+ até o tamanho m",
            "Ω(m·k^m)", "Θ(m·k^m)", "O(m·k^m)", "O(m) por cadeia",
            "São (k^(m+1) − 1)/(k − 1) cadeias e cada uma precisa ser escrita: o custo é "
            "o tamanho da própria saída, igual em todos os casos (crescimento exponencial em m)."),
    Analise("2. Autômato finito", "Simulação de AFD (δ em tabela hash)",
            "Ω(1)", "Θ(n)", "O(n)", "O(n) com passo a passo",
            "Uma consulta O(1) a δ por símbolo. Melhor caso: o autômato trava no 1º "
            "símbolo. Cadeias aceitas exigem ler os n símbolos."),
    Analise("2. Autômato finito", "Simulação de AFN (conjunto de estados + fecho-λ)",
            "Ω(1)", "Θ(n·|Q|²)", "O(n·|Q|²)", "O(n·|Q|)",
            "A cada símbolo, cada um dos até |Q| estados ativos contribui com até |Q| "
            "destinos, e o fecho-λ é uma busca em profundidade no grafo das transições λ."),
    Analise("2. Autômato finito", "Conversão AFN → AFD (subconjuntos)",
            "Ω(|Q|·k)", "—", "O(2^|Q|·k·|Q|²)", "O(2^|Q|·k)",
            "Cada estado do AFD é um subconjunto de Q; podem existir 2^|Q| subconjuntos "
            "alcançáveis. Se o AFN já é determinístico, só |Q| subconjuntos são gerados."),
    Analise("3. GLC", "Reconhecimento de Earley",
            "Ω(n)", "Θ(n²) em gramáticas não ambíguas", "O(n³)", "O(n²)",
            "Cada um dos n+1 conjuntos tem O(n) itens; a etapa de conclusão percorre um "
            "conjunto anterior (O(n)), dando O(n³). Sem ambiguidade cada item é criado "
            "uma única vez (O(n²)); em gramáticas como S → aS | λ há O(1) itens por conjunto."),
    Analise("3. GLC", "Derivação mais à esquerda a partir da árvore",
            "Ω(t)", "Θ(t·n)", "O(t·f)", "O(t)",
            "t = nós da árvore e f = maior forma sentencial. Cada passo procura a "
            "variável mais à esquerda e reescreve a forma. Em aⁿbⁿ isso dá Θ(n²)."),
    Analise("4. Autômato com pilha", "Empilhar / desempilhar",
            "Ω(1)", "Θ(1)", "O(1) amortizado", "O(n)",
            "A pilha é uma lista dinâmica com o topo no final: append e pop não deslocam elementos."),
    Analise("4. Autômato com pilha", "Simulação por busca em largura nas configurações",
            "Ω(n)", "Θ(n²) em APs determinísticos (aⁿbⁿ)", "O(b^t) (exponencial)", "O(c·n)",
            "c = configurações visitadas. Em aⁿbⁿ há Θ(n) configurações, mas cada uma "
            "guarda uma cópia da pilha (até n símbolos) para o passo a passo: Θ(n²). "
            "Em APs não determinísticos, com b escolhas por passo e t passos, o espaço "
            "de busca pode crescer exponencialmente (por isso existe um limite)."),
    Analise("5. Máquina de Turing", "Opção A: reconhecer w#w",
            "Ω(1)", "Θ(n²) para cadeias aceitas", "O(n²)", "O(n)",
            "Para cada símbolo de w a cabeça atravessa a fita até a outra metade e volta: "
            "|w| viagens de comprimento proporcional a |w|. Exatamente 2(|w|+1)² "
            "transições quando aceita. Melhor caso: rejeição imediata (ex.: '#a')."),
    Analise("5. Máquina de Turing", "Opção B: soma em unário",
            "Ω(n)", "Θ(n)", "O(n)", "O(n)",
            "Uma ida até o fim da fita e uma volta: exatamente 2n + 2 transições para "
            "entradas válidas, em todos os casos."),
    Analise("5. Máquina de Turing", "Passo de simulação (δ em tabela hash, fita em dicionário)",
            "Ω(1)", "Θ(1)", "O(1)", "O(células usadas)",
            "Cada transição é uma consulta e uma escrita em tabela hash. Guardar a fita "
            "de cada passo para a visualização acrescenta O(n) por passo."),
]


# ---------------------------------------------------------------------- #
# Medição empírica
# ---------------------------------------------------------------------- #
def _afd_par_de_a() -> AutomatoFinito:
    return AutomatoFinito(["p", "i"], ["a", "b"],
                          {("p", "a"): {"i"}, ("i", "a"): {"p"},
                           ("p", "b"): {"p"}, ("i", "b"): {"i"}}, "p", ["p"])


def medir(tamanhos=(2, 4, 8, 16, 32, 64)) -> list[dict]:
    """Conta operações reais do simulador para entradas de tamanho crescente.

    Cada linha traz, para um valor de n (|w| = n em cada metade/parcela):

    * ``afd``      - transições do AFD ao ler uma cadeia de tamanho 2n;
    * ``earley``   - itens criados por Earley para aⁿbⁿ com S → aSb | λ;
    * ``earley_amb`` - itens para aⁿ com a gramática ambígua S → SS | a;
    * ``ap``       - configurações visitadas pelo AP para aⁿbⁿ;
    * ``mt_wsw``   - transições da MT para aⁿ#aⁿ;
    * ``mt_soma``  - transições da MT para 0ⁿ10ⁿ.
    """
    afd = _afd_par_de_a()
    glc = Gramatica.de_texto("S -> aSb | λ")
    glc_ambigua = Gramatica.de_texto("S -> SS | a")
    ap = AutomatoPilha.anbn()
    mt_a = MaquinaTuring.w_hash_w()
    mt_b = MaquinaTuring.soma_unaria()

    linhas = []
    for n in tamanhos:
        linhas.append({
            "n": n,
            "afd": len(afd.simular("ab" * n).passos),
            "earley": glc.reconhecer("a" * n + "b" * n).itens_earley,
            "earley_amb": glc_ambigua.reconhecer("a" * n).itens_earley,
            "ap": ap.simular("a" * n + "b" * n).configuracoes_exploradas,
            "mt_wsw": mt_a.executar("a" * n + "#" + "a" * n, guardar_passos=False).total_passos,
            "mt_soma": mt_b.executar("0" * n + "1" + "0" * n, guardar_passos=False).total_passos,
        })
    return linhas


COLUNAS_MEDICAO = {
    "n": "n",
    "afd": "AFD (transições)",
    "earley": "Earley aⁿbⁿ (itens)",
    "earley_amb": "Earley ambígua (itens)",
    "ap": "AP aⁿbⁿ (configurações)",
    "mt_wsw": "MT w#w (transições)",
    "mt_soma": "MT soma (transições)",
}
