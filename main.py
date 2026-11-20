"""Interface de console do Simulador de Linguagens Formais.

Uso:
    python main.py           -> menu interativo
    python main.py --demo    -> executa os exemplos do enunciado, sem perguntas
"""

from __future__ import annotations

import sys
from pathlib import Path

from simulador import (Alfabeto, AutomatoFinito, AutomatoPilha, Gramatica,
                       Linguagem, MaquinaTuring)
from simulador.automato_finito import formatar_conjunto
from simulador.complexidade import ANALISE, COLUNAS_MEDICAO, medir
from simulador.linguagens import exibir

EXEMPLOS = Path(__file__).parent / "exemplos"


# ---------------------------------------------------------------------- #
# Utilitários de console
# ---------------------------------------------------------------------- #
def titulo(texto: str) -> None:
    print("\n" + "=" * 64)
    print(texto)
    print("=" * 64)


def perguntar(mensagem: str, padrao: str = "") -> str:
    sufixo = f" [{padrao}]" if padrao else ""
    resposta = input(f"{mensagem}{sufixo}: ").strip()
    return resposta or padrao


def ler_cadeia(mensagem: str = "Cadeia de entrada (ENTER = cadeia vazia λ)") -> str:
    return input(f"{mensagem}: ").strip().replace("λ", "")


def escolher_arquivo(prefixos: tuple[str, ...]) -> Path:
    """Lista os JSON de exemplos/ com os prefixos dados e devolve o escolhido."""
    arquivos = sorted(a for a in EXEMPLOS.glob("*.json") if a.name.startswith(prefixos))
    for i, arquivo in enumerate(arquivos, 1):
        print(f"  {i}) {arquivo.name}")
    print("  ou digite o caminho de outro arquivo .json")
    resposta = perguntar("Arquivo", "1")
    if resposta.isdigit() and 1 <= int(resposta) <= len(arquivos):
        return arquivos[int(resposta) - 1]
    return Path(resposta)


def veredito(aceita: bool) -> str:
    return "ACEITA" if aceita else "REJEITA"


# ---------------------------------------------------------------------- #
# Módulo 1 - Linguagens formais
# ---------------------------------------------------------------------- #
def mostrar_linguagens(alfabeto: Alfabeto, cadeia: str, segunda: str, tamanho_max: int,
                       linguagem: Linguagem | None) -> None:
    print(f"Σ = {alfabeto}")
    print(f"Entrada: {exibir(cadeia)}")
    if alfabeto.valida(cadeia):
        print("Cadeia válida para Σ")
    else:
        erros = ", ".join(f"'{s}' (posição {i + 1})" for i, s in alfabeto.simbolos_invalidos(cadeia))
        print(f"Cadeia INVÁLIDA para Σ: {erros}")
    print(f"Tamanho = {alfabeto.tamanho(cadeia)}")
    print(f"Concatenação: {exibir(cadeia)} · {exibir(segunda)} = "
          f"{exibir(alfabeto.concatenar(cadeia, segunda))}")
    estrela = [exibir(w) for w in alfabeto.sigma_estrela(tamanho_max)]
    mais = [exibir(w) for w in alfabeto.sigma_mais(tamanho_max)]
    print(f"Σ* (até tamanho {tamanho_max}, {len(estrela)} cadeias) = {{{', '.join(estrela)}, ...}}")
    print(f"Σ+ (até tamanho {tamanho_max}, {len(mais)} cadeias) = {{{', '.join(mais)}, ...}}")
    if linguagem is not None:
        print(f"L = {linguagem}")
        pertence = "∈" if linguagem.pertence(cadeia) else "∉"
        print(f"{exibir(cadeia)} {pertence} L")
        if not linguagem.finita:
            amostra = [exibir(w) for w in linguagem.enumerar(tamanho_max)]
            print(f"Cadeias de L até tamanho {tamanho_max}: {{{', '.join(amostra)}}}")


