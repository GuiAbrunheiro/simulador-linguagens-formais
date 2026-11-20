# Simulador de Linguagens Formais e Modelos Computacionais

Projeto prático em dupla da disciplina **Aspectos Teóricos da Computação** (UNIFOR) — parte da nota da AV3.

**Dupla**

| Nome | Matrícula |
|---|---|
| Guilherme Abrunheiro de Souza | 2410417 |
| Matheus Maciel Holanda | 2015023 |

Ferramenta educacional que modela, valida e simula, passo a passo, os principais modelos da Teoria da Computação:

| Módulo | O que faz |
|---|---|
| 1. Linguagens Formais | Define Σ e L, valida cadeias, calcula Σ\*, Σ+, tamanho e concatenação |
| 2. Autômato Finito | Simula AFD e AFN (com transições λ) carregados de JSON; converte AFN → AFD |
| 3. Gramática Livre de Contexto | Reconhece cadeias (algoritmo de Earley), mostra a derivação e a árvore |
| 4. Autômato com Pilha | Simula APs (inclusive não determinísticos) mostrando leitura, estado e pilha |
| 5. Máquina de Turing | **Opção A** (L = { w#w }) **e Opção B** (soma em unário), com a fita a cada passo |
| 6. Complexidade | Análise em O, Ω e Θ de cada algoritmo + medição empírica |

Há duas interfaces sobre o mesmo núcleo: **console** e **web (Streamlit)**, esta última com a visualização dos estados dos autômatos, da pilha do AP e da fita da Máquina de Turing (item bônus).

## Como executar

Requisitos: **Python 3.10 ou superior**.

```bash
git clone https://github.com/GuiAbrunheiro/simulador-linguagens-formais.git
cd simulador-linguagens-formais
```

### Console (não precisa instalar nada)

```bash
python main.py           # menu interativo
python main.py --demo    # roda todos os exemplos do enunciado de uma vez
```

### Interface gráfica (Streamlit)

```bash
pip install -r requirements.txt
streamlit run app.py
```

O navegador abre em `http://localhost:8501`. Cada módulo fica em uma aba, e o controle **Passo da execução** avança e volta a simulação.

### Testes

```bash
pip install -r requirements.txt
pytest
```

São 61 testes. Além dos exemplos do enunciado, eles comparam cada simulador com a definição matemática da linguagem em **todas** as cadeias até um certo tamanho (por exemplo, a MT de `w#w` é conferida em todas as 3.280 cadeias sobre {a, b, #} de tamanho até 7).

## Estrutura do projeto

```
simulador-linguagens-formais/
├── main.py                  # interface de console
├── app.py                   # interface web (Streamlit)
├── simulador/               # núcleo: lógica pura, sem entrada/saída
│   ├── linguagens.py        # Módulo 1 - Alfabeto e Linguagem
│   ├── automato_finito.py   # Módulo 2 - AFD / AFN
│   ├── glc.py               # Módulo 3 - Gramática (Earley)
│   ├── automato_pilha.py    # Módulo 4 - Pilha e AP
│   ├── turing.py            # Módulo 5 - Máquina de Turing
│   └── complexidade.py      # Módulo 6 - análise e medição
├── exemplos/                # definições em JSON prontas para carregar
├── tests/                   # testes automatizados (pytest)
└── docs/                    # documento técnico, diagramas e roteiro
```

## Exemplos de entrada e saída

Todas as saídas abaixo foram copiadas de `python main.py --demo`.

### Módulo 1 — Linguagens Formais

Entrada: Σ = {a, b}, cadeia `abba`, segunda cadeia `ab`, L = {λ, ab, abba}.

```
Σ = {a, b}
Entrada: abba
Cadeia válida para Σ
Tamanho = 4
Concatenação: abba · ab = abbaab
Σ* (até tamanho 2, 7 cadeias) = {λ, a, b, aa, ab, ba, bb, ...}
Σ+ (até tamanho 2, 6 cadeias) = {a, b, aa, ab, ba, bb, ...}
L = {λ, ab, abba}
abba ∈ L
```

### Módulo 2 — Autômato Finito

Entrada: o autômato em JSON (`exemplos/afd_ab.json`) e a cadeia `ab`.

```json
{
  "nome": "AFD do enunciado: aceita apenas 'ab'",
  "estados": ["q0", "q1", "q2"],
  "alfabeto": ["a", "b"],
  "inicial": "q0",
  "finais": ["q2"],
  "transicoes": [
    {"de": "q0", "simbolo": "a", "para": "q1"},
    {"de": "q1", "simbolo": "b", "para": "q2"}
  ]
}
```

```
Entrada: ab
Passo a passo:
  1. δ(q0, a) = q1
  2. δ(q1, b) = q2
Caminho: q0 -> q1 -> q2
ACEITA
```

Em um AFN, `"para"` pode ser uma lista (`["q0", "q1"]`) e `"simbolo"` pode ser `"λ"`. Saída para `exemplos/afn_termina_ab.json` com a cadeia `aab`:

```
Passo a passo:
  0. início (com fecho-λ): {q0}
  1. lê 'a': {q0} -> {q0, q1}
  2. lê 'a': {q0, q1} -> {q0, q1}
  3. lê 'b': {q0, q1} -> {q0, q2}
Caminho: q0 -> q0 -> q1 -> q2
ACEITA
```

### Módulo 3 — Gramática Livre de Contexto

Entrada: produções `S -> aSb | λ` (digitadas ou em `exemplos/glc_anbn.json`) e a cadeia `aaabbb`.

```
Derivação passo a passo (mais à esquerda):
    S
  ⇒ aSb   [S -> aSb]
  ⇒ aaSbb   [S -> aSb]
  ⇒ aaaSbbb   [S -> aSb]
  ⇒ aaabbb   [S -> λ]
Árvore de derivação:
  S
  ├── a
  ├── S
  │   ├── a
  │   ├── S
  │   │   ├── a
  │   │   ├── S
  │   │   │   └── λ
  │   │   └── b
  │   └── b
  └── b
ACEITA
```

Para a cadeia `aab` a saída é `REJEITA`.

### Módulo 4 — Autômato com Pilha

Entrada: AP de L = { aⁿbⁿ | n ≥ 1 } (`exemplos/ap_anbn.json`) e a cadeia `aabb`.

```
  Passo Leitura  Estado  Pilha (topo à esq.)   Restante    Transição
  0     -        q0      Z                     aabb        configuração inicial
  1     a        q0      AZ                    abb         δ(q0, a, Z) = (q0, AZ)
  2     a        q0      AAZ                   bb          δ(q0, a, A) = (q0, AA)
  3     b        q1      AZ                    b           δ(q0, b, A) = (q1, λ)
  4     b        q1      Z                     λ           δ(q1, b, A) = (q1, λ)
  5     λ        qf      Z                     λ           δ(q1, λ, Z) = (qf, Z)
ACEITA
```

Para `aab`: `REJEITA (Nenhuma computação aceita: o autômato trava em q1 com entrada restante 'λ' e pilha AZ.)`

### Módulo 5 — Máquina de Turing

**Opção A** — entrada `ab#ab` (trecho; a execução completa tem 18 transições):

```
  Passo Estado    Fita (cabeça entre colchetes)
  0     q0         _ [a] b  #  a  b  _
  1     qa         _  X [b] #  a  b  _
  2     qa         _  X  b [#] a  b  _
  3     qa2        _  X  b  # [a] b  _
  4     qvolta     _  X  b [#] X  b  _
  ...
  18    qaceita    _  X  X  #  X  X [_] _
Total de transições: 18
ACEITA
```

**Opção B** — entrada `000100` (3 + 2):

```
  Passo Estado    Fita (cabeça entre colchetes)
  0     q0         _ [0] 0  0  1  0  0  _
  ...
  14    qaceita    _ [0] 0  0  0  0  _
Total de transições: 14
Fita final: 00000
ACEITA
```

### Módulo 6 — Complexidade

Resumo (a análise completa, com justificativas, está no documento técnico e na opção 6 do menu):

| Algoritmo | Melhor caso | Caso médio | Pior caso |
|---|---|---|---|
| Validar cadeia em Σ | Ω(1) | Θ(n) | O(n) |
| Enumerar Σ\* até tamanho m | Ω(m·kᵐ) | Θ(m·kᵐ) | O(m·kᵐ) |
| Simulação de AFD | Ω(1) | Θ(n) | O(n) |
| Simulação de AFN | Ω(1) | Θ(n·\|Q\|²) | O(n·\|Q\|²) |
| Conversão AFN → AFD | Ω(\|Q\|·k) | — | O(2^\|Q\|·k·\|Q\|²) |
| GLC — Earley | Ω(n) | Θ(n²) (não ambígua) | O(n³) |
| AP — busca em largura | Ω(n) | Θ(n²) (determinístico) | exponencial |
| MT Opção A (w#w) | Ω(1) | Θ(n²) | O(n²) |
| MT Opção B (soma) | Ω(n) | Θ(n) | O(n) |

Medição empírica feita pelo próprio simulador (operações contadas, não tempo):

```
n     AFD   Earley aⁿbⁿ   Earley ambígua   AP aⁿbⁿ   MT w#w   MT soma
2     4     13            12               6         18       12
4     8     25            30               10        50       20
8     16    49            90               18        162      36
16    32    97            306              34        578      68
32    64    193           1122             66        2178     132
64    128   385           4290             130       8450     260
```

Dobrar n dobra as colunas lineares e quadruplica as quadráticas (MT w#w e Earley com a gramática ambígua `S -> SS | a`).

## Formato dos arquivos JSON

- **Autômato finito:** `estados`, `alfabeto`, `inicial`, `finais`, `transicoes` (`de`, `simbolo`, `para`).
- **Gramática:** `variaveis`, `terminais`, `inicial`, `producoes` (`{"S": ["aSb", "λ"]}`).
- **Autômato com pilha:** além dos campos do autômato, `alfabeto_pilha`, `simbolo_inicial_pilha`, `aceitacao` (`estado_final`, `pilha_vazia` ou `ambos`) e transições com `de`, `leitura`, `topo`, `para`, `empilha` (o primeiro símbolo de `empilha` fica no topo).
- **Máquina de Turing:** `estados`, `alfabeto`, `alfabeto_fita`, `branco`, `inicial`, `aceitacao`, `rejeicao` e transições com `de`, `le`, `para`, `escreve`, `move` (`E`, `D` ou `P`).

A cadeia vazia pode ser escrita como `"λ"`, `"ε"` ou `""`. A pasta `exemplos/` traz um arquivo de cada tipo.

## Documentação

O documento técnico (introdução, fundamentação teórica, arquitetura com UML e casos de uso, implementação, complexidade e conclusão) está em [`docs/Documento_Tecnico.pdf`](docs/Documento_Tecnico.pdf). O roteiro da apresentação de 10 minutos está em [`docs/roteiro_apresentacao.md`](docs/roteiro_apresentacao.md).
