# ===========================================
# 🐝 Automagik Hive Multi-Agent System - Simplified Makefile
# ===========================================

.DEFAULT_GOAL := help
MAKEFLAGS += --no-print-directory
SHELL := /bin/bash

# ===========================================
# 🎨 Colors & Symbols
# ===========================================
FONT_RED := $(shell tput setaf 1)
FONT_GREEN := $(shell tput setaf 2)
FONT_YELLOW := $(shell tput setaf 3)
FONT_BLUE := $(shell tput setaf 4)
FONT_PURPLE := $(shell tput setaf 5)
FONT_CYAN := $(shell tput setaf 6)
FONT_GRAY := $(shell tput setaf 7)
FONT_BLACK := $(shell tput setaf 8)
FONT_BOLD := $(shell tput bold)
FONT_RESET := $(shell tput sgr0)
CHECKMARK := ✅
WARNING := ⚠️
ERROR := ❌
MAGIC := 🐝

# ===========================================
# 📁 Paths & Configuration
# ===========================================
PROJECT_ROOT := $(shell pwd)
VENV_PATH := $(PROJECT_ROOT)/.venv
PYTHON := $(VENV_PATH)/bin/python
DOCKER_COMPOSE_FILE := docker/main/docker-compose.yml

# Docker Compose command detection
DOCKER_COMPOSE := $(shell if command -v docker-compose >/dev/null 2>&1; then echo "docker-compose"; else echo "docker compose"; fi)

# UV command
UV := uv

# Load port from .env file
HIVE_PORT := $(shell grep -E '^HIVE_API_PORT=' .env 2>/dev/null | cut -d'=' -f2 | tr -d ' ')
ifeq ($(HIVE_PORT),)
    HIVE_PORT := 8886
endif


# ===========================================
# 🛠️ Utility Functions
# ===========================================
define print_status
    echo -e "$(FONT_PURPLE)🐝 $(1)$(FONT_RESET)"
endef

define print_success
    echo -e "$(FONT_GREEN)$(CHECKMARK) $(1)$(FONT_RESET)"
endef

define print_warning
    echo -e "$(FONT_YELLOW)$(WARNING) $(1)$(FONT_RESET)"
endef

define print_error
    echo -e "$(FONT_RED)$(ERROR) $(1)$(FONT_RESET)"
endef

define show_hive_logo
    if [ -z "$${HIVE_QUIET_LOGO}" ]; then \
        echo ""; \
        echo -e "$(FONT_PURPLE)                                                                     $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)                                                                     $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    ████         ████    ████    ████             ███████████       $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    ████         ████    ████     ████            ███████████       $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    ████         ████    ████      ████      ████ ████              $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    ████         ████    ████      █████    ████  ████              $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    ████         ████    ████       ████   ████   ████              $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)                 ████    ████        ████  ████   ██████████████    $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)                 ████    ████        █████████    ██████████████    $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)                 ████    ████         ███████     ████              $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    █████████████████    ████          █████      ████              $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    █████████████████    ████           ████      ████              $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    ████         ████ ██████████        ░██       ███████████       $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)    ████         ████ ██████████         █        ███████████       $(FONT_RESET)"; \
        echo -e "$(FONT_PURPLE)                                                                     $(FONT_RESET)"; \
        echo ""; \
    fi
endef

define check_docker
    BACKEND=$$(grep -E '^HIVE_DATABASE_BACKEND=' .env 2>/dev/null | cut -d'=' -f2 | tr -d ' ' || echo "pglite"); \
    if [ "$$BACKEND" = "pglite" ] || [ "$$BACKEND" = "sqlite" ]; then \
        $(call print_status,Using $$BACKEND backend - Docker not required); \
        exit 0; \
    fi; \
    if ! command -v docker >/dev/null 2>&1; then \
        $(call print_error,Docker not found); \
        echo -e "$(FONT_YELLOW)💡 Install Docker: https://docs.docker.com/get-docker/$(FONT_RESET)"; \
        echo -e "$(FONT_YELLOW)💡 Or switch to PGlite: HIVE_DATABASE_BACKEND=pglite$(FONT_RESET)"; \
        exit 1; \
    fi; \
    if ! docker info >/dev/null 2>&1; then \
        $(call print_error,Docker daemon not running); \
        echo -e "$(FONT_YELLOW)💡 Start Docker service$(FONT_RESET)"; \
        echo -e "$(FONT_YELLOW)💡 Or switch to PGlite: HIVE_DATABASE_BACKEND=pglite$(FONT_RESET)"; \
        exit 1; \
    fi
endef

define check_env_file
    if [ ! -f ".env" ]; then \
        $(call print_warning,.env file not found); \
        echo -e "$(FONT_CYAN)Copying .env.example to .env...$(FONT_RESET)"; \
        cp .env.example .env; \
        $(call print_success,.env created from example); \
        $(call generate_hive_api_key); \
        echo -e "$(FONT_YELLOW)💡 Edit .env and add your AI provider API keys$(FONT_RESET)"; \
    elif grep -q "HIVE_API_KEY=your-hive-api-key-here" .env; then \
        $(call print_warning,Hive API key needs to be generated); \
        $(call generate_hive_api_key); \
    elif ! grep -q "HIVE_API_KEY=hive_" .env; then \
        $(call print_warning,Hive API key format needs updating to hive_ prefix); \
        $(call generate_hive_api_key); \
    fi
endef

define generate_hive_api_key
    $(call print_status,Checking/generating secure Hive API key...); \
    uv run python -c "from lib.auth.init_service import AuthInitService; auth = AuthInitService(); key = auth.get_current_key(); print('API key already exists') if key else auth.ensure_api_key()"
endef


define show_api_key_info
    echo ""; \
    CURRENT_KEY=$$(grep "^HIVE_API_KEY=" .env 2>/dev/null | cut -d'=' -f2); \
    if [ -n "$$CURRENT_KEY" ]; then \
        echo -e "$(FONT_GREEN)🔑 YOUR API KEY: $$CURRENT_KEY$(FONT_RESET)"; \
        echo -e "$(FONT_CYAN)   Already saved to .env - use in x-api-key headers$(FONT_RESET)"; \
        echo ""; \
    fi
