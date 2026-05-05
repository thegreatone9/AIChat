#!/usr/bin/env bash
# ============================================================
#  AIChat — Single entry point to build & start all services
#  Usage:  ./start.sh
#
#  This script is fully self-contained. On a fresh clone it will:
#    1. Verify all prerequisites (Node.js, Python 3, Ollama)
#    2. Pull required Ollama models if missing
#    3. Create Python venv & install dependencies
#    4. Install Node.js dependencies for server & client
#    5. Kill any existing services on our ports
#    6. Start all 3 services in parallel
# ============================================================

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ---------- Colors ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log()  { echo -e "${CYAN}[AIChat]${NC} $1"; }
ok()   { echo -e "${GREEN}[  OK  ]${NC} $1"; }
warn() { echo -e "${YELLOW}[ WARN ]${NC} $1"; }
err()  { echo -e "${RED}[ERROR ]${NC} $1"; exit 1; }

# ============================================================
#  Prerequisites
# ============================================================
log "${BOLD}Checking prerequisites...${NC}"

command -v node   &>/dev/null || err "Node.js is not installed. Install from https://nodejs.org"
command -v npm    &>/dev/null || err "npm is not installed. It ships with Node.js — reinstall Node."
command -v python3 &>/dev/null || err "Python 3 is not installed. Install from https://python.org"
command -v ollama &>/dev/null || err "Ollama is not installed. Install from https://ollama.com"

NODE_V=$(node -v)
PY_V=$(python3 --version)
ok "Node.js $NODE_V, $PY_V, Ollama ✓"

# ============================================================
#  Ollama Models
# ============================================================
ensure_model() {
  local model=$1
  if ollama list 2>/dev/null | grep -q "^$model"; then
    ok "Ollama model '$model' ready"
  else
    log "Pulling Ollama model '$model' (first run only, may take a few minutes)..."
    ollama pull "$model"
    ok "Model '$model' pulled"
  fi
}

log "${BOLD}Checking Ollama models...${NC}"
ensure_model "qwen2.5:7b"
ensure_model "nomic-embed-text"

# ============================================================
#  Python Virtual Environment & Dependencies
# ============================================================
log "${BOLD}Setting up AI Services (Python)...${NC}"

AI_DIR="$ROOT_DIR/ai-services"
VENV_DIR="$AI_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
  log "Creating Python virtual environment..."
  python3 -m venv "$VENV_DIR"
  ok "Virtual environment created at $VENV_DIR"
fi

log "Installing Python dependencies..."
"$VENV_DIR/bin/pip" install -q --upgrade pip
"$VENV_DIR/bin/pip" install -q -r "$AI_DIR/requirements.txt"
ok "Python dependencies ready"

# ============================================================
#  Node.js Dependencies — Server
# ============================================================
log "${BOLD}Setting up Node.js Server...${NC}"

SERVER_DIR="$ROOT_DIR/server"
log "Installing server dependencies..."
(cd "$SERVER_DIR" && npm install --silent)
ok "Server dependencies ready"

# ============================================================
#  Node.js Dependencies — Client
# ============================================================
log "${BOLD}Setting up React Client...${NC}"

CLIENT_DIR="$ROOT_DIR/client"
log "Installing client dependencies..."
(cd "$CLIENT_DIR" && npm install --silent)
ok "Client dependencies ready"

# ============================================================
#  Kill existing processes on our ports
# ============================================================
kill_port() {
  local port=$1
  local pids
  pids=$(lsof -ti :"$port" 2>/dev/null || true)
  if [ -n "$pids" ]; then
    warn "Killing existing process(es) on port $port (PIDs: $pids)"
    echo "$pids" | xargs kill -9 2>/dev/null || true
    sleep 0.5
  fi
}

log "Clearing ports..."
kill_port 5173
kill_port 5000
kill_port 8000
ok "Ports cleared"

# ============================================================
#  Track child PIDs for cleanup on Ctrl+C
# ============================================================
PIDS=()

cleanup() {
  echo ""
  log "Shutting down all services..."
  for pid in "${PIDS[@]}"; do
    kill -0 "$pid" 2>/dev/null && kill "$pid" 2>/dev/null || true
  done
  kill_port 5173; kill_port 5000; kill_port 8000
  ok "All services stopped. Goodbye!"
  exit 0
}

trap cleanup SIGINT SIGTERM

# ============================================================
#  Start Services
# ============================================================

# 1. AI Services — FastAPI on port 8000
log "Starting AI Services on port 8000..."
(cd "$AI_DIR" && "$VENV_DIR/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 --reload) &
PIDS+=($!)

# 2. Node.js Server — Express on port 5000
log "Starting Node.js Server on port 5000..."
(cd "$SERVER_DIR" && node --watch src/server.js) &
PIDS+=($!)

# 3. React Client — Vite on port 5173
log "Starting React Client on port 5173..."
(cd "$CLIENT_DIR" && npx vite --host --port 5173) &
PIDS+=($!)

# ============================================================
#  Dashboard
# ============================================================
sleep 2
echo ""
echo -e "${BOLD}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  ✦  All AIChat services are running!${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════${NC}"
echo -e "  ${CYAN}Client:${NC}       http://localhost:5173"
echo -e "  ${CYAN}Server:${NC}       http://localhost:5000"
echo -e "  ${CYAN}AI Services:${NC}  http://localhost:8000"
echo -e "  ${CYAN}API Docs:${NC}     http://localhost:8000/docs"
echo -e "${BOLD}═══════════════════════════════════════════════${NC}"
echo -e "  Press ${YELLOW}Ctrl+C${NC} to stop all services"
echo ""

wait
