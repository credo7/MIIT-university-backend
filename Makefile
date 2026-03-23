#===============================================================================
# MIIT Project Makefile
#===============================================================================

.PHONY: help up down restart logs build backup backup-list backup-logs backup-status backup-restore backup-install backup-uninstall pack unpack up-pack down-pack

# Пути
BACKUP_SCRIPT := ./scripts/mongodb-backup.sh
SYSTEMD_DIR := /etc/systemd/system
PROJECT_DIR := $(shell pwd)

#===============================================================================
# ПОМОЩЬ
#===============================================================================

help:
	@echo ""
	@echo "==================== MIIT Project ===================="
	@echo ""
	@echo "Docker:"
	@echo "  make up          - Запустить все контейнеры"
	@echo "  make down        - Остановить все контейнеры"
	@echo "  make restart     - Перезапустить контейнеры"
	@echo "  make logs        - Показать логи контейнеров"
	@echo "  make build       - Пересобрать контейнеры"
	@echo ""
	@echo "Бэкапы:"
	@echo "  make backup      - Создать бэкап MongoDB сейчас"
	@echo "  make backup-list - Показать список всех бэкапов"
	@echo "  make backup-logs - Показать историю бэкапов"
	@echo "  make backup-status   - Статус systemd таймера"
	@echo "  make backup-restore  - Восстановить из бэкапа"
	@echo ""
	@echo "Установка автобэкапов:"
	@echo "  make backup-install   - Установить systemd таймер"
	@echo "  make backup-uninstall - Удалить systemd таймер"
	@echo ""
	@echo "Перенос на Linux сервер без интернета:"
	@echo "  make pack     - Упаковать проект + Docker образы (для Linux amd64)"
	@echo "  make unpack   - Загрузить Docker образы из архива"
	@echo "  make up-pack  - Запустить из готовых образов"
	@echo ""

#===============================================================================
# DOCKER
#===============================================================================

up:
	@echo "Starting containers..."
	docker-compose up -d

down:
	@echo "Stopping containers..."
	docker-compose down

restart:
	@echo "Restarting containers..."
	docker-compose restart

logs:
	docker-compose logs -f

build:
	@echo "Building containers..."
	docker-compose build

#===============================================================================
# БЭКАПЫ
#===============================================================================

backup:
	@echo "Creating MongoDB backup..."
	@$(BACKUP_SCRIPT) backup

backup-list:
	@$(BACKUP_SCRIPT) list

backup-logs:
	@$(BACKUP_SCRIPT) logs 30

backup-status:
	@echo "Systemd Timer Status:"
	@systemctl status mongodb-backup.timer 2>/dev/null || echo "Timer not installed. Run 'make backup-install' to set up automatic backups."
	@echo ""
	@echo "Next scheduled run:"
	@systemctl list-timers mongodb-backup.timer 2>/dev/null || echo "Timer not active"

backup-restore:
	@echo "Available backups:"
	@$(BACKUP_SCRIPT) list
	@echo ""
	@read -p "Enter backup filename (e.g., backup_2025-01-24_03-00.tar.gz): " file; \
	$(BACKUP_SCRIPT) restore "backups/$$file"

#===============================================================================
# SYSTEMD TIMER (требует sudo)
#===============================================================================

backup-install:
	@echo "Installing systemd timer for automatic backups..."
	@echo ""
	@echo "[Unit]" | sudo tee $(SYSTEMD_DIR)/mongodb-backup.service > /dev/null
	@echo "Description=MongoDB Backup Service" | sudo tee -a $(SYSTEMD_DIR)/mongodb-backup.service > /dev/null
	@echo "After=docker.service" | sudo tee -a $(SYSTEMD_DIR)/mongodb-backup.service > /dev/null
	@echo "Requires=docker.service" | sudo tee -a $(SYSTEMD_DIR)/mongodb-backup.service > /dev/null
	@echo "" | sudo tee -a $(SYSTEMD_DIR)/mongodb-backup.service > /dev/null
	@echo "[Service]" | sudo tee -a $(SYSTEMD_DIR)/mongodb-backup.service > /dev/null
	@echo "Type=oneshot" | sudo tee -a $(SYSTEMD_DIR)/mongodb-backup.service > /dev/null
	@echo "WorkingDirectory=$(PROJECT_DIR)" | sudo tee -a $(SYSTEMD_DIR)/mongodb-backup.service > /dev/null
	@echo "ExecStart=$(PROJECT_DIR)/scripts/mongodb-backup.sh backup" | sudo tee -a $(SYSTEMD_DIR)/mongodb-backup.service > /dev/null
	@echo "User=root" | sudo tee -a $(SYSTEMD_DIR)/mongodb-backup.service > /dev/null
	@echo "StandardOutput=journal" | sudo tee -a $(SYSTEMD_DIR)/mongodb-backup.service > /dev/null
	@echo "StandardError=journal" | sudo tee -a $(SYSTEMD_DIR)/mongodb-backup.service > /dev/null
	@echo "" | sudo tee -a $(SYSTEMD_DIR)/mongodb-backup.service > /dev/null
	@echo "[Install]" | sudo tee -a $(SYSTEMD_DIR)/mongodb-backup.service > /dev/null
	@echo "WantedBy=multi-user.target" | sudo tee -a $(SYSTEMD_DIR)/mongodb-backup.service > /dev/null
	@echo "[Unit]" | sudo tee $(SYSTEMD_DIR)/mongodb-backup.timer > /dev/null
	@echo "Description=Daily MongoDB Backup Timer" | sudo tee -a $(SYSTEMD_DIR)/mongodb-backup.timer > /dev/null
	@echo "" | sudo tee -a $(SYSTEMD_DIR)/mongodb-backup.timer > /dev/null
	@echo "[Timer]" | sudo tee -a $(SYSTEMD_DIR)/mongodb-backup.timer > /dev/null
	@echo "OnCalendar=*-*-* 03:00:00" | sudo tee -a $(SYSTEMD_DIR)/mongodb-backup.timer > /dev/null
	@echo "Persistent=true" | sudo tee -a $(SYSTEMD_DIR)/mongodb-backup.timer > /dev/null
	@echo "RandomizedDelaySec=300" | sudo tee -a $(SYSTEMD_DIR)/mongodb-backup.timer > /dev/null
	@echo "" | sudo tee -a $(SYSTEMD_DIR)/mongodb-backup.timer > /dev/null
	@echo "[Install]" | sudo tee -a $(SYSTEMD_DIR)/mongodb-backup.timer > /dev/null
	@echo "WantedBy=timers.target" | sudo tee -a $(SYSTEMD_DIR)/mongodb-backup.timer > /dev/null
	@sudo systemctl daemon-reload
	@sudo systemctl enable mongodb-backup.timer
	@sudo systemctl start mongodb-backup.timer
	@echo ""
	@echo "Automatic backups installed successfully!"
	@echo "Backups will run daily at 03:00"
	@echo ""
	@echo "Useful commands:"
	@echo "  make backup-status  - Check timer status"
	@echo "  make backup         - Run backup manually"
	@echo "  journalctl -u mongodb-backup.service - View backup logs"

