#!/usr/bin/env bash
# ============================================================================
# setup-whatsapp.sh — Configuração completa do WhatsApp Mini-Aulas
# ============================================================================
# Uso:
#   chmod +x setup-whatsapp.sh
#   ./setup-whatsapp.sh
#
# Este script:
#   1. Instala o ngrok (se não instalado)
#   2. Sobe o Docker Compose com Evolution API + PostgreSQL
#   3. Configura a instância do Evolution API
#   4. Abre o QR Code no navegador para conectar o WhatsApp
#   5. Configura o webhook automaticamente
# ============================================================================

set -euo pipefail

# ── Cores ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${BLUE}ℹ${RESET}  $*"; }
success() { echo -e "${GREEN}✅${RESET} $*"; }
warn()    { echo -e "${YELLOW}⚠${RESET}  $*"; }
error()   { echo -e "${RED}❌${RESET} $*"; exit 1; }
step()    { echo -e "\n${BOLD}${BLUE}▶ $*${RESET}"; }

# ── Configurações ─────────────────────────────────────────────────────────────
EVOLUTION_API_KEY="${EVOLUTION_API_KEY:-changeme-secret-key}"
EVOLUTION_INSTANCE="${EVOLUTION_INSTANCE:-shadowing}"
APP_PORT=5000
EVOLUTION_PORT=8080
ENV_FILE=".env"

# ── Banner ────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}╔═══════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}║     🎓 Shadowing Practice — WhatsApp Setup            ║${RESET}"
echo -e "${BOLD}║     Mini-aulas estilo BeConfident via WhatsApp         ║${RESET}"
echo -e "${BOLD}╚═══════════════════════════════════════════════════════╝${RESET}"
echo ""

# ── Verificar requisitos ──────────────────────────────────────────────────────
step "Verificando requisitos..."

command -v docker >/dev/null    || error "Docker não encontrado. Instale em https://docker.com"
command -v docker-compose >/dev/null 2>&1 || command -v docker compose >/dev/null 2>&1 || \
    error "Docker Compose não encontrado."
command -v curl >/dev/null      || error "curl não encontrado. Instale com: apt install curl"
success "Docker e curl disponíveis."

# ── Instalar ngrok ──────────────────────────────────────────────────────────
step "Verificando ngrok..."

if ! command -v ngrok &>/dev/null; then
    warn "ngrok não encontrado. Instalando..."

    if command -v snap &>/dev/null; then
        sudo snap install ngrok
    elif [[ "$(uname)" == "Darwin" ]] && command -v brew &>/dev/null; then
        brew install ngrok/ngrok/ngrok
    else
        # Linux — download direto
        NGROK_URL="https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz"
        curl -sSL "$NGROK_URL" | tar xz -C /tmp
        sudo mv /tmp/ngrok /usr/local/bin/ngrok
    fi
    success "ngrok instalado!"
else
    success "ngrok já instalado: $(ngrok --version 2>/dev/null | head -1)"
fi

# ── Configurar .env ──────────────────────────────────────────────────────────
step "Configurando variáveis de ambiente..."

if [[ ! -f "$ENV_FILE" ]]; then
    warn ".env não encontrado. Criando um básico..."
    cat > "$ENV_FILE" << EOF
# WhatsApp Mini-Aulas
WHATSAPP_ENABLED=1
EVOLUTION_API_KEY=${EVOLUTION_API_KEY}
EVOLUTION_INSTANCE=${EVOLUTION_INSTANCE}
EVOLUTION_SERVER_URL=http://localhost:8080
EOF
    success ".env criado."
fi

# Verificar se WHATSAPP_ENABLED já existe no .env
if grep -q "^WHATSAPP_ENABLED=" "$ENV_FILE" 2>/dev/null; then
    # Atualizar para 1
    sed -i 's/^WHATSAPP_ENABLED=.*/WHATSAPP_ENABLED=1/' "$ENV_FILE"
else
    echo "" >> "$ENV_FILE"
    echo "# WhatsApp Mini-Aulas" >> "$ENV_FILE"
    echo "WHATSAPP_ENABLED=1" >> "$ENV_FILE"
    echo "EVOLUTION_API_KEY=${EVOLUTION_API_KEY}" >> "$ENV_FILE"
    echo "EVOLUTION_INSTANCE=${EVOLUTION_INSTANCE}" >> "$ENV_FILE"
fi
success ".env configurado (WHATSAPP_ENABLED=1)"

# ── Subir Docker Compose ──────────────────────────────────────────────────────
step "Iniciando Docker Compose (Evolution API + PostgreSQL + App)..."

# Detectar comando docker compose
if command -v docker-compose &>/dev/null; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

$COMPOSE_CMD up -d --build

echo ""
info "Aguardando Evolution API inicializar (~30s)..."
for i in $(seq 1 30); do
    if curl -sf "http://localhost:${EVOLUTION_PORT}/" > /dev/null 2>&1; then
        success "Evolution API online!"
        break
    fi
    printf "."
    sleep 1
done
echo ""

