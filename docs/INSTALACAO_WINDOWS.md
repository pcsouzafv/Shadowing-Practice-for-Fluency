# Instalacao no Windows

Guia de implantacao do `Shadowing Practice for Fluency` em Windows 10/11 com foco comercial.

## Recomendacao

Para clientes e ambientes de producao leve, padronize a instalacao com `Docker Desktop`.

Vantagens:

- reduz variacao entre maquinas
- ja inclui `ffmpeg` dentro do container
- simplifica suporte e atualizacao
- evita dependencia de `bash` no Windows

Use instalacao Python local apenas para demonstracao tecnica, testes internos ou suporte.

## Opcao 1: Docker Desktop no Windows

### 1. Pre-requisitos

Instale no Windows:

- `Docker Desktop`
- `WSL 2` habilitado no Docker Desktop
- navegador Chrome ou Edge

Requisitos recomendados de maquina:

- 8 GB de RAM no minimo
- 15 GB livres em disco

### 2. Copiar a aplicacao para a maquina

Sugestao de pasta:

```powershell
mkdir C:\ShadowingPractice
```

Copie o projeto inteiro para dentro dessa pasta.

Evite instalar em pasta sincronizada por OneDrive durante a operacao comercial.

### 3. Criar o arquivo de configuracao

No PowerShell, dentro da pasta do projeto:

```powershell
cd "C:\ShadowingPractice\Shadowing Practice for Fluency"
Copy-Item .env.example .env
notepad .env
```

### 4. Configuracao minima recomendada no `.env`

Para uma instalacao comercial basica, use este perfil:

```env
DATABASE_URL=disabled
WHATSAPP_ENABLED=0
```

Observacoes:

- `DATABASE_URL=disabled` desliga a camada adaptativa com Postgres. Isso simplifica bastante a instalacao inicial.
- `WHATSAPP_ENABLED=0` mantem o modulo WhatsApp desligado na aplicacao.
- Se nao for usar Ollama local, pode deixar `OLLAMA_ENABLED=0`.

### 5. Subir os containers

Ainda no PowerShell:

```powershell
docker compose up -d --build
```

O `docker-compose.yml` atual sobe estes servicos:

- `shadowing-practice`
- `evolution-api`
- `evolution-db`

Mesmo com `WHATSAPP_ENABLED=0`, os containers da Evolution sobem porque fazem parte do compose atual.

### 6. Validar a instalacao

Verifique se os containers ficaram no ar:

```powershell
docker compose ps
```

Veja os logs da aplicacao:

```powershell
docker compose logs -f shadowing-practice
```

Abra no navegador:

- `http://localhost:5000`
- `http://localhost:5000/api/status`

### 7. Como ligar novamente depois

```powershell
docker compose start
```

Para parar:

```powershell
docker compose stop
```

### 8. Como atualizar para uma nova versao

Substitua os arquivos do projeto e rode:

```powershell
docker compose down
docker compose up -d --build
```

### 9. Backup recomendado

Guarde copia destes itens:

- `.env`
- pasta `data\`
- pasta `static\audio\`

## Opcao 2: Python local no Windows

Use este modo apenas quando voce quiser rodar sem Docker.

### 1. Pre-requisitos

Instale:

- `Python 3.12`
- `FFmpeg` no `PATH` do Windows

Na instalacao do Python, marque a opcao `Add Python to PATH`.

### 2. Criar o `.env`

No PowerShell:

```powershell
cd "C:\ShadowingPractice\Shadowing Practice for Fluency"
Copy-Item .env.example .env
notepad .env
```

Configuracao minima recomendada:

```env
DATABASE_URL=disabled
WHATSAPP_ENABLED=0
```

### 3. Executar com o atalho do projeto

Rode:

```powershell
.\run_windows.bat
```

Esse arquivo:

- cria `.venv` se ainda nao existir
- instala dependencias
- cria `.env` automaticamente se ele estiver ausente
- inicia a aplicacao

### 4. Validar a aplicacao

Abra:

- `http://localhost:5000`
- `http://localhost:5000/api/status`

## Quando usar Postgres adaptativo

So configure `DATABASE_URL` se voce realmente precisar da integracao adaptativa com Postgres.

### Exemplo para Python local

```env
DATABASE_URL=postgresql://idiomasbr:idiomasbr123@localhost:5433/idiomasbr
```

### Exemplo para Docker Desktop no Windows

```env
DATABASE_URL=postgresql://idiomasbr:idiomasbr123@host.docker.internal:5433/idiomasbr
```

No Docker, `localhost` aponta para dentro do container. Por isso, se o banco estiver no host Windows, use `host.docker.internal`.

## Quando usar WhatsApp

Se for comercializar o modulo de mini-aulas no WhatsApp, ajuste no `.env`:

```env
WHATSAPP_ENABLED=1
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=troque-esta-chave
EVOLUTION_INSTANCE=shadowing
EVOLUTION_SERVER_URL=https://seu-dominio-publico
```

Para uso real, `EVOLUTION_SERVER_URL` deve apontar para uma URL publica valida.

## Quando usar Ollama no host Windows

Se o Ollama estiver instalado no Windows host e a aplicacao rodar via Docker:

```env
OLLAMA_ENABLED=1
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

Se nao usar Ollama, deixe:

```env
OLLAMA_ENABLED=0
```

## Checklist de entrega comercial

Antes de entregar ao cliente, valide:

- a aplicacao abre em `http://localhost:5000`
- `GET /api/status` responde sem erro HTTP
- o `.env` esta preenchido com as chaves corretas
- o Windows Firewall nao esta bloqueando a porta usada
- a pasta `data\` esta com permissao de escrita
- a pasta `static\audio\` esta com permissao de escrita
- existe rotina de backup do `.env`, `data\` e `static\audio\`

## Solucao rapida de problemas

### Porta 5000 ocupada

Altere a publicacao de porta no `docker-compose.yml` ou finalize o processo que esta usando `5000`.

### O status mostra erro de banco

Se voce nao usa Postgres adaptativo, deixe no `.env`:

```env
DATABASE_URL=disabled
```

### Ollama nao responde no Docker

Use:

```env
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

### O app abre, mas audio/WhatsApp falham no modo Python local

Confirme se o `FFmpeg` esta instalado no Windows e visivel no `PATH`.