def modulo_linguagens() -> None:
    titulo("MÓDULO 1 - LINGUAGENS FORMAIS")
    alfabeto = Alfabeto.de_texto(perguntar("Alfabeto Σ (símbolos separados por vírgula)", "a,b"))
    print("Definição da linguagem L:")
    print("  1) por enumeração (ex.: ab, abba, λ)")
    print("  2) por expressão regular (ex.: (ab)*)")
    print("  3) não definir")
    opcao = perguntar("Opção", "1")
    linguagem = None
    if opcao == "1":
        cadeias = [c.strip() for c in perguntar("Cadeias de L separadas por vírgula", "ab,abba,λ").split(",")]
        linguagem = Linguagem(alfabeto, cadeias=cadeias)
    elif opcao == "2":
        linguagem = Linguagem(alfabeto, regex=perguntar("Expressão regular", "(ab)*"))
    cadeia = ler_cadeia()
    segunda = ler_cadeia("Segunda cadeia para concatenar (ENTER = λ)")
    tamanho_max = int(perguntar("Tamanho máximo para listar Σ* e Σ+", "2"))
    print()
    mostrar_linguagens(alfabeto, cadeia, segunda, tamanho_max, linguagem)


# ---------------------------------------------------------------------- #
# Módulo 2 - Autômato finito
# ---------------------------------------------------------------------- #
def mostrar_automato(af: AutomatoFinito) -> None:
    print(f"{af.nome}  [{af.tipo}]")
    print(f"Q = {{{', '.join(af.estados)}}}   Σ = {{{', '.join(af.alfabeto)}}}   "
          f"q0 = {af.inicial}   F = {{{', '.join(sorted(af.finais))}}}")
    for linha in af.tabela_transicoes():
        print("  " + linha)


def mostrar_simulacao_af(af: AutomatoFinito, cadeia: str) -> None:
    resultado = af.simular(cadeia)
    print(f"Entrada: {exibir(cadeia)}")
    print("Passo a passo:")
    if af.deterministico:
        for p in resultado.passos:
            destino = next(iter(p.destino)) if p.destino else "(sem transição)"
            print(f"  {p.indice + 1}. δ({next(iter(p.origem))}, {p.simbolo}) = {destino}")
    else:
        print(f"  0. início (com fecho-λ): {formatar_conjunto(resultado.estados_iniciais)}")
        for p in resultado.passos:
            print(f"  {p.indice + 1}. lê '{p.simbolo}': {formatar_conjunto(p.origem)} "
                  f"-> {formatar_conjunto(p.destino)}")
    print(f"Caminho: {resultado.caminho_texto()}")
    print(veredito(resultado.aceita))
    print(f"({resultado.motivo})")


def modulo_automato_finito() -> None:
    titulo("MÓDULO 2 - AUTÔMATO FINITO (AFD / AFN)")
    af = AutomatoFinito.de_json(escolher_arquivo(("afd", "afn")))
    print()
    mostrar_automato(af)
    while True:
        print()
        mostrar_simulacao_af(af, ler_cadeia())
        if not af.deterministico and perguntar("Mostrar o AFD equivalente? (s/n)", "n") == "s":
            mostrar_automato(af.para_afd())
        if perguntar("Testar outra cadeia? (s/n)", "s") != "s":
            break


# ---------------------------------------------------------------------- #
# Módulo 3 - GLC
# ---------------------------------------------------------------------- #
def mostrar_gramatica(g: Gramatica) -> None:
    print(g.nome)
    print(f"V = {{{', '.join(g.variaveis)}}}   T = {{{', '.join(g.terminais)}}}   S = {g.inicial}")
    for linha in g.producoes_texto():
        print("  " + linha)


def mostrar_reconhecimento_glc(g: Gramatica, cadeia: str) -> None:
    resultado = g.reconhecer(cadeia)
    print(f"Entrada: {exibir(cadeia)}")
    if resultado.aceita:
        print("Derivação passo a passo (mais à esquerda):")
        for i, passo in enumerate(resultado.derivacao):
            regra = f"   [{passo.producao}]" if passo.producao else ""
            seta = "  " if i == 0 else "⇒ "
            print(f"  {seta}{passo.forma}{regra}")
        print("Árvore de derivação:")
        for linha in Gramatica.arvore_texto(resultado.arvore):
            print("  " + linha)
    print("ACEITA" if resultado.aceita else "REJEITA")
    print(f"({resultado.motivo})")


