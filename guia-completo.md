# Guia Completo de Uso

Guia pratico para usar todas as funcoes da aplicacao de forma progressiva e com foco em resultado de fluencia.

## 1. Como o Sistema Esta Organizado

A aplicacao combina cinco blocos:

1. `Treino de fala` (audio + repeticao + gravacao)
2. `Analise inteligente` (feedback de pronuncia e estrutura)
3. `Conversacao por voz` (simulacao de dialogo real)
4. `YouTube Lab` (material autentico com karaoke)
5. `Progresso` (registro e metricas)

## 2. Mapa das Funcoes (o que existe no codigo)

| Funcao no produto | Endpoint principal | Resultado |
|---|---|---|
| Gerar sessao de shadowing | `POST /api/generate` | Audio + frases + videos relacionados |
| Gerar audio rapido | `POST /api/tts` | URL de audio para frase |
| Analise do texto | `POST /api/analyze` | Dicas de pronuncia, vocabulario, foco de shadowing |
| Texto de pratica por IA | `POST /api/generate-practice` | Texto sob medida por tema/tipo/tamanho |
| Conversacao por voz | `POST /api/conversation` | Transcricao do usuario + resposta IA + audio |
| Aula da conversa | `POST /api/conversation/lesson` | Resumo, transcricao traduzida, correcoes, gramatica, dicas |
| Karaoke YouTube | `POST /api/youtube-transcript` | Segmentos com timing para sincronia |
| Estudo frase por frase | `POST /api/youtube-transcript-study` | Traducao, vocabulario e explicacoes por trecho |
| Progresso | `GET/POST /api/progress` | Registro de desempenho |
| Exportacao de dados | `GET /api/progress/export` | CSV pronto para analise |

## 3. Jornada Recomendada (30 minutos)

### Bloco A - Preparacao (5 min)

1. Escolha idioma e um texto curto
2. Gere sessao (`Gerar Sessao`)
3. Ajuste velocidade (0.75x a 1.0x)

### Bloco B - Producao (15 min)

1. Shadowing com texto
2. Shadowing sem texto
3. Grave e compare sua voz

### Bloco C - Diagnostico (5 min)

1. Clique em `Analisar com IA`
2. Escolha 1-2 pontos para corrigir hoje

### Bloco D - Conversacao (5 min)

1. Entre na aba `Conversar`
2. Fale por 2-4 turnos
3. Gere `Aula Inteligente` para consolidar erros e vocabulário

## 4. Aula Inteligente vs Aula de Correcao

| Botao | Quando usar | Resultado esperado |
|---|---|---|
| `Aula Inteligente` | Sessao geral, sem foco definido | O sistema escolhe foco automatico (`balanced`, `corrections`, `vocabulary`) |
| `Aula de Correcao` | Voce quer ajuste gramatical/pratico imediato | Mais itens de correcoes e gramatica, menos dispersao |

## 5. Como o Foco Inteligente e Decidido

Na aula de conversacao, o backend calcula foco automatico com base em sinais da fala do usuario, como:

- repeticoes excessivas
- frases muito fragmentadas
- padroes de pergunta mal formados
- mistura de idiomas no mesmo turno

Com isso, o retorno deixa de ser generico e prioriza o que mais impacta a proxima sessao.

## 6. Modos do YouTube Karaoke Lab

| Modo | Uso recomendado |
|---|---|
| `accuracy` | Melhor sincronia possivel (mais processamento) |
| `balanced` | Equilibrio entre velocidade e qualidade |
| `fast` | Carregamento rapido para exploracao inicial |

## 7. Idiomas na Pratica

- Conversacao e geracao de texto na UI: `en`, `pt`, `es`, `fr`, `de`, `it`
- Traducoes da aula: `pt`, `en`, `es`, `fr`, `de`, `it`
- TTS local offline (Piper): `en`, `pt`, `fr`, `es`, `de`

## 8. Padrao Diario de Evolucao

1. Uma sessao curta de shadowing
2. Uma analise objetiva
3. Uma micro-conversa por voz
4. Um registro no progresso

A consistencia diaria vale mais que sessoes longas e irregulares.