backup-uninstall:
	@echo "Removing systemd timer..."
	@sudo systemctl stop mongodb-backup.timer 2>/dev/null || true
	@sudo systemctl disable mongodb-backup.timer 2>/dev/null || true
	@sudo rm -f $(SYSTEMD_DIR)/mongodb-backup.service
	@sudo rm -f $(SYSTEMD_DIR)/mongodb-backup.timer
	@sudo systemctl daemon-reload
	@echo "Systemd timer removed."
	@echo "Note: Your existing backups in ./backups/ are preserved."

#===============================================================================
# УПАКОВКА ДЛЯ ПЕРЕНОСА (без интернета)
#===============================================================================

PACK_NAME := miit-pack-$(shell date +%Y%m%d).tar.gz
PLATFORM := linux/amd64

pack:
	@echo "Упаковка проекта для Linux (amd64)..."
	@echo ""
	@echo "1. Сборка API образа для Linux amd64..."
	@docker buildx build --platform $(PLATFORM) -t miit-api:amd64 --load .
	@echo ""
	@echo "2. Скачивание MongoDB для Linux amd64..."
	@docker pull --platform $(PLATFORM) mongo:4.4.6
	@echo ""
	@echo "3. Сохранение Docker образов..."
	@mkdir -p .pack-tmp
	@echo "Сохранение MongoDB (amd64)..."
	@docker save mongo:4.4.6 | gzip > .pack-tmp/mongo-4.4.6.tar.gz
	@echo "Сохранение API (amd64)..."
	@docker save miit-api:amd64 | gzip > .pack-tmp/miit-api.tar.gz
	@echo ""
	@echo "4. Создание архива..."
	@tar --exclude='backups/*.tar.gz' \
		--exclude='db/data' \
		--exclude='db' \
		--exclude='.venv' \
		--exclude='__pycache__' \
		--exclude='.git' \
		--exclude='*.pyc' \
		--exclude='.env' \
		--exclude='miit-pack-*.tar.gz' \
		-cvzf $(PACK_NAME) \
		.
	@rm -rf .pack-tmp
	@echo ""
	@echo "=========================================="
	@echo "Готово! Создан файл: $(PACK_NAME)"
	@echo "Размер: $$(ls -lh $(PACK_NAME) | awk '{print $$5}')"
	@echo ""
	@echo "Для установки на Linux сервере:"
	@echo "  1. Скопировать $(PACK_NAME) на сервер"
	@echo "  2. tar -xzf $(PACK_NAME) && cd miit"
	@echo "  3. make unpack"
	@echo "  4. cp .env.example .env && nano .env"
	@echo "  5. make up-pack"
	@echo "=========================================="

unpack:
	@echo "Загрузка Docker образов..."
	@if [ ! -d ".pack-tmp" ]; then \
		echo "Ошибка: папка .pack-tmp не найдена."; \
		echo "Сначала распакуйте архив: tar -xzf miit-pack-*.tar.gz"; \
		exit 1; \
	fi
	@echo ""
	@for img in .pack-tmp/*.tar.gz; do \
		echo "Loading $$img..."; \
		gunzip -c "$$img" | docker load; \
	done
	@echo ""
	@echo "Переименование образа API..."
	@docker tag miit-api:amd64 miit-api:latest 2>/dev/null || true
	@rm -rf .pack-tmp
	@echo ""
	@echo "=========================================="
	@echo "Готово! Образы загружены."
	@echo ""
	@echo "Следующие шаги:"
	@echo "  1. Создайте .env: cp .env.example .env"
	@echo "  2. Отредактируйте .env (пароли)"
	@echo "  3. Запустите: make up-pack"
	@echo "=========================================="

up-pack:
	@echo "Запуск из готовых образов..."
	docker-compose -f docker-compose.pack.yml up -d

down-pack:
	docker-compose -f docker-compose.pack.yml down
