# Shadowing Practice for Fluency

Plataforma de shadowing com foco em fluencia oral, pratica guiada por IA, conversacao por voz, estudo de transcricoes e acompanhamento de progresso.

## Visao Geral

O sistema foi desenhado para transformar pratica diaria em um fluxo completo:

1. gerar audio e texto sincronizado para repeticao
2. analisar pronuncia, ritmo e vocabulário
3. praticar conversacao em voz com parceiro de IA
4. transformar videos do YouTube em laboratorio de karaoke
5. registrar progresso e evolucao semanal

## Modulos da Aplicacao

| Modulo | O que faz |
|---|---|
| `Praticar` | Gera sessao de shadowing com TTS, karaoke de texto, loop e gravacao de voz |
| `IA Tools` | Gera textos de pratica por tema, nivel, tipo e foco |
| `Conversar` | Conversacao por voz + colinha + aula de conversacao com foco inteligente |
| `Progresso` | Log de sessoes, historico, exportacao CSV e metricas |
| `YouTube Karaoke Lab` | Extrai transcricao, sincroniza karaoke e gera estudo frase por frase |

## Idiomas Suportados

### Pela interface (UI)

- Pratica, IA Tools e Conversar: `en`, `pt`, `es`, `fr`, `de`, `it`
- YouTube Karaoke (idioma preferido de legenda): `en`, `pt`, `es`, `fr`
- Aula de conversacao (traducao): `pt`, `en`, `es`, `fr`, `de`, `it`

### Motores de voz (TTS)

- Piper local: `en`, `pt`, `es`, `fr`, `de`, `it`
- Deepgram Aura-2 (quando configurado): `en`, `es`, `fr`, `de`, `it`, `ja`, `nl`
- LMNT: depende das vozes disponiveis na conta

## Principais Funcoes (Back-end)

| Endpoint | Funcao |
|---|---|
| `POST /api/generate` | Gera sessao completa: audio + sentencas + videos relacionados |
| `POST /api/tts` | Gera audio para frase individual |
| `POST /api/analyze` | Analise inteligente do texto para shadowing |
| `POST /api/generate-practice` | Geracao de texto de pratica por parametros |
| `POST /api/videos` | Busca videos relacionados |
| `POST /api/youtube-transcript` | Extracao de transcricao para karaoke |
| `POST /api/youtube-transcript-study` | Estudo frase por frase com traducao e apoio de IA |
| `POST /api/conversation` | Conversacao por voz (STT -> resposta IA -> TTS) |
| `POST /api/conversation/lesson` | Aula da conversa (`smart`, `corrections`, `vocabulary`) |
| `GET /api/agent/intents` | Lista de intents da engenharia de agentes |
| `POST /api/agent/run` | Orquestrador multiagente (`practice`, `conversation`, `youtube`, `progress`, `auto`) |
| `GET/POST /api/progress` | Leitura e gravacao de progresso |
| `GET /api/progress/export` | Exportacao CSV |
| `GET /api/status` | Status de provedores e fallbacks |

## Engenharia de Agentes (novo)

Endpoint principal:

```bash
POST /api/agent/run
```

Payload base:

```json
{
  "intent": "auto",
  "query": "gerar texto de prática sobre entrevistas",
  "payload": {
    "action": "generate_practice_text",
    "topic": "job interview",
    "target_lang": "en",
    "level": "intermediate",
    "text_length": "medium",
    "text_type": "dialogue"
  }
}
```

Intents suportadas:

- `auto`: roteia automaticamente por query/payload
- `practice`: prática, análise, geração de texto
- `conversation`: conversa por voz e aula da conversa
- `youtube`: transcrição e estudo frase a frase
- `progress`: resumo/salvar progresso

## Estrategia de Fallback (Confiabilidade)

### IA textual

- ordem: `DeepSeek -> OpenRouter -> OpenAI -> Ollama local`
- se indisponivel: modo local basico para nao interromper o fluxo

### TTS

- por selecao de engine, com fallback automatico entre provedores
- fallback final: `Piper local` (offline)

### Piper mais natural

