# Ferramentas e Operacao

Este guia separa o que ja existe dentro da aplicacao do que e opcional fora dela.

## 1. Ferramentas Nativas do Sistema

### 1.1 Treino e audio

- `Gerar Sessao` para criar audio e frases
- controle de velocidade (`0.5x` a `1.5x`)
- loop automatico para repeticao
- gravacao e comparacao no proprio app

### 1.2 Analise inteligente

- `Analisar com IA` para diagnostico de pronuncia, ritmo e vocabulario
- `Gerar + Analisar` para fluxo rapido em uma acao

### 1.3 Conversacao

- conversa por voz com STT local
- colinha opcional de respostas
- `Aula Inteligente` (foco automatico)
- `Aula de Correcao` (foco em erros e estrutura)

### 1.4 YouTube Karaoke Lab

- extracao de transcricao com multiplos fallbacks
- karaoke sincronizado palavra a palavra
- estudo frase por frase com traducao

### 1.5 Progresso

- log de sessoes
- historico de pratica
- exportacao CSV

## 2. Stack Tecnica (resumo)

| Camada | Recursos |
|---|---|
| Web | Flask + frontend JS |
| TTS | LMNT, Deepgram, Piper local |
| STT | faster-whisper local + fallbacks de audio |
| IA textual | DeepSeek, OpenRouter, OpenAI, Ollama |
| Video | YouTube + `youtube-transcript-api` + `yt-dlp` |

## 3. Comandos Operacionais

### Rodar local

```bash
./run.sh
```

### Rodar com Docker

```bash
docker compose up -d --build
```

### Ver status de provedores

```bash
curl -sS http://127.0.0.1:5000/api/status
```

### Logs do container

```bash
docker compose logs -f
```

### Limpeza de audios em cache (API)

```bash
curl -X POST http://127.0.0.1:5000/api/cleanup
```

## 4. Variaveis de Ambiente Essenciais

| Variavel | Uso |
|---|---|
| `LMNT_API_KEY` | TTS LMNT |
| `DEEPSEEK_API_KEY` | IA textual |
| `OPENROUTER_API_KEY` | IA textual + audio fallback |
| `OPENAI_API_KEY` | IA textual + transcricao fallback |
| `DEEPGRAM_API_KEY` | STT/TTS Deepgram |
| `LOCAL_WHISPER_ENABLED` | Ativa STT local para conversa |
| `PIPER_ENABLED` | Ativa TTS local offline |
| `OLLAMA_ENABLED` | Ativa IA local como ultimo fallback |

## 5. Ferramentas Externas Opcionais

- Audacity (inspecao de audio)
- Anki (revisao de vocabulario)
- Planilha (analise extra de progresso)

Use apenas como complemento. O fluxo principal ja pode ser feito todo no sistema.