# ── Iniciar ngrok ─────────────────────────────────────────────────────────────
step "Iniciando ngrok para expor o webhook..."

# Parar ngrok anterior se existir
pkill -f "ngrok http ${APP_PORT}" 2>/dev/null || true
sleep 1

# Iniciar ngrok em background
ngrok http ${APP_PORT} --log=stdout > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!

echo ""
info "Aguardando ngrok..."
sleep 4

# Obter URL pública do ngrok
NGROK_URL=""
for i in $(seq 1 15); do
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | \
        python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    tunnels = d.get('tunnels', [])
    for t in tunnels:
        if t.get('proto') == 'https':
            print(t['public_url'])
            break
except:
    pass
" 2>/dev/null || true)

    if [[ -n "$NGROK_URL" ]]; then
        break
    fi
    printf "."
    sleep 1
done
echo ""

if [[ -z "$NGROK_URL" ]]; then
    error "Não foi possível obter a URL do ngrok. Verifique em http://localhost:4040"
fi

WEBHOOK_URL="${NGROK_URL}/whatsapp/webhook"
success "URL pública do ngrok: ${NGROK_URL}"
success "Webhook URL: ${WEBHOOK_URL}"

# Atualizar EVOLUTION_SERVER_URL no .env
sed -i "s|^EVOLUTION_SERVER_URL=.*|EVOLUTION_SERVER_URL=${NGROK_URL}|" "$ENV_FILE" || \
    echo "EVOLUTION_SERVER_URL=${NGROK_URL}" >> "$ENV_FILE"

# ── Configurar instância no Evolution API ────────────────────────────────────
step "Configurando instância '${EVOLUTION_INSTANCE}' no Evolution API..."

# Criar instância
CREATE_RESPONSE=$(curl -s -X POST \
    "http://localhost:${EVOLUTION_PORT}/instance/create" \
    -H "apikey: ${EVOLUTION_API_KEY}" \
    -H "Content-Type: application/json" \
    -d "{
        \"instanceName\": \"${EVOLUTION_INSTANCE}\",
        \"qrcode\": true,
        \"integration\": \"WHATSAPP-BAILEYS\",
        \"webhook\": {
            \"url\": \"${WEBHOOK_URL}\",
            \"byEvents\": false,
            \"base64\": false,
            \"events\": [\"QRCODE_UPDATED\", \"MESSAGES_UPSERT\", \"MESSAGES_UPDATE\", \"CONNECTION_UPDATE\"]
        }
    }" 2>/dev/null || echo '{}')

echo "Resposta: $CREATE_RESPONSE" | head -c 200
echo ""

# Configurar webhook
WEBHOOK_RESPONSE=$(curl -s -X POST \
    "http://localhost:${EVOLUTION_PORT}/webhook/set/${EVOLUTION_INSTANCE}" \
    -H "apikey: ${EVOLUTION_API_KEY}" \
    -H "Content-Type: application/json" \
    -d "{
        \"webhook\": {
            \"enabled\": true,
            \"url\": \"${WEBHOOK_URL}\",
            \"byEvents\": false,
            \"base64\": false,
            \"events\": [\"QRCODE_UPDATED\", \"MESSAGES_UPSERT\", \"MESSAGES_UPDATE\", \"CONNECTION_UPDATE\"]
        }
    }" 2>/dev/null || echo '{}')

success "Webhook configurado: ${WEBHOOK_URL}"

# ── QR Code ────────────────────────────────────────────────────────────────
step "Obtendo QR Code para conectar o WhatsApp..."

echo ""
echo -e "${BOLD}${YELLOW}📱 PRÓXIMOS PASSOS:${RESET}"
echo ""
echo -e "  1. Abra o link abaixo para ver o QR Code:"
echo -e "     ${BOLD}${BLUE}http://localhost:${EVOLUTION_PORT}/manager${RESET}"
echo ""
echo -e "  2. Ou acesse via API:"
echo -e "     ${BOLD}${BLUE}http://localhost:${APP_PORT}/whatsapp/qrcode${RESET}"
echo ""
echo -e "  3. No WhatsApp no seu celular:"
echo -e "     ${BOLD}WhatsApp > ⋮ > Aparelhos conectados > Conectar aparelho${RESET}"
echo -e "     Escaneie o QR Code."
echo ""
echo -e "  4. Após conectar, o bot estará ativo!"
echo -e "     Envie ${BOLD}'OI'${RESET} para o seu próprio número para testar."
echo ""
echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${BOLD}Status dos serviços:${RESET}"
echo -e "  App Flask:      http://localhost:${APP_PORT}"
echo -e "  Evolution API:  http://localhost:${EVOLUTION_PORT}"
echo -e "  ngrok UI:       http://localhost:4040"
echo -e "  Alunos:         http://localhost:${APP_PORT}/whatsapp/students"
echo -e "  Status WA:      http://localhost:${APP_PORT}/whatsapp/status"
echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
echo -e "${BOLD}Pressione Ctrl+C para parar o ngrok quando terminar.${RESET}"
echo ""

# Manter o ngrok rodando em foreground até Ctrl+C
wait $NGROK_PID