def modulo_glc() -> None:
    titulo("MÓDULO 3 - GRAMÁTICA LIVRE DE CONTEXTO")
    print("  1) carregar de um arquivo JSON")
    print("  2) digitar as produções")
    if perguntar("Opção", "1") == "2":
        print("Digite uma produção por linha (ex.: S -> aSb | λ). Linha vazia encerra.")
        linhas = []
        while (linha := input("  ").strip()):
            linhas.append(linha)
        g = Gramatica.de_texto("\n".join(linhas))
    else:
        g = Gramatica.de_json(escolher_arquivo(("glc",)))
    print()
    mostrar_gramatica(g)
    while True:
        print()
        mostrar_reconhecimento_glc(g, ler_cadeia())
        if perguntar("Testar outra cadeia? (s/n)", "s") != "s":
            break


# ---------------------------------------------------------------------- #
# Módulo 4 - Autômato com pilha
# ---------------------------------------------------------------------- #
def mostrar_simulacao_ap(ap: AutomatoPilha, cadeia: str) -> None:
    resultado = ap.simular(cadeia)
    print(f"Entrada: {exibir(cadeia)}")
    print(f"  {'Passo':<6}{'Leitura':<9}{'Estado':<8}{'Pilha (topo à esq.)':<22}{'Restante':<12}Transição")
    for i, p in enumerate(resultado.passos):
        print(f"  {i:<6}{p.leitura:<9}{p.estado:<8}{p.pilha_texto():<22}"
              f"{exibir(p.restante):<12}{p.acao}")
    print(veredito(resultado.aceita))
    print(f"({resultado.motivo})")


def modulo_ap() -> None:
    titulo("MÓDULO 4 - AUTÔMATO COM PILHA")
    ap = AutomatoPilha.de_json(escolher_arquivo(("ap",)))
    print(f"\n{ap.nome}")
    for linha in ap.tabela_transicoes():
        print("  " + linha)
    while True:
        print()
        mostrar_simulacao_ap(ap, ler_cadeia())
        if perguntar("Testar outra cadeia? (s/n)", "s") != "s":
            break