endef

define generate_postgres_credentials
    $(call extract_postgres_credentials_from_env); \
    if [ -n "$$POSTGRES_USER" ] && [ -n "$$POSTGRES_PASS" ] && \
       [ "$$POSTGRES_PASS" != "your-secure-password-here" ] && \
       [ "$$POSTGRES_USER" != "hive_user" ] && \
       [ "$$POSTGRES_USER" != "your-username-here" ]; then \
        $(call print_status,Using existing PostgreSQL credentials from .env...); \
        echo -e "$(FONT_CYAN)Reusing credentials:$(FONT_RESET)"; \
        echo -e "  User: $$POSTGRES_USER"; \
        echo -e "  Password: $$POSTGRES_PASS"; \
        echo -e "  Database: $$POSTGRES_DB"; \
    else \
        $(call print_status,Generating secure PostgreSQL credentials...); \
        POSTGRES_USER=$$(openssl rand -base64 12 | tr -d '=+/' | cut -c1-16); \
        POSTGRES_PASS=$$(openssl rand -base64 12 | tr -d '=+/' | cut -c1-16); \
        POSTGRES_DB="hive"; \
        sed -i "s|^HIVE_DATABASE_URL=.*|HIVE_DATABASE_URL=postgresql+psycopg://$$POSTGRES_USER:$$POSTGRES_PASS@localhost:5532/$$POSTGRES_DB|" .env; \
        $(call print_success,PostgreSQL credentials generated and saved to .env); \
        echo -e "$(FONT_CYAN)Generated credentials:$(FONT_RESET)"; \
        echo -e "  User: $$POSTGRES_USER"; \
        echo -e "  Password: $$POSTGRES_PASS"; \
        echo -e "  Database: $$POSTGRES_DB"; \
    fi
endef


