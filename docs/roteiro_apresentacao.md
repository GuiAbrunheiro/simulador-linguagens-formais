# Roteiro da apresentação (10 minutos)

Deixe o app aberto antes de começar: `streamlit run app.py`. Como plano B, `python main.py --demo` mostra tudo no terminal.

| Tempo | O que mostrar | O que falar |
|---|---|---|
| 0:00 – 1:00 | Tela inicial com as 6 abas | Problema (ferramenta para estudar Teoria da Computação), arquitetura em duas camadas: núcleo `simulador/` sem entrada/saída + duas interfaces (console e Streamlit). |
| 1:00 – 2:15 | **Aba 1 – Linguagens.** Σ = {a, b}, cadeia `abba`. Depois troque para `abca`. | Validação símbolo a símbolo, tamanho, concatenação. Σ* é infinito, por isso listamos até um tamanho m. Mostrar L por enumeração e por expressão regular. |
| 2:15 – 3:45 | **Aba 2 – Autômato Finito.** `afd_ab.json` com `ab`, arrastando o passo. Depois `afn_termina_ab.json` com `aab`. | No AFD há sempre 1 estado ativo; no AFN acompanhamos o conjunto de estados. Abrir "AFD equivalente" e comentar a construção de subconjuntos. |
| 3:45 – 5:00 | **Aba 3 – GLC.** `S -> aSb | λ` com `aaabbb`; depois `aab` (rejeita). | Usamos o algoritmo de Earley, que aceita qualquer GLC. Mostrar a derivação mais à esquerda e a árvore. |
| 5:00 – 6:15 | **Aba 4 – AP.** `ap_anbn.json` com `aabb`, passo a passo. Depois `aab`. | Empilha um A para cada a, desempilha um para cada b. Mostrar a pilha crescendo e esvaziando; na rejeição, onde o autômato travou. |
| 6:15 – 8:00 | **Aba 5 – MT.** Opção A com `ab#ab` (arrastar o passo); Opção B com `000100`. | Opção A: marca com X e vai e volta na fita. Opção B: troca o 1 por 0 e apaga o último 0. Fizemos as duas opções. |
| 8:00 – 9:30 | **Aba 6 – Complexidade.** Tabela e gráfico. | AFD Θ(n); AFN O(n·|Q|²); Earley O(n³); MT w#w Θ(n²) com exatamente 2(|w|+1)² transições; soma Θ(n). O gráfico confirma: dobrar n dobra as lineares e quadruplica as quadráticas. |
| 9:30 – 10:00 | Terminal com `pytest` | 61 testes que comparam cada simulador com a definição da linguagem em todas as cadeias curtas. Encerrar e abrir para perguntas. |

## Perguntas prováveis

- **Por que Earley e não CYK?** O CYK exige a gramática na Forma Normal de Chomsky; a árvore sairia da gramática convertida, não da que o usuário digitou. Earley trabalha direto na gramática original e tem o mesmo pior caso O(n³).
- **Como o AFN é simulado sem "adivinhar" o caminho?** Guardando o conjunto de todos os estados possíveis após cada símbolo (é a construção de subconjuntos feita sob demanda).
- **O AP pode entrar em laço?** Pode, se houver ciclo de transições λ que só empilha. Por isso a busca em largura tem um limite de configurações.
- **Por que a MT de w#w é quadrática?** Para cada símbolo de w a cabeça atravessa a fita até a outra metade e volta. Com uma fita só não dá para fazer melhor que isso por comparação direta.
- **O que acontece se a MT não tiver transição?** Ela para e rejeita (convenção usual); também há um limite de passos para detectar laço infinito.