# ---------------------------------------------------------------------- #
# Módulo 5 - Máquina de Turing
# ---------------------------------------------------------------------- #
def mostrar_execucao_mt(mt: MaquinaTuring, entrada: str, max_linhas: int = 60) -> None:
    resultado = mt.executar(entrada)
    print(f"Entrada: {exibir(entrada)}")
    print(f"  {'Passo':<6}{'Estado':<10}Fita (cabeça entre colchetes)")
    passos = resultado.passos
    cortar = len(passos) > max_linhas
    visiveis = passos[:max_linhas // 2] + passos[-max_linhas // 2:] if cortar else passos
    for i, p in enumerate(visiveis):
        if cortar and i == max_linhas // 2:
            print(f"  ... ({len(passos) - max_linhas} passos omitidos) ...")
        print(f"  {p.numero:<6}{p.estado:<10}{p.fita_texto()}")
    print(f"Total de transições: {resultado.total_passos}")
    print(f"Fita final: {exibir(resultado.saida)}")
    print(veredito(resultado.aceita))
    print(f"({resultado.motivo})")


def modulo_turing() -> None:
    titulo("MÓDULO 5 - MÁQUINA DE TURING")
    print("  A) Reconhecer L = { w#w }")
    print("  B) Somar dois números em unário (ex.: 000100 = 3 + 2)")
    print("  C) Carregar outra máquina de um arquivo JSON")
    opcao = perguntar("Opção", "A").upper()
    if opcao == "B":
        mt = MaquinaTuring.soma_unaria()
    elif opcao == "C":
        mt = MaquinaTuring.de_json(escolher_arquivo(("mt",)))
    else:
        mt = MaquinaTuring.w_hash_w()
    print(f"\n{mt.nome}\n{mt.descricao}")
    for linha in mt.tabela_transicoes():
        print("  " + linha)
    while True:
        print()
        mostrar_execucao_mt(mt, ler_cadeia())
        if perguntar("Testar outra entrada? (s/n)", "s") != "s":
            break


# ---------------------------------------------------------------------- #
# Módulo 6 - Complexidade
# ---------------------------------------------------------------------- #
def mostrar_complexidade() -> None:
    modulo_atual = ""
    for a in ANALISE:
        if a.modulo != modulo_atual:
            modulo_atual = a.modulo
            print(f"\n[{modulo_atual}]")
        print(f"  • {a.algoritmo}")
        print(f"      Melhor caso: {a.melhor}   Caso médio: {a.medio}   Pior caso: {a.pior}")
        print(f"      Espaço: {a.espaco}")
        print(f"      {a.justificativa}")
    print("\nMedição empírica (operações contadas pelo próprio simulador):")
    linhas = medir()
    cabecalho = list(COLUNAS_MEDICAO.values())
    larguras = [max(len(c), 6) + 2 for c in cabecalho]
    print("  " + "".join(c.ljust(l) for c, l in zip(cabecalho, larguras)))
    for linha in linhas:
        print("  " + "".join(str(linha[chave]).ljust(l) for chave, l in zip(COLUNAS_MEDICAO, larguras)))
    print("  Dobrar n dobra as colunas lineares (AFD, AP, MT soma, Earley aⁿbⁿ) e")
    print("  quadruplica as quadráticas (MT w#w, Earley com gramática ambígua).")


def modulo_complexidade() -> None:
    titulo("MÓDULO 6 - COMPLEXIDADE COMPUTACIONAL")
    mostrar_complexidade()


# ---------------------------------------------------------------------- #
# Demonstração e menu
# ---------------------------------------------------------------------- #
def demo() -> None:
    """Executa, sem interação, os exemplos do enunciado do projeto."""
    titulo("MÓDULO 1 - LINGUAGENS FORMAIS")
    alfabeto = Alfabeto.de_texto("a,b")
    mostrar_linguagens(alfabeto, "abba", "ab", 2, Linguagem(alfabeto, cadeias=["ab", "abba", "λ"]))

    titulo("MÓDULO 2 - AUTÔMATO FINITO (AFD / AFN)")
    afd = AutomatoFinito.de_json(EXEMPLOS / "afd_ab.json")
    mostrar_automato(afd)
    print()
    mostrar_simulacao_af(afd, "ab")
    print()
    afn = AutomatoFinito.de_json(EXEMPLOS / "afn_termina_ab.json")
    mostrar_automato(afn)
    print()
    mostrar_simulacao_af(afn, "aab")

    titulo("MÓDULO 3 - GRAMÁTICA LIVRE DE CONTEXTO")
    g = Gramatica.de_json(EXEMPLOS / "glc_anbn.json")
    mostrar_gramatica(g)
    print()
    mostrar_reconhecimento_glc(g, "aaabbb")
    print()
    mostrar_reconhecimento_glc(g, "aab")

    titulo("MÓDULO 4 - AUTÔMATO COM PILHA")
    ap = AutomatoPilha.anbn()
    print(ap.nome)
    print()
    mostrar_simulacao_ap(ap, "aabb")
    print()
    mostrar_simulacao_ap(ap, "aab")

    titulo("MÓDULO 5 - MÁQUINA DE TURING")
    print("Opção A - L = { w#w }\n")
    mostrar_execucao_mt(MaquinaTuring.w_hash_w(), "ab#ab")
    print("\nOpção B - soma em unário (3 + 2)\n")
    mostrar_execucao_mt(MaquinaTuring.soma_unaria(), "000100")

    modulo_complexidade()


MENU = {
    "1": ("Linguagens Formais", modulo_linguagens),
    "2": ("Autômato Finito (AFD / AFN)", modulo_automato_finito),
    "3": ("Gramática Livre de Contexto", modulo_glc),
    "4": ("Autômato com Pilha", modulo_ap),
    "5": ("Máquina de Turing", modulo_turing),
    "6": ("Complexidade Computacional", modulo_complexidade),
    "7": ("Demonstração completa (exemplos do enunciado)", demo),
}


def menu() -> None:
    while True:
        titulo("SIMULADOR DE LINGUAGENS FORMAIS E MODELOS COMPUTACIONAIS")
        for chave, (nome, _) in MENU.items():
            print(f"  {chave}) {nome}")
        print("  0) Sair")
        opcao = perguntar("Escolha")
        if opcao == "0":
            print("Até logo!")
            return
        if opcao not in MENU:
            print("Opção inválida.")
            continue
        try:
            MENU[opcao][1]()
        except (ValueError, KeyError, FileNotFoundError, OSError) as erro:
            # erro de definição (JSON, alfabeto, gramática): mostra e volta ao menu
            print(f"\nErro: {erro}")
        input("\nENTER para voltar ao menu...")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    else:
        try:
            menu()
        except (KeyboardInterrupt, EOFError):
            print("\nEncerrado.")