- O backend agora aplica uma camada contextual antes do Piper: limpeza de texto, pontuacao final, remocao opcional de labels de dialogo e presets de prosodia.
- Perfis disponiveis: `balanced`, `chat`, `lesson`, `story`, `question`, `expressive`
- Lexico editavel: `config/piper_pronunciations.json`
- Tuning por modelo/voz: `config/piper_voice_profiles.json`
- Frases de calibracao: `config/piper_calibration_phrases.json`
- Campos opcionais nas rotas que caem no Piper:
  - `piper_profile` ou `tts_style`
  - `length_scale`, `noise_scale`, `noise_w_scale`, `sentence_silence`, `volume`
  - `speaker_id`
  - `normalize_audio`
  - `piper_options` (objeto com os mesmos campos)

Exemplo rapido:

```bash
./tts_piper.sh --lang pt --profile chat "WhatsApp e YouTube funcionam melhor com contexto" /tmp/teste.wav
```

Calibracao em lote:

```bash
.venv/bin/python scripts/piper_calibrate.py --lang pt --limit 2
```

Todos os idiomas principais do projeto:

```bash
.venv/bin/python scripts/piper_calibrate.py --project-langs --profiles balanced,chat --limit 1 --skip-missing-models
```

### YouTube transcricao

- tentativas combinadas por modo (`accuracy`, `balanced`, `fast`)
- fontes possiveis: API de legenda, `yt-dlp`, `Deepgram`, `faster-whisper`, OpenRouter audio, OpenAI audio

## Início Rapido

### Windows

Para instalacao comercial no Windows, use o guia dedicado:

- [docs/INSTALACAO_WINDOWS.md](docs/INSTALACAO_WINDOWS.md)

### 1) Rodar local

```bash
chmod +x run.sh
./run.sh
```

Aplicacao em `http://127.0.0.1:5000`.

### 2) Rodar com Docker

```bash
docker compose up -d --build
```

Observacoes:

- A imagem da app passa a usar o nome `shadowing-practice:local` por padrao.
- `models/` e `config/` entram no container por volume read-only; ajustes de voz/tuning nao exigem rebuild da imagem.
- Rebuild com `--build` continua sendo necessario quando houver mudanca em codigo Python, `requirements.txt` ou `Dockerfile`.

Logs:

```bash
docker compose logs -f
```

### 3) Check rapido de saude

```bash
curl -sS http://127.0.0.1:5000/api/status
```

## Variaveis Relevantes (.env)

- `LMNT_API_KEY`
- `DEEPSEEK_API_KEY`
- `OPENROUTER_API_KEY`
- `OPENAI_API_KEY`
- `DEEPGRAM_API_KEY`
- `DEEPGRAM_ENABLED` (default `1`)
- `DATABASE_URL` (`disabled` desliga o Postgres adaptativo; em Docker no Windows use `host.docker.internal`)
- `LOCAL_WHISPER_ENABLED` (default `1`)
- `OLLAMA_ENABLED` (default `1`)
- `OLLAMA_BASE_URL` (default `http://127.0.0.1:11434`)
- `OLLAMA_MODEL` (opcional)
- `PIPER_ENABLED` (default `1`)

## Integracao com o sistema principal

- A camada adaptativa grava no mesmo Postgres do sistema principal, mas isolada no schema `shadowing_adaptive`.
- A resolucao opcional de identidade consulta `public.users` sem substituir o fluxo anonimo por `learner_key`.
- Para abrir a interface ja vinculada a um usuario do outro sistema, passe na URL:
  - `?user_id=123`
  - `?email=aluno@dominio.com`
  - `?phone=5511999999999`
  - opcional: `&source_system=idiomasbr`

## Fluxo Recomendado de Uso

1. Gere uma sessao no modulo `Praticar`
2. Use `Analisar com IA` para pontos de pronuncia e ritmo
3. Faca `Conversar` por voz por 5 a 10 minutos
4. Abra `Aula Inteligente` para feedback contextual
5. Salve a sessao em `Progresso`

## Documentacao do Projeto

- [docs/ARQUITETURA_SISTEMA_E_AGENTES.md](docs/ARQUITETURA_SISTEMA_E_AGENTES.md)
- [docs/INSTALACAO_WINDOWS.md](docs/INSTALACAO_WINDOWS.md)
- [guia-completo.md](guia-completo.md)
- [protocolo-sessao.md](protocolo-sessao.md)
- [plano-progressivo.md](plano-progressivo.md)
- [ferramentas.md](ferramentas.md)
- [dicas-avancadas.md](dicas-avancadas.md)
