"""Interface gráfica (Streamlit) do Simulador de Linguagens Formais.

Executar com:
    streamlit run app.py

Mostra visualmente os estados dos autômatos, a pilha do AP e a fita da
Máquina de Turing, com um controle deslizante para avançar passo a passo.
Toda a lógica está no pacote ``simulador``; este arquivo só desenha.
"""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

import streamlit as st

from simulador import (Alfabeto, AutomatoFinito, AutomatoPilha, Gramatica,
                       Linguagem, MaquinaTuring)
from simulador.automato_finito import formatar_conjunto
from simulador.complexidade import ANALISE, COLUNAS_MEDICAO, medir
from simulador.linguagens import exibir
from simulador.turing import BRANCO

EXEMPLOS = Path(__file__).parent / "exemplos"
COR_ATIVO = "#FFC53D"

st.set_page_config(page_title="Simulador de Linguagens Formais", page_icon="🧮", layout="wide")

st.markdown("""
<style>
.celulas {display:flex; flex-wrap:wrap; gap:4px; margin:6px 0 2px 0; font-family:monospace;}
.celula {min-width:38px; height:38px; border:2px solid #555; border-radius:6px;
         display:flex; align-items:center; justify-content:center; font-size:18px;
         background:#fff; color:#111;}
.celula.ativa {background:#FFC53D; border-color:#B36B00; font-weight:700;}
.celula.lida {background:#E3E3E3; color:#777;}
.celula.branco {color:#bbb;}
.pilha {display:inline-flex; flex-direction:column; gap:4px; padding:8px 10px;
        border:3px solid #555; border-top:none; border-radius:0 0 8px 8px; min-width:74px;
        min-height:60px; justify-content:flex-end; font-family:monospace;}
.pilha .celula {width:54px;}
.legenda {font-size:13px; color:#666;}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------- #
# Componentes visuais
# ---------------------------------------------------------------------- #
def selo(aceita: bool, motivo: str = "") -> None:
    if aceita:
        st.success(f"**ACEITA** — {motivo}" if motivo else "**ACEITA**")
    else:
        st.error(f"**REJEITA** — {motivo}" if motivo else "**REJEITA**")


def desenhar_entrada(cadeia: str, lidos: int) -> None:
    """Entrada como fileira de células: lidas em cinza, a próxima em destaque."""
    if not cadeia:
        st.markdown('<div class="celulas"><div class="celula branco">λ</div></div>', unsafe_allow_html=True)
        return
    celulas = []
    for i, simbolo in enumerate(cadeia):
        classe = "lida" if i < lidos else ("ativa" if i == lidos else "")
        celulas.append(f'<div class="celula {classe}">{escape(simbolo)}</div>')
    st.markdown(f'<div class="celulas">{"".join(celulas)}</div>', unsafe_allow_html=True)


def desenhar_pilha(pilha: tuple[str, ...]) -> None:
    """Pilha na vertical, com o topo em cima e em destaque."""
    celulas = []
    for i, simbolo in enumerate(reversed(pilha)):
        classe = "ativa" if i == 0 else ""
        celulas.append(f'<div class="celula {classe}">{escape(simbolo)}</div>')
    conteudo = "".join(celulas) or '<div class="legenda">(vazia)</div>'
    st.markdown(f'<div class="legenda">topo ↓</div><div class="pilha">{conteudo}</div>',
                unsafe_allow_html=True)


def desenhar_fita(fita: dict[int, str], cabeca: int, margem: int = 2) -> None:
    """Fita da MT com a célula sob a cabeça em destaque."""
    posicoes = list(fita) + [cabeca]
    celulas = []
    for i in range(min(posicoes) - margem, max(posicoes) + margem + 1):
        simbolo = fita.get(i, BRANCO)
        classes = "celula" + (" ativa" if i == cabeca else "") + (" branco" if simbolo == BRANCO and i != cabeca else "")
        celulas.append(f'<div class="{classes}">{escape(simbolo)}</div>')
    st.markdown(f'<div class="celulas">{"".join(celulas)}</div>'
                '<div class="legenda">célula amarela = posição da cabeça de leitura/escrita</div>',
                unsafe_allow_html=True)


def controle_de_passo(chave: str, total: int) -> int:
    """Controle deslizante de passo (0 = configuração inicial)."""
    if total == 0:
        return 0
    return st.slider("Passo da execução", 0, total, total, key=chave,
                     help="Arraste para avançar ou voltar a execução passo a passo.")


def carregar_definicao(rotulo: str, prefixos: tuple[str, ...], chave: str) -> dict | None:
    """Escolhe um exemplo, envia um arquivo ou edita o JSON; devolve o dicionário."""
    arquivos = sorted(a for a in EXEMPLOS.glob("*.json") if a.name.startswith(prefixos))
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        escolhido = st.selectbox(f"Exemplo de {rotulo}", arquivos, format_func=lambda a: a.name, key=f"{chave}_ex")
    with coluna2:
        enviado = st.file_uploader("ou carregue um arquivo JSON", type="json", key=f"{chave}_up")
    texto = enviado.getvalue().decode("utf-8") if enviado else escolhido.read_text(encoding="utf-8")
    with st.expander("Ver / editar o JSON"):
        texto = st.text_area("Definição em JSON", texto, height=260,
                             key=f"{chave}_json_{enviado.name if enviado else escolhido.name}")
    try:
        return json.loads(texto)
    except json.JSONDecodeError as erro:
        st.error(f"JSON inválido: {erro}")
        return None


def ler_cadeia(rotulo: str, padrao: str, chave: str) -> str:
    return st.text_input(rotulo, padrao, key=chave, help="Deixe vazio para a cadeia vazia (λ).").strip().replace("λ", "")


# ---------------------------------------------------------------------- #
# Abas
# ---------------------------------------------------------------------- #
def aba_linguagens() -> None:
    st.subheader("Módulo 1 — Linguagens Formais")
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        texto_alfabeto = st.text_input("Alfabeto Σ (símbolos separados por vírgula)", "a, b")
        cadeia = ler_cadeia("Cadeia de entrada", "abba", "l_cadeia")
        segunda = ler_cadeia("Segunda cadeia (para concatenar)", "ab", "l_segunda")
        tamanho_max = st.slider("Tamanho máximo para listar Σ* e Σ+", 0, 5, 2)
    with coluna2:
        modo = st.radio("Definição da linguagem L", ["Enumeração", "Expressão regular"], horizontal=True)
        if modo == "Enumeração":
            texto_l = st.text_input("Cadeias de L (separadas por vírgula; λ = vazia)", "ab, abba, λ")
        else:
            texto_l = st.text_input("Expressão regular", "(ab)*")
    try:
        alfabeto = Alfabeto.de_texto(texto_alfabeto)
        if modo == "Enumeração":
            linguagem = Linguagem(alfabeto, cadeias=[c.strip() for c in texto_l.split(",") if c.strip()])
        else:
            linguagem = Linguagem(alfabeto, regex=texto_l)
    except Exception as erro:  # definição inválida digitada pelo usuário
        st.error(f"Definição inválida: {erro}")
        return

    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Σ", str(alfabeto))
    m2.metric("Tamanho |w|", alfabeto.tamanho(cadeia))
    m3.metric("Concatenação", exibir(alfabeto.concatenar(cadeia, segunda)))
    if alfabeto.valida(cadeia):
        st.success(f"Cadeia **{exibir(cadeia)}** válida para Σ (pertence a Σ*).")
    else:
        erros = ", ".join(f"'{s}' na posição {i + 1}" for i, s in alfabeto.simbolos_invalidos(cadeia))
        st.error(f"Cadeia inválida para Σ: {erros}.")
    if not alfabeto.valida(segunda):
        st.warning("A segunda cadeia tem símbolos fora de Σ; a concatenação foi feita mesmo assim.")
    simbolo = "∈" if linguagem.pertence(cadeia) else "∉"
    st.info(f"L = {linguagem}  →  **{exibir(cadeia)} {simbolo} L**")

    estrela = [exibir(w) for w in alfabeto.sigma_estrela(tamanho_max)]
    mais = [exibir(w) for w in alfabeto.sigma_mais(tamanho_max)]
    st.markdown(f"**Σ\\*** até tamanho {tamanho_max} ({len(estrela)} cadeias)")
    st.code("{" + ", ".join(estrela) + ", ...}", language=None)
    st.markdown(f"**Σ+** até tamanho {tamanho_max} ({len(mais)} cadeias)")
    st.code("{" + ", ".join(mais) + ", ...}", language=None)
    if not linguagem.finita:
        st.markdown(f"**Cadeias de L** até tamanho {tamanho_max}")
        st.code("{" + ", ".join(exibir(w) for w in linguagem.enumerar(tamanho_max)) + "}", language=None)


def aba_automato_finito() -> None:
    st.subheader("Módulo 2 — Autômato Finito (AFD / AFN)")
    dados = carregar_definicao("autômato", ("afd", "afn"), "af")
    if dados is None:
        return
    try:
        af = AutomatoFinito.de_dict(dados)
    except Exception as erro:
        st.error(f"Autômato inválido: {erro}")
        return
    cadeia = ler_cadeia("Cadeia de entrada", "ab", "af_cadeia")
    resultado = af.simular(cadeia)
    passo = controle_de_passo(f"af_passo_{af.nome}_{cadeia}", len(resultado.passos))

    ativos = resultado.estados_iniciais if passo == 0 else resultado.passos[passo - 1].destino
    visitados = set(resultado.estados_iniciais)
    for p in resultado.passos[:passo]:
        visitados |= p.destino

    esquerda, direita = st.columns([3, 2])
    with esquerda:
        st.caption(f"{af.nome} — **{af.tipo}** · estados ativos em amarelo, já visitados em azul")
        st.graphviz_chart(af.para_dot(ativos, visitados), width="stretch")
    with direita:
        st.markdown("**Entrada**")
        desenhar_entrada(cadeia, passo)
        st.markdown(f"**Estados ativos:** {formatar_conjunto(ativos)}")
        linhas = [{"Passo": 0, "Lê": "—", "De": "—", "Para": formatar_conjunto(resultado.estados_iniciais)}]
        linhas += [{"Passo": p.indice + 1, "Lê": p.simbolo, "De": formatar_conjunto(p.origem),
                    "Para": formatar_conjunto(p.destino)} for p in resultado.passos]
        st.dataframe(linhas[:passo + 1], hide_index=True, width="stretch")

    if passo == len(resultado.passos):
        st.markdown(f"**Caminho:** `{resultado.caminho_texto()}`")
        selo(resultado.aceita, resultado.motivo)
    if not af.deterministico:
        with st.expander("AFD equivalente (construção de subconjuntos)"):
            afd = af.para_afd()
            st.graphviz_chart(afd.para_dot(), width="stretch")
            st.caption(f"{len(afd.estados)} estados no AFD para {len(af.estados)} no AFN.")


def aba_glc() -> None:
    st.subheader("Módulo 3 — Gramática Livre de Contexto")
    modo = st.radio("Como definir a gramática", ["Digitar produções", "Arquivo JSON"], horizontal=True)
    try:
        if modo == "Digitar produções":
            texto = st.text_area("Produções (uma variável por linha; use | para alternativas e λ para vazio)",
                                 "S -> aSb | λ", height=110)
            g = Gramatica.de_texto(texto)
        else:
            dados = carregar_definicao("gramática", ("glc",), "glc")
            if dados is None:
                return
            g = Gramatica.de_dict(dados)
    except Exception as erro:
        st.error(f"Gramática inválida: {erro}")
        return

    st.markdown(f"**V** = {{{', '.join(g.variaveis)}}} · **T** = {{{', '.join(g.terminais)}}} · "
                f"**símbolo inicial** = {g.inicial}")
    cadeia = ler_cadeia("Cadeia de entrada", "aaabbb", "glc_cadeia")
    resultado = g.reconhecer(cadeia)
    selo(resultado.aceita, resultado.motivo)
    if not resultado.aceita:
        return
    esquerda, direita = st.columns(2)
    with esquerda:
        st.markdown("**Derivação passo a passo (mais à esquerda)**")
        st.dataframe([{"Passo": i, "Forma sentencial": p.forma, "Produção aplicada": p.producao or "—"}
                      for i, p in enumerate(resultado.derivacao)], hide_index=True, width="stretch")
        st.code(resultado.derivacao_texto(), language=None)
    with direita:
        st.markdown("**Árvore de derivação**")
        st.graphviz_chart(Gramatica.arvore_dot(resultado.arvore))
        st.caption("Azul: variáveis · amarelo: terminais · cinza: λ")


def aba_ap() -> None:
    st.subheader("Módulo 4 — Autômato com Pilha")
    dados = carregar_definicao("autômato com pilha", ("ap",), "ap")
    if dados is None:
        return
    try:
        ap = AutomatoPilha.de_dict(dados)
    except Exception as erro:
        st.error(f"Autômato inválido: {erro}")
        return
    cadeia = ler_cadeia("Cadeia de entrada", "aabb", "ap_cadeia")
    resultado = ap.simular(cadeia)
    total = len(resultado.passos) - 1
    passo = controle_de_passo(f"ap_passo_{ap.nome}_{cadeia}", total)
    atual = resultado.passos[passo]

    esquerda, meio, direita = st.columns([3, 1, 3])
    with esquerda:
        st.caption(f"{ap.nome} · rótulo das setas: leitura, topo / empilha")
        st.graphviz_chart(ap.para_dot(atual.estado), width="stretch")
    with meio:
        st.markdown("**Pilha**")
        desenhar_pilha(atual.pilha)
    with direita:
        st.markdown("**Entrada**")
        desenhar_entrada(cadeia, len(cadeia) - len(atual.restante))
        st.markdown(f"**Estado:** `{atual.estado}`  \n**Transição:** `{atual.acao}`")
    st.dataframe([{"Passo": i, "Leitura": p.leitura, "Estado": p.estado,
                   "Pilha (topo à esquerda)": p.pilha_texto(), "Entrada restante": exibir(p.restante),
                   "Transição": p.acao} for i, p in enumerate(resultado.passos[:passo + 1])],
                 hide_index=True, width="stretch")
    if passo == total:
        selo(resultado.aceita, resultado.motivo)


def aba_turing() -> None:
    st.subheader("Módulo 5 — Máquina de Turing")
    opcoes = {
        "Opção A — reconhecer L = { w#w }": (MaquinaTuring.w_hash_w, "ab#ab"),
        "Opção B — soma em unário (000100 = 3 + 2)": (MaquinaTuring.soma_unaria, "000100"),
        "Outra máquina (JSON)": (None, "000100"),
    }
    escolha = st.radio("Máquina", list(opcoes), horizontal=True)
    construtor, padrao = opcoes[escolha]
    try:
        if construtor is None:
            dados = carregar_definicao("máquina de Turing", ("mt",), "mt")
            if dados is None:
                return
            mt = MaquinaTuring.de_dict(dados)
        else:
            mt = construtor()
    except Exception as erro:
        st.error(f"Máquina inválida: {erro}")
        return
    st.caption(mt.descricao)
    entrada = ler_cadeia("Conteúdo inicial da fita", padrao, f"mt_entrada_{escolha}")
    resultado = mt.executar(entrada, limite=5000)
    total = len(resultado.passos) - 1
    passo = controle_de_passo(f"mt_passo_{mt.nome}_{entrada}", total)
    atual = resultado.passos[passo]

    st.markdown("**Fita**")
    desenhar_fita(atual.fita, atual.cabeca)
    c1, c2, c3 = st.columns(3)
    c1.metric("Estado atual", atual.estado)
    c2.metric("Passo", f"{passo} de {total}")
    c3.metric("Posição da cabeça", atual.cabeca)
    st.markdown(f"**Transição aplicada:** `{atual.acao}`")
    if passo == total:
        selo(resultado.aceita, resultado.motivo)
        st.markdown(f"**Fita final:** `{exibir(resultado.saida)}`"
                    + (f" → resultado da soma = **{len(resultado.saida)}**"
                       if construtor is MaquinaTuring.soma_unaria and resultado.aceita else ""))
    with st.expander("Diagrama de estados e função de transição"):
        st.graphviz_chart(mt.para_dot(atual.estado), width="stretch")
        st.code("\n".join(mt.tabela_transicoes()), language=None)


@st.cache_data
def _medicao() -> list[dict]:
    return medir()


def aba_complexidade() -> None:
    st.subheader("Módulo 6 — Complexidade Computacional")
    st.markdown("Análise assintótica dos algoritmos do simulador. "
                "**n** = tamanho da entrada, **|Q|** = nº de estados, **k** = |Σ|.")
    st.dataframe([{"Módulo": a.modulo, "Algoritmo": a.algoritmo, "Melhor caso (Ω)": a.melhor,
                   "Caso médio (Θ)": a.medio, "Pior caso (O)": a.pior, "Espaço": a.espaco}
                  for a in ANALISE], hide_index=True, width="stretch")
    with st.expander("Justificativa de cada análise"):
        for a in ANALISE:
            st.markdown(f"**{a.algoritmo}** — {a.justificativa}")

    st.markdown("#### Medição empírica")
    st.caption("Operações contadas pelo próprio simulador para entradas cada vez maiores. "
               "Dobrar n dobra as curvas lineares e quadruplica as quadráticas.")
    linhas = _medicao()
    st.dataframe([{COLUNAS_MEDICAO[c]: v for c, v in linha.items()} for linha in linhas],
                 hide_index=True, width="stretch")
    st.line_chart({COLUNAS_MEDICAO[c]: [linha[c] for linha in linhas] for c in COLUNAS_MEDICAO if c != "n"},
                  x_label="índice da medição (n = 2, 4, 8, 16, 32, 64)", y_label="operações")


# ---------------------------------------------------------------------- #
st.title("Simulador de Linguagens Formais e Modelos Computacionais")
st.caption("Aspectos Teóricos da Computação · Projeto prático em dupla")

abas = st.tabs(["1 · Linguagens", "2 · Autômato Finito", "3 · GLC",
                "4 · Autômato com Pilha", "5 · Máquina de Turing", "6 · Complexidade"])
for aba, funcao in zip(abas, [aba_linguagens, aba_automato_finito, aba_glc,
                              aba_ap, aba_turing, aba_complexidade]):
    with aba:
        funcao()