define setup_docker_postgres
    echo ""; \
    echo -e "$(FONT_PURPLE)🐳 Optional Docker PostgreSQL Setup$(FONT_RESET)"; \
    echo -e "$(FONT_CYAN)Would you like to set up Docker PostgreSQL with secure credentials? (Y/n)$(FONT_RESET)"; \
    read -r REPLY </dev/tty; \
    if [ "$$REPLY" != "n" ] && [ "$$REPLY" != "N" ]; then \
        $(call check_docker); \
        $(call generate_postgres_credentials); \
        echo -e "$(FONT_CYAN)🐳 Starting PostgreSQL container...$(FONT_RESET)"; \
        if [ -d "./data/postgres" ]; then \
            if [ "$$(uname -s)" = "Linux" ] || [ "$$(uname -s)" = "Darwin" ]; then \
                OWNER=$$(stat -c '%U' ./data/postgres 2>/dev/null || stat -f '%Su' ./data/postgres 2>/dev/null || echo "unknown"); \
                if [ "$$OWNER" = "root" ]; then \
                    echo -e "$(FONT_YELLOW)💡 Fixing PostgreSQL data directory permissions...$(FONT_RESET)"; \
                    sudo chown -R $$(id -u):$$(id -g) ./data/postgres 2>/dev/null || true; \
                fi; \
            fi; \
        fi; \
        DB_URL=$$(grep '^HIVE_DATABASE_URL=' .env | cut -d'=' -f2-); \
        WITHOUT_PROTOCOL=$${DB_URL#*://}; \
        CREDENTIALS=$${WITHOUT_PROTOCOL%%@*}; \
        AFTER_AT=$${WITHOUT_PROTOCOL##*@}; \
        export POSTGRES_USER=$${CREDENTIALS%%:*}; \
        export POSTGRES_PASSWORD=$${CREDENTIALS##*:}; \
        export POSTGRES_DB=$${AFTER_AT##*/}; \
        if [ "$$(uname -s)" = "Linux" ] || [ "$$(uname -s)" = "Darwin" ]; then \
            export POSTGRES_UID=$$(id -u); \
            export POSTGRES_GID=$$(id -g); \
        else \
            export POSTGRES_UID=1000; \
            export POSTGRES_GID=1000; \
        fi; \
        mkdir -p ./data/postgres; \
        chmod -R 755 ./data/postgres; \
        chown -R $${POSTGRES_UID}:$${POSTGRES_GID} ./data/postgres 2>/dev/null || sudo chown -R $$USER:$$USER ./data/postgres; \
        echo -e "$(FONT_CYAN)📋 Creating Docker environment file for compose...$(FONT_RESET)"; \
        mkdir -p docker/main; \
        echo "POSTGRES_USER=$$POSTGRES_USER" > docker/main/.env; \
        echo "POSTGRES_PASSWORD=$$POSTGRES_PASSWORD" >> docker/main/.env; \
        echo "POSTGRES_DB=$$POSTGRES_DB" >> docker/main/.env; \
        echo "POSTGRES_UID=$$POSTGRES_UID" >> docker/main/.env; \
        echo "POSTGRES_GID=$$POSTGRES_GID" >> docker/main/.env; \
        echo "HIVE_API_PORT=$$(grep '^HIVE_API_PORT=' .env | cut -d'=' -f2 | head -1 || echo '8886')" >> docker/main/.env; \
        $(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) up -d postgres; \
        echo -e "$(FONT_GREEN)$(CHECKMARK) PostgreSQL container started with secure credentials!$(FONT_RESET)"; \
        echo -e "$(FONT_YELLOW)💡 Run 'make dev' for development or 'make prod' for production stack$(FONT_RESET)"; \
    else \
        echo -e "$(FONT_GRAY)Skipping Docker PostgreSQL setup$(FONT_RESET)"; \
    fi
endef

define check_prerequisites
    if ! command -v python3 >/dev/null 2>&1; then \
        $(call print_error,Python 3 not found); \
        exit 1; \
    fi; \
    if ! command -v uv >/dev/null 2>&1; then \
        if [ -f "$HOME/.local/bin/uv" ]; then \
            export PATH="$HOME/.local/bin:$PATH"; \
            $(call print_status,Found uv in $HOME/.local/bin); \
        else \
            $(call print_status,Installing uv...); \
            curl -LsSf https://astral.sh/uv/install.sh | sh; \
            export PATH="$HOME/.local/bin:$PATH"; \
            $(call print_success,uv installed successfully); \
        fi; \
    else \
        $(call print_status,uv is already available in PATH); \
    fi
endef

define setup_python_env
    $(call print_status,Installing dependencies with uv...); \
    if command -v uv >/dev/null 2>&1; then \
        if ! uv sync 2>/dev/null; then \
            $(call print_warning,Installation failed - clearing UV cache and retrying...); \
            uv cache clean; \
            uv sync; \
        fi; \
    elif [ -f "$HOME/.local/bin/uv" ]; then \
        if ! $HOME/.local/bin/uv sync 2>/dev/null; then \
            $(call print_warning,Installation failed - clearing UV cache and retrying...); \
            $HOME/.local/bin/uv cache clean; \
            $HOME/.local/bin/uv sync; \
        fi; \
    else \
        $(call print_error,uv not found - please run 'make install' first); \
        exit 1; \
    fi
endef






# ===========================================
# 📋 Help System
# ===========================================
.PHONY: help
help: ## 🐝 Show this help message
	@$(call show_hive_logo)
	@echo -e "$(FONT_BOLD)$(FONT_CYAN)Automagik Hive Multi-Agent System$(FONT_RESET) - $(FONT_GRAY)Enterprise AI Framework$(FONT_RESET)"
	@echo ""
	@echo -e "$(FONT_PURPLE)🐝 Usage: make [command]$(FONT_RESET)"
	@echo ""
	@echo -e "$(FONT_CYAN)🚀 Getting Started:$(FONT_RESET)"
	@echo -e "  $(FONT_PURPLE)install$(FONT_RESET)         Install environment (PGlite by default - no Docker)"
	@echo -e "  $(FONT_PURPLE)install-pglite$(FONT_RESET)  Install with PGlite backend (no Docker required)"
	@echo -e "  $(FONT_PURPLE)install-sqlite$(FONT_RESET)  Install with SQLite backend (no Docker required)"
	@echo -e "  $(FONT_PURPLE)install-postgres$(FONT_RESET) Install with PostgreSQL + Docker"
	@echo -e "  $(FONT_PURPLE)dev$(FONT_RESET)             Start local development server (with hot-reload)"
	@echo -e "  $(FONT_PURPLE)serve$(FONT_RESET)           Start workspace server (mirrors --serve)"
	@echo -e "  $(FONT_PURPLE)prod$(FONT_RESET)            Start production stack via Docker"
	@echo -e "  $(FONT_PURPLE)version$(FONT_RESET)         Show version (mirrors --version)"
	@echo ""
	@echo -e "$(FONT_CYAN)🐘 PostgreSQL Management (UV Integration):$(FONT_RESET)"
	@echo -e "  $(FONT_PURPLE)postgres-status$(FONT_RESET) Check PostgreSQL status (mirrors --postgres-status)"
	@echo -e "  $(FONT_PURPLE)postgres-start$(FONT_RESET)  Start PostgreSQL (mirrors --postgres-start)"
	@echo -e "  $(FONT_PURPLE)postgres-stop$(FONT_RESET)   Stop PostgreSQL (mirrors --postgres-stop)"
	@echo -e "  $(FONT_PURPLE)postgres-restart$(FONT_RESET) Restart PostgreSQL (mirrors --postgres-restart)"
	@echo -e "  $(FONT_PURPLE)postgres-logs$(FONT_RESET)   Show PostgreSQL logs (mirrors --postgres-logs)"
	@echo -e "  $(FONT_PURPLE)postgres-health$(FONT_RESET) Check PostgreSQL health (mirrors --postgres-health)"
	@echo ""
	@echo -e "$(FONT_CYAN)🏭 Production Environment (UV Integration):$(FONT_RESET)"
	@echo -e "  $(FONT_PURPLE)restart$(FONT_RESET)         Restart production environment (mirrors --restart)"
	@echo ""
	@echo ""
	@echo -e "$(FONT_CYAN)🎛️ Service Control:$(FONT_RESET)"
	@echo -e "  $(FONT_PURPLE)status$(FONT_RESET)          Show running services status"
	@echo -e "  $(FONT_PURPLE)stop$(FONT_RESET)            Stop application service (keeps database running)"
	@echo -e "  $(FONT_PURPLE)stop-all$(FONT_RESET)       Stop all services (including database)"
	@echo -e "  $(FONT_PURPLE)update$(FONT_RESET)          Fast rebuild of Docker app using cache"
	@echo -e "  $(FONT_PURPLE)rebuild$(FONT_RESET)         Force full rebuild of Docker app (no cache)"
	@echo ""
	@echo -e "$(FONT_CYAN)📋 Monitoring:$(FONT_RESET)"
	@echo -e "  $(FONT_PURPLE)logs$(FONT_RESET)            Show recent service logs"
	@echo -e "  $(FONT_PURPLE)logs-live$(FONT_RESET)       Follow service logs in real-time"
	@echo -e "  $(FONT_PURPLE)health$(FONT_RESET)          Check API health endpoint"
	@echo ""
	@echo -e "$(FONT_CYAN)🔄 Maintenance:$(FONT_RESET)"
	@echo -e "  $(FONT_PURPLE)test$(FONT_RESET)            Run Python test suite"
	@echo -e "  $(FONT_PURPLE)clean$(FONT_RESET)           Clean temporary files (__pycache__, etc.)"
	@echo -e "  $(FONT_PURPLE)uninstall$(FONT_RESET)       Complete uninstall - removes everything"
	@echo -e "  $(FONT_PURPLE)uninstall-workspace$(FONT_RESET) Uninstall current workspace (mirrors uninstall)"
	@echo -e "  $(FONT_PURPLE)uninstall-global$(FONT_RESET) Uninstall global installation (mirrors --uninstall-global)"
	@echo ""
	@echo -e "$(FONT_CYAN)📦 Release & Publishing:$(FONT_RESET)"
	@echo -e "  $(FONT_PURPLE)bump-major$(FONT_RESET)      Bump major version (1.0.0 → 2.0.0)"
	@echo -e "  $(FONT_PURPLE)bump-minor$(FONT_RESET)      Bump minor version (0.1.0 → 0.2.0)"
	@echo -e "  $(FONT_PURPLE)bump-patch$(FONT_RESET)      Bump patch version (0.1.0 → 0.1.1)"
	@echo -e "  $(FONT_PURPLE)bump-rc$(FONT_RESET)         Add/bump RC suffix (0.2.0 → 0.2.0rc1)"
	@echo -e "  $(FONT_PURPLE)bump$(FONT_RESET)            Bump beta version (0.1.1b2 → 0.1.1b3)"
	@echo -e "  $(FONT_PURPLE)release-rc$(FONT_RESET)      Commit, tag, and publish release"
	@echo ""
	@echo -e "$(FONT_YELLOW)💡 For detailed commands, inspect the Makefile.$(FONT_RESET)"
	@echo ""

# ===========================================
# 🚀 Installation
# ===========================================
.PHONY: install-local
install-local: ## 🛠️ Install development environment (local only)
	@$(call print_status,Installing development environment...)
	@$(call check_prerequisites)
	@$(call setup_python_env)
	@$(call check_env_file)
	@$(call show_hive_logo)
	@$(call show_api_key_info)
	@$(call print_success,Development environment ready!)
	@echo -e "$(FONT_CYAN)💡 Run 'make dev' to start development server$(FONT_RESET)"

.PHONY: install
install: ## 🛠️ Complete environment setup - mirrors CLI install
	@$(call print_status,Installing complete Automagik Hive environment...)
	@$(call check_prerequisites)
	@$(call setup_python_env)
	@uv run automagik-hive install
	@$(call sync_mcp_config_with_credentials)
	@$(call print_success,Environment ready!)
	@echo -e "$(FONT_CYAN)🌐 API available at: http://localhost:$(HIVE_PORT)$(FONT_RESET)"

.PHONY: install-pglite
install-pglite: ## 🛠️ Install with PGlite backend (no Docker required)
	@$(call print_status,Installing Automagik Hive with PGlite backend...)
	@$(call check_prerequisites)
	@$(call setup_python_env)
	@$(call check_env_file)
	@sed -i 's/^HIVE_DATABASE_BACKEND=.*/HIVE_DATABASE_BACKEND=pglite/' .env
	@sed -i 's|^HIVE_DATABASE_URL=.*|HIVE_DATABASE_URL=pglite://./data/automagik_hive.db|' .env
	@$(call show_hive_logo)
	@$(call show_api_key_info)
	@$(call print_success,PGlite environment ready - no Docker required!)
	@echo -e "$(FONT_CYAN)💡 Run 'make dev' to start development server$(FONT_RESET)"

.PHONY: install-sqlite
install-sqlite: ## 🛠️ Install with SQLite backend (no Docker required)
	@$(call print_status,Installing Automagik Hive with SQLite backend...)
	@$(call check_prerequisites)
	@$(call setup_python_env)
	@$(call check_env_file)
	@sed -i 's/^HIVE_DATABASE_BACKEND=.*/HIVE_DATABASE_BACKEND=sqlite/' .env
	@sed -i 's|^HIVE_DATABASE_URL=.*|HIVE_DATABASE_URL=sqlite:///./data/automagik_hive.db|' .env
	@$(call show_hive_logo)
	@$(call show_api_key_info)
	@$(call print_success,SQLite environment ready - no Docker required!)
	@echo -e "$(FONT_CYAN)💡 Run 'make dev' to start development server$(FONT_RESET)"

.PHONY: install-postgres
install-postgres: ## 🛠️ Install with PostgreSQL backend (requires Docker)
	@$(call print_status,Installing Automagik Hive with PostgreSQL backend...)
	@$(call check_docker)
	@$(call check_prerequisites)
	@$(call setup_python_env)
	@$(call check_env_file)
	@sed -i 's/^HIVE_DATABASE_BACKEND=.*/HIVE_DATABASE_BACKEND=postgresql/' .env
	@$(call setup_docker_postgres)
	@$(call show_hive_logo)
	@$(call show_api_key_info)
	@$(call print_success,PostgreSQL environment ready!)
	@echo -e "$(FONT_CYAN)💡 Run 'make dev' to start development server$(FONT_RESET)"


# ===========================================
# 🎛️ Service Management
# ===========================================
.PHONY: dev
dev: ## 🛠️ Start development server with hot reload
	@$(call show_hive_logo)
	@$(call print_status,Starting Automagik Hive development server...)
	@$(call check_env_file)
	@if [ ! -d "$(VENV_PATH)" ]; then \
		$(call print_error,Virtual environment not found); \
		echo -e "$(FONT_YELLOW)💡 Run 'make install' first$(FONT_RESET)"; \
		exit 1; \
	fi
	@echo -e "$(FONT_YELLOW)💡 Press Ctrl+C to stop the server$(FONT_RESET)"
	@echo -e "$(FONT_PURPLE)🚀 Starting server...$(FONT_RESET)"
	@HIVE_DEV_GRACEFUL=1 uv run automagik-hive dev

.PHONY: serve
serve: ## 🚀 Start production server (Docker) - mirrors CLI --serve
	@$(call print_status,Starting production server...)
	@$(call check_env_file)
	@uv run automagik-hive --serve
	@$(call print_success,Production server started!)

# ===========================================
# 🐘 PostgreSQL Management (UV Integration)
# ===========================================
.PHONY: postgres-status
postgres-status: ## 📊 Check PostgreSQL status - mirrors CLI --postgres-status
	@$(call print_status,PostgreSQL Status)
	@uv run automagik-hive --postgres-status

.PHONY: postgres-start
postgres-start: ## 🚀 Start PostgreSQL - mirrors CLI --postgres-start
	@$(call print_status,Starting PostgreSQL...)
	@uv run automagik-hive --postgres-start

.PHONY: postgres-stop
postgres-stop: ## 🛑 Stop PostgreSQL - mirrors CLI --postgres-stop
	@$(call print_status,Stopping PostgreSQL...)
	@uv run automagik-hive --postgres-stop

.PHONY: postgres-restart
postgres-restart: ## 🔄 Restart PostgreSQL - mirrors CLI --postgres-restart
	@$(call print_status,Restarting PostgreSQL...)
	@uv run automagik-hive --postgres-restart

.PHONY: postgres-logs
postgres-logs: ## 📄 Show PostgreSQL logs - mirrors CLI --postgres-logs
	@echo -e "$(FONT_PURPLE)🐘 PostgreSQL Logs$(FONT_RESET)"
	@uv run automagik-hive --postgres-logs --tail 50

.PHONY: postgres-health
postgres-health: ## 💊 Check PostgreSQL health - mirrors CLI --postgres-health
	@$(call print_status,PostgreSQL Health Check)
	@uv run automagik-hive --postgres-health

# ===========================================
# 🚀 Core Development Commands (UV Integration)
# ===========================================

.PHONY: version
version: ## 📄 Show version - mirrors CLI --version
	@uv run automagik-hive --version

.PHONY: stop
stop: ## 🛑 Stop production environment - mirrors CLI --stop
	@$(call print_status,Stopping production environment...)
	@uv run automagik-hive --stop
	@$(call print_success,Production environment stopped!)

.PHONY: restart
restart: ## 🔄 Restart production environment - mirrors CLI --restart
	@$(call print_status,Restarting production environment...)
	@uv run automagik-hive --restart
	@$(call print_success,Production environment restarted!)




.PHONY: status
status: ## 📊 Show production environment status - mirrors CLI --status
	@$(call print_status,Production Environment Status)
	@uv run automagik-hive --status

# ===========================================
# 📋 Monitoring
# ===========================================
.PHONY: logs
logs: ## 📄 Show production environment logs - mirrors CLI --logs
	@echo -e "$(FONT_PURPLE)🐝 Production Environment Logs$(FONT_RESET)"
	@uv run automagik-hive --logs --tail 50

# DEPRECATED: No CLI equivalent - kept for backward compatibility
# .PHONY: logs-live
# logs-live: ## 📄 Follow logs in real-time
# 	@echo -e "$(FONT_PURPLE)🐝 Live Application Logs$(FONT_RESET)"
# 	@if docker ps --filter "name=hive-api" --format "{{.Names}}" | grep -q hive-api; then \
# 		echo -e "$(FONT_CYAN)=== Following Hive Agents Container Logs ====$(FONT_RESET)"; \
# 		echo -e "$(FONT_YELLOW)💡 Press Ctrl+C to stop following logs$(FONT_RESET)"; \
# 		docker logs -f hive-api; \
# 	elif pgrep -f "python.*api/serve.py" >/dev/null 2>&1; then \
# 		echo -e "$(FONT_CYAN)=== Following Local Development Logs ====$(FONT_RESET)"; \
# 		if [ -f "logs/app.log" ]; then \
# 			echo -e "$(FONT_YELLOW)💡 Press Ctrl+C to stop following logs$(FONT_RESET)"; \
# 			tail -f logs/app.log; \
# 		elif [ -f "app.log" ]; then \
# 			echo -e "$(FONT_YELLOW)💡 Press Ctrl+C to stop following logs$(FONT_RESET)"; \
# 			tail -f app.log; \
# 		else \
# 			echo -e "$(FONT_YELLOW)⚠️ No log files found for local development$(FONT_RESET)"; \
# 			echo -e "$(FONT_GRAY)📋 Logs are displayed in the terminal where 'make dev' is running$(FONT_RESET)"; \
# 		fi \
# 	else \
# 		echo -e "$(FONT_YELLOW)⚠️ No running services found$(FONT_RESET)"; \
# 		echo -e "$(FONT_GRAY)💡 Start services with 'make dev' (local) or 'make prod' (Docker)$(FONT_RESET)"; \
# 	fi

.PHONY: health
health: ## 💊 Check service health
	@$(call print_status,Health Check)
	@if docker ps --filter "name=hive-api" --format "{{.Names}}" | grep -q hive-api; then \
		if curl -s http://localhost:$(HIVE_PORT)/health >/dev/null 2>&1; then \
			echo -e "$(FONT_GREEN)$(CHECKMARK) API health check: passed$(FONT_RESET)"; \
		else \
			echo -e "$(FONT_YELLOW)$(WARNING) API health check: failed$(FONT_RESET)"; \
		fi; \
	else \
		echo -e "$(FONT_YELLOW)$(WARNING) Docker containers not running$(FONT_RESET)"; \
	fi
	@if curl -s http://localhost:$(HIVE_PORT)/health >/dev/null 2>&1; then \
		echo -e "$(FONT_GREEN)$(CHECKMARK) Development server: healthy$(FONT_RESET)"; \
	elif pgrep -f "python.*api/serve.py" >/dev/null 2>&1; then \
		echo -e "$(FONT_YELLOW)$(WARNING) Development server running but health check failed$(FONT_RESET)"; \
	fi

# ===========================================
# 🔄 Maintenance & Data Management
# ===========================================
.PHONY: clean
clean: ## 🧹 Clean temporary files
	@$(call print_status,Cleaning temporary files...)
	@rm -rf logs/ 2>/dev/null || true
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -type f -delete 2>/dev/null || true
	@find . -name "*.pyo" -type f -delete 2>/dev/null || true
	@$(call print_success,Cleanup complete!)


.PHONY: uninstall
uninstall: ## 🗑️ Uninstall production environment - mirrors CLI uninstall
	@$(call print_status,Uninstalling production environment...)
	@uv run automagik-hive uninstall
	@$(call print_success,Production environment uninstalled!)


.PHONY: test
test: ## 🧪 Run test suite
	@$(call print_status,Running tests...)
	@if [ ! -d "$(VENV_PATH)" ]; then \
		$(call print_error,Virtual environment not found); \
		echo -e "$(FONT_YELLOW)💡 Run 'make install' first$(FONT_RESET)"; \
		exit 1; \
	fi
	@uv run pytest

# ===========================================
# 🔄 Uninstall Commands (UV Integration)
# ===========================================
.PHONY: uninstall-workspace
uninstall-workspace: ## 🗑️ Uninstall current workspace (mirrors --uninstall)
	@$(call print_status,Uninstalling current workspace...)
	@uv run automagik-hive --uninstall
	@$(call print_success,Workspace uninstalled!)

.PHONY: uninstall-global
uninstall-global: ## 🗑️ Uninstall global installation (mirrors --uninstall-global)
	@$(call print_status,Uninstalling global installation...)
	@uv run automagik-hive --uninstall-global
	@$(call print_success,Global installation uninstalled!)

# ===========================================

# ===========================================
# 🚀 Semantic Version Bumping
# ===========================================
.PHONY: bump-major
bump-major: ## 🏷️ Bump major version (X.0.0)
	@$(call print_status,Bumping major version...)
	@if [ ! -f "pyproject.toml" ]; then \
		$(call print_error,pyproject.toml not found); \
		exit 1; \
	fi
	@CURRENT_VERSION=$$(grep '^version = ' pyproject.toml | cut -d'"' -f2); \
	BASE_VERSION=$$(echo "$$CURRENT_VERSION" | sed 's/[-+].*//' | sed 's/[a-z].*//'  | sed 's/rc.*//' | sed 's/b.*//'); \
	MAJOR=$$(echo "$$BASE_VERSION" | cut -d'.' -f1); \
	NEW_MAJOR=$$((MAJOR + 1)); \
	NEW_VERSION="$${NEW_MAJOR}.0.0"; \
	$(call print_status,Updating version from $$CURRENT_VERSION to $$NEW_VERSION); \
	sed -i "s/^version = \"$$CURRENT_VERSION\"/version = \"$$NEW_VERSION\"/" pyproject.toml; \
	$(call print_success,Version bumped to $$NEW_VERSION); \
	echo -e "$(FONT_CYAN)💡 Next: make release-rc (or make bump-rc for RC)$(FONT_RESET)"

.PHONY: bump-minor
bump-minor: ## 🏷️ Bump minor version (0.X.0)
	@$(call print_status,Bumping minor version...)
	@if [ ! -f "pyproject.toml" ]; then \
		$(call print_error,pyproject.toml not found); \
		exit 1; \
	fi
	@CURRENT_VERSION=$$(grep '^version = ' pyproject.toml | cut -d'"' -f2); \
	BASE_VERSION=$$(echo "$$CURRENT_VERSION" | sed 's/[-+].*//' | sed 's/[a-z].*//' | sed 's/rc.*//' | sed 's/b.*//'); \
	MAJOR=$$(echo "$$BASE_VERSION" | cut -d'.' -f1); \
	MINOR=$$(echo "$$BASE_VERSION" | cut -d'.' -f2); \
	NEW_MINOR=$$((MINOR + 1)); \
	NEW_VERSION="$${MAJOR}.$${NEW_MINOR}.0"; \
	$(call print_status,Updating version from $$CURRENT_VERSION to $$NEW_VERSION); \
	sed -i "s/^version = \"$$CURRENT_VERSION\"/version = \"$$NEW_VERSION\"/" pyproject.toml; \
	$(call print_success,Version bumped to $$NEW_VERSION); \
	echo -e "$(FONT_CYAN)💡 Next: make release-rc (or make bump-rc for RC)$(FONT_RESET)"

.PHONY: bump-patch
bump-patch: ## 🏷️ Bump patch version (0.0.X)
	@$(call print_status,Bumping patch version...)
	@if [ ! -f "pyproject.toml" ]; then \
		$(call print_error,pyproject.toml not found); \
		exit 1; \
	fi
	@CURRENT_VERSION=$$(grep '^version = ' pyproject.toml | cut -d'"' -f2); \
	BASE_VERSION=$$(echo "$$CURRENT_VERSION" | sed 's/[-+].*//' | sed 's/[a-z].*//' | sed 's/rc.*//' | sed 's/b.*//'); \
	MAJOR=$$(echo "$$BASE_VERSION" | cut -d'.' -f1); \
	MINOR=$$(echo "$$BASE_VERSION" | cut -d'.' -f2); \
	PATCH=$$(echo "$$BASE_VERSION" | cut -d'.' -f3); \
	NEW_PATCH=$$((PATCH + 1)); \
	NEW_VERSION="$${MAJOR}.$${MINOR}.$${NEW_PATCH}"; \
	$(call print_status,Updating version from $$CURRENT_VERSION to $$NEW_VERSION); \
	sed -i "s/^version = \"$$CURRENT_VERSION\"/version = \"$$NEW_VERSION\"/" pyproject.toml; \
	$(call print_success,Version bumped to $$NEW_VERSION); \
	echo -e "$(FONT_CYAN)💡 Next: make release-rc (or make bump-rc for RC)$(FONT_RESET)"

# ===========================================
# 🚀 Release & Publishing (Beta)
# ===========================================
.PHONY: bump
bump: ## 🏷️ Bump beta version and prepare for release
	@$(call print_status,Bumping beta version...)
	@if [ ! -f "pyproject.toml" ]; then \
		$(call print_error,pyproject.toml not found); \
		exit 1; \
	fi
	@CURRENT_VERSION=$$(grep '^version = ' pyproject.toml | cut -d'"' -f2); \
	if echo "$$CURRENT_VERSION" | grep -q "b[0-9]*$$"; then \
		BETA_NUM=$$(echo "$$CURRENT_VERSION" | grep -o "b[0-9]*$$" | sed 's/b//'); \
		NEW_BETA_NUM=$$((BETA_NUM + 1)); \
		BASE_VERSION=$$(echo "$$CURRENT_VERSION" | sed 's/b[0-9]*$$//'); \
		NEW_VERSION="$${BASE_VERSION}b$${NEW_BETA_NUM}"; \
	else \
		$(call print_error,Current version is not a beta version: $$CURRENT_VERSION); \
		echo -e "$(FONT_YELLOW)💡 Only beta versions can be bumped with this command$(FONT_RESET)"; \
		exit 1; \
	fi; \
	$(call print_status,Updating version from $$CURRENT_VERSION to $$NEW_VERSION); \
	sed -i "s/^version = \"$$CURRENT_VERSION\"/version = \"$$NEW_VERSION\"/" pyproject.toml; \
	$(call print_success,Version bumped to $$NEW_VERSION); \
	echo -e "$(FONT_CYAN)💡 Next: make publish$(FONT_RESET)"

.PHONY: publish
publish: ## 📦 Build and publish beta release to PyPI
	@$(call print_status,Publishing beta release...)
	@if [ ! -f "pyproject.toml" ]; then \
		$(call print_error,pyproject.toml not found); \
		exit 1; \
	fi
	@CURRENT_VERSION=$$(grep '^version = ' pyproject.toml | cut -d'"' -f2); \
	if ! echo "$$CURRENT_VERSION" | grep -q "b[0-9]*$$"; then \
		$(call print_error,Not a beta version: $$CURRENT_VERSION); \
		echo -e "$(FONT_YELLOW)💡 Only beta versions can be published with this command$(FONT_RESET)"; \
		exit 1; \
	fi; \
	$(call print_status,Building package for version $$CURRENT_VERSION); \
	rm -rf dist/ build/ *.egg-info/; \
	if command -v uv >/dev/null 2>&1; then \
		uv build; \
	else \
		$(call print_error,uv not found - required for building); \
		exit 1; \
	fi; \
	$(call print_status,Committing version bump...); \
	git add pyproject.toml; \
	git commit -m "bump: beta version $$CURRENT_VERSION" \
		-m "🏷️ BETA RELEASE PREPARATION:" \
		-m "- Bumped version to $$CURRENT_VERSION" \
		-m "- Ready for PyPI publication via 'make publish'" \
		-m "- UVX testing enabled with: uvx automagik-hive@$$CURRENT_VERSION" \
		-m "" \
		-m "🚀 TESTING COMMAND:" \
		-m "uvx automagik-hive@$$CURRENT_VERSION --version" \
		--trailer "Co-Authored-By: Automagik Genie <genie@namastex.ai>"; \
	$(call print_status,Creating and pushing git tag...); \
	git tag "v$$CURRENT_VERSION" -m "Beta release v$$CURRENT_VERSION"; \
	git push origin dev; \
	git push origin "v$$CURRENT_VERSION"; \
	$(call print_status,Publishing to PyPI...); \
	if [ -f ".env" ]; then \
		PYPI_USERNAME=$$(grep '^PYPI_USERNAME=' .env | cut -d'=' -f2 | tr -d ' '); \
		PYPI_TOKEN=$$(grep '^PYPI_API_KEY=' .env | cut -d'=' -f2 | tr -d ' '); \
		if [ -n "$$PYPI_USERNAME" ] && [ -n "$$PYPI_TOKEN" ] && [ "$$PYPI_TOKEN" != "your-pypi-api-token-here" ]; then \
			$(call print_status,Using PyPI credentials from .env file...); \
			export TWINE_USERNAME="$$PYPI_USERNAME"; \
			export TWINE_PASSWORD="$$PYPI_TOKEN"; \
		else \
			$(call print_warning,PyPI credentials not found in .env - will prompt for input); \
		fi; \
	else \
		$(call print_warning,.env file not found - will prompt for PyPI credentials); \
	fi; \
	if command -v twine >/dev/null 2>&1; then \
		twine upload dist/*; \
	else \
		$(call print_warning,twine not found - installing...); \
		uv add --dev twine; \
		uv run twine upload dist/*; \
	fi; \
	$(call print_success,Beta release $$CURRENT_VERSION published!); \
	echo -e "$(FONT_CYAN)🚀 Test with: uvx automagik-hive@$$CURRENT_VERSION --version$(FONT_RESET)"; \
	echo -e "$(FONT_YELLOW)💡 Wait 5-10 minutes for PyPI propagation$(FONT_RESET)"

# ===========================================
# 🚀 Release Candidate Publishing
# ===========================================
.PHONY: bump-rc
bump-rc: ## 🏷️ Add/bump RC suffix to current version
	@$(call print_status,Adding/bumping release candidate suffix...)
	@if [ ! -f "pyproject.toml" ]; then \
		$(call print_error,pyproject.toml not found); \
		exit 1; \
	fi
	@CURRENT_VERSION=$$(grep '^version = ' pyproject.toml | cut -d'"' -f2); \
	if echo "$$CURRENT_VERSION" | grep -q "rc[0-9]*$$"; then \
		RC_NUM=$$(echo "$$CURRENT_VERSION" | grep -o "rc[0-9]*$$" | sed 's/rc//'); \
		NEW_RC_NUM=$$((RC_NUM + 1)); \
		BASE_VERSION=$$(echo "$$CURRENT_VERSION" | sed 's/rc[0-9]*$$//'); \
		NEW_VERSION="$${BASE_VERSION}rc$${NEW_RC_NUM}"; \
		$(call print_status,Bumping RC: $$CURRENT_VERSION → $$NEW_VERSION); \
	else \
		BASE_VERSION=$$(echo "$$CURRENT_VERSION" | sed 's/[-+].*//' | sed 's/[a-z].*//' | sed 's/b.*//'); \
		NEW_VERSION="$${BASE_VERSION}rc1"; \
		$(call print_status,Adding RC suffix: $$CURRENT_VERSION → $$NEW_VERSION); \
	fi; \
	sed -i "s/^version = \"$$CURRENT_VERSION\"/version = \"$$NEW_VERSION\"/" pyproject.toml; \
	$(call print_success,Version bumped to $$NEW_VERSION); \
	echo -e "$(FONT_CYAN)💡 Next: make release-rc (commit, tag, and publish)$(FONT_RESET)"

.PHONY: release-rc
release-rc: ## 🚀 Create release (commit, tag, push) - triggers GitHub Actions publishing
	@$(call print_status,Creating release...)
	@if [ ! -f "pyproject.toml" ]; then \
		$(call print_error,pyproject.toml not found); \
		exit 1; \
	fi
	@CURRENT_VERSION=$$(grep '^version = ' pyproject.toml | cut -d'"' -f2); \
	if git status --porcelain | grep -q "pyproject.toml"; then \
		$(call print_status,Committing version bump to v$$CURRENT_VERSION...); \
		git add pyproject.toml; \
		git commit -m "release: v$$CURRENT_VERSION" \
			-m "🚀 Release v$$CURRENT_VERSION" \
			-m "" \
			-m "This release will be published via GitHub Actions" \
			-m "Associated PR: #56" \
			--trailer "Co-Authored-By: Automagik Genie 🧞 <genie@namastex.ai>"; \
	else \
		$(call print_status,No changes to commit - pyproject.toml already committed); \
	fi; \
	$(call print_status,Creating git tag v$$CURRENT_VERSION...); \
	if git tag -l "v$$CURRENT_VERSION" | grep -q "v$$CURRENT_VERSION"; then \
		$(call print_warning,Tag v$$CURRENT_VERSION already exists - deleting and recreating...); \
		git tag -d "v$$CURRENT_VERSION"; \
	fi; \
	git tag "v$$CURRENT_VERSION" -m "Release v$$CURRENT_VERSION"; \
	$(call print_status,Pushing to origin...); \
	git push origin dev; \
	git push origin "v$$CURRENT_VERSION"; \
	$(call print_success,Release v$$CURRENT_VERSION created and pushed!); \
	echo ""; \
	echo -e "$(FONT_PURPLE)🤖 GitHub Actions Publishing Pipeline Started$(FONT_RESET)"; \
	echo ""; \
	echo -e "$(FONT_CYAN)📋 Publishing Steps:$(FONT_RESET)"; \
	echo -e "  1. ✅ Build package"; \
	echo -e "  2. ✅ Verify version matches tag"; \
	echo -e "  3. 🧪 Publish to TestPyPI"; \
	echo -e "  4. 🧪 Test installation from TestPyPI"; \
	echo -e "  5. 📦 Publish to PyPI"; \
	echo -e "  6. 🎉 Update GitHub Release"; \
	echo ""; \
	echo -e "$(FONT_CYAN)🔗 Monitor Progress:$(FONT_RESET)"; \
	echo -e "  $(FONT_PURPLE)https://github.com/namastexlabs/automagik-hive/actions$(FONT_RESET)"; \
	echo ""; \
	echo -e "$(FONT_YELLOW)💡 Installation (after ~5-10 minutes):$(FONT_RESET)"; \
	echo -e "  pip install automagik-hive==$$CURRENT_VERSION"; \
	echo -e "  uvx automagik-hive@$$CURRENT_VERSION --version"

# ===========================================
# 🧹 Phony Targets
# ===========================================
.PHONY: help install install-local dev prod stop restart status logs logs-live health clean test uninstall serve version postgres-status postgres-start postgres-stop postgres-restart postgres-logs postgres-health uninstall-workspace uninstall-global bump-major bump-minor bump-patch bump publish bump-rc release-rc
# ===========================================
# 🔑 UNIFIED CREDENTIAL MANAGEMENT SYSTEM
# ===========================================

# Extract PostgreSQL credentials from main .env file
define extract_postgres_credentials_from_env
    if [ -f ".env" ] && grep -q "^HIVE_DATABASE_URL=" .env; then \
        EXISTING_URL=$$(grep "^HIVE_DATABASE_URL=" .env | cut -d'=' -f2); \
        if echo "$$EXISTING_URL" | grep -q "postgresql+psycopg://"; then \
            POSTGRES_USER=$$(echo "$$EXISTING_URL" | sed -n 's|.*://\([^:]*\):.*|\1|p'); \
            POSTGRES_PASS=$$(echo "$$EXISTING_URL" | sed -n 's|.*://[^:]*:\([^@]*\)@.*|\1|p'); \
            POSTGRES_DB=$$(echo "$$EXISTING_URL" | sed -n 's|.*/\([^?]*\).*|\1|p'); \
            POSTGRES_HOST=$$(echo "$$EXISTING_URL" | sed -n 's|.*@\([^:]*\):.*|\1|p'); \
            POSTGRES_PORT=$$(echo "$$EXISTING_URL" | sed -n 's|.*:\([0-9]*\)/.*|\1|p'); \
        fi; \
    fi
endef

# Extract API key from main .env file  
define extract_hive_api_key_from_env
    if [ -f ".env" ] && grep -q "^HIVE_API_KEY=" .env; then \
        HIVE_API_KEY=$$(grep "^HIVE_API_KEY=" .env | cut -d'=' -f2); \
    fi
endef


  

# Generate MCP configuration with current credentials
define sync_mcp_config_with_credentials
    $(call extract_postgres_credentials_from_env); \
    $(call extract_hive_api_key_from_env); \
    if [ -n "$$POSTGRES_USER" ] && [ -n "$$POSTGRES_PASS" ] && [ -n "$$HIVE_API_KEY" ]; then \
        $(call print_status,Updating .mcp.json with current credentials...); \
        sed -i "s|postgresql+psycopg://[^@]*@|postgresql+psycopg://$$POSTGRES_USER:$$POSTGRES_PASS@|g" .mcp.json; \
        sed -i "s|\"HIVE_API_KEY\": \"[^\"]*\"|\"HIVE_API_KEY\": \"$$HIVE_API_KEY\"|g" .mcp.json; \
        $(call print_success,.mcp.json updated with current credentials); \
    else \
        $(call print_warning,Could not update .mcp.json - missing credentials); \
    fi
endef
