#!/bin/bash

#===============================================================================
# MongoDB Backup Script
# Создание бэкапов MongoDB с ротацией (daily/weekly/monthly)
#===============================================================================

set -e

# ===== КОНФИГУРАЦИЯ =====
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_DIR}/backups"
LOG_FILE="${BACKUP_DIR}/backup_logs.txt"
MONGO_CONTAINER="mongodb"

# MongoDB авторизация (из .env файла)
ENV_FILE="${PROJECT_DIR}/.env"
if [ -f "$ENV_FILE" ]; then
    MONGO_USER=$(grep -E "^MONGO_USERNAME=" "$ENV_FILE" | cut -d'=' -f2)
    MONGO_PASS=$(grep -E "^MONGO_PASSWORD=" "$ENV_FILE" | cut -d'=' -f2)
fi
# Fallback если .env не найден
MONGO_USER="${MONGO_USER:-admin}"
MONGO_PASS="${MONGO_PASS:-password}"

# Ротация бэкапов (8 бэкапов)
# - 2 ежедневных (вчера, позавчера)
# - 2 еженедельных (1 и 2 недели назад)
# - 4 месячных (покрывают семестр + каникулы)
DAILY_KEEP=2         # Хранить 2 ежедневных бэкапа
WEEKLY_KEEP=2        # Хранить 2 еженедельных бэкапа
MONTHLY_KEEP=4       # Хранить 4 месячных бэкапа (весь семестр)
WEEKLY_DAY=0         # День недели для weekly (0=вс, 1=пн, ...)
MONTHLY_DAY=1        # День месяца для monthly

# Предупреждения
LOW_DISK_THRESHOLD=5 # Порог предупреждения о низком месте (GB)

# ===== ФУНКЦИИ =====

# Получить свободное место на диске (в GB)
get_free_space() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        df -g "$BACKUP_DIR" 2>/dev/null | tail -1 | awk '{print $4}'
    else
        # Linux
        df -BG "$BACKUP_DIR" 2>/dev/null | tail -1 | awk '{print $4}' | sed 's/G//'
    fi
}

# Логирование
log() {
    local status="$1"
    local message="$2"
    local size="$3"
    local duration="$4"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local free_space=$(get_free_space)

    # Проверка на низкое место
    local low_space_warning=""
    if [ -n "$free_space" ] && [ "$free_space" -lt "$LOW_DISK_THRESHOLD" ] 2>/dev/null; then
        low_space_warning=" LOW DISK SPACE!"
    fi

    # Формирование записи
    local log_entry
    if [ "$status" = "SUCCESS" ]; then
        log_entry="[$timestamp] SUCCESS | $message | ${size} | ${duration}s | Free: ${free_space}GB${low_space_warning}"
    else
        log_entry="[$timestamp] FAILED  | $message | Free: ${free_space}GB${low_space_warning}"
    fi

    # Запись в лог
    echo "$log_entry" >> "$LOG_FILE"
    echo "$log_entry"
}

# Инициализация лог-файла
init_log() {
    if [ ! -f "$LOG_FILE" ]; then
        echo "================================================================================" > "$LOG_FILE"
        echo "MONGODB BACKUP LOG" >> "$LOG_FILE"
        echo "================================================================================" >> "$LOG_FILE"
    fi
}

# Получить размер файла в читаемом формате
get_file_size() {
    local file="$1"
    if [ -f "$file" ]; then
        ls -lh "$file" | awk '{print $5}'
    else
        echo "0B"
    fi
}

# Проверить, нужно ли сохранить бэкап как weekly
is_weekly_day() {
    [ "$(date +%w)" -eq "$WEEKLY_DAY" ]
}

# Проверить, нужно ли сохранить бэкап как monthly
is_monthly_day() {
    [ "$(date +%d)" -eq "$MONTHLY_DAY" ]
}

# Создать бэкап
create_backup() {
    local backup_name="backup_$(date '+%Y-%m-%d_%H-%M')"
    local temp_dir="/tmp/${backup_name}"
    local backup_file="${BACKUP_DIR}/${backup_name}.tar.gz"
    local start_time=$(date +%s)

    echo "Creating backup: $backup_name"

    # Проверить, работает ли контейнер MongoDB
    if ! docker ps --format '{{.Names}}' | grep -q "^${MONGO_CONTAINER}$"; then
        log "FAILED" "Error: MongoDB container '${MONGO_CONTAINER}' not running"
        return 1
    fi

    # Создать дамп MongoDB
    mkdir -p "$temp_dir"
    if ! docker exec "$MONGO_CONTAINER" mongodump \
        --username "$MONGO_USER" \
        --password "$MONGO_PASS" \
        --authenticationDatabase admin \
        --out /tmp/dump 2>&1; then
        log "FAILED" "Error: mongodump failed"
        rm -rf "$temp_dir"
        return 1
    fi

    # Скопировать дамп из контейнера
    if ! docker cp "${MONGO_CONTAINER}:/tmp/dump" "$temp_dir/" 2>/dev/null; then
        log "FAILED" "Error: Failed to copy dump from container"
        docker exec "$MONGO_CONTAINER" rm -rf /tmp/dump 2>/dev/null || true
        rm -rf "$temp_dir"
        return 1
    fi

    # Удалить временный дамп в контейнере
    docker exec "$MONGO_CONTAINER" rm -rf /tmp/dump 2>/dev/null || true

    # Сжать в tar.gz
    if ! tar -czf "$backup_file" -C "$temp_dir" . 2>/dev/null; then
        log "FAILED" "Error: Failed to create tar.gz archive"
        rm -rf "$temp_dir"
        return 1
    fi

    # Очистить временные файлы
    rm -rf "$temp_dir"

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local size=$(get_file_size "$backup_file")

    # Добавить метку типа бэкапа
    local backup_type=""
    if is_monthly_day; then
        backup_type=" [MONTHLY]"
    elif is_weekly_day; then
        backup_type=" [WEEKLY]"
    fi

    log "SUCCESS" "${backup_name}.tar.gz${backup_type}" "$size" "$duration"

    return 0
}

# Вспомогательная функция для получения epoch из даты
date_to_epoch() {
    local date_str="$1"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        date -j -f "%Y-%m-%d" "$date_str" +%s 2>/dev/null
    else
        date -d "$date_str" +%s 2>/dev/null
    fi
}

# Вспомогательная функция для получения дня недели из даты
date_to_dow() {
    local date_str="$1"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        date -j -f "%Y-%m-%d" "$date_str" +%w 2>/dev/null
    else
        date -d "$date_str" +%w 2>/dev/null
    fi
}

# Вспомогательная функция для получения дня месяца из даты
date_to_dom() {
    local date_str="$1"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        date -j -f "%Y-%m-%d" "$date_str" +%d 2>/dev/null
    else
        date -d "$date_str" +%d 2>/dev/null
    fi
}

# Ротация бэкапов
rotate_backups() {
    echo "Rotating backups..."

    local today=$(date +%Y-%m-%d)
    local current_day_of_week=$(date +%w)
    local current_day_of_month=$(date +%d)

    # Получить список всех бэкапов (отсортированы по дате, новые первыми)
    local all_backups=($(ls -t "${BACKUP_DIR}"/backup_*.tar.gz 2>/dev/null))

    if [ ${#all_backups[@]} -eq 0 ]; then
        echo "No backups found"
        return 0
    fi

    # Массивы для категоризации
    local daily_backups=()
    local weekly_backups=()
    local monthly_backups=()
    local to_delete=()

    for backup in "${all_backups[@]}"; do
        # Извлечь дату из имени файла
        local filename=$(basename "$backup")
        local backup_date=$(echo "$filename" | sed 's/backup_\([0-9-]*\)_.*/\1/')

        if [ -z "$backup_date" ]; then
            continue
        fi

        # Вычислить возраст бэкапа в днях
        local backup_epoch=$(date_to_epoch "$backup_date")
        local today_epoch=$(date +%s)
        local age_days=$(( (today_epoch - backup_epoch) / 86400 ))

        # Определить день недели и месяца для бэкапа
        local backup_dow=$(date_to_dow "$backup_date")
        local backup_dom=$(date_to_dom "$backup_date")

        # Категоризация
        if [ "$age_days" -lt "$DAILY_KEEP" ]; then
            # Ежедневные бэкапы (последние N дней)
            daily_backups+=("$backup")
        elif [ "$backup_dom" -eq "$MONTHLY_DAY" ] && [ ${#monthly_backups[@]} -lt "$MONTHLY_KEEP" ]; then
            # Месячный бэкап (1-е число месяца)
            monthly_backups+=("$backup")
        elif [ "$backup_dow" -eq "$WEEKLY_DAY" ] && [ ${#weekly_backups[@]} -lt "$WEEKLY_KEEP" ]; then
            # Еженедельный бэкап (воскресенье)
            weekly_backups+=("$backup")
        else
            # Подлежит удалению
            to_delete+=("$backup")
        fi
    done

    # Удалить лишние бэкапы
    for backup in "${to_delete[@]}"; do
        echo "Deleting old backup: $(basename "$backup")"
        rm -f "$backup"
    done

    echo "Rotation complete. Kept: ${#daily_backups[@]} daily, ${#weekly_backups[@]} weekly, ${#monthly_backups[@]} monthly"
}

# Показать список бэкапов
list_backups() {
    echo "================================================================================"
    echo "BACKUP LIST"
    echo "================================================================================"

    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A "${BACKUP_DIR}"/backup_*.tar.gz 2>/dev/null)" ]; then
        echo "No backups found"
        return 0
    fi

    local total_size=0

    for backup in $(ls -t "${BACKUP_DIR}"/backup_*.tar.gz 2>/dev/null); do
        local filename=$(basename "$backup")
        local size=$(get_file_size "$backup")

        # Получить размер в байтах (совместимо с macOS и Linux)
        local size_bytes
        if [[ "$OSTYPE" == "darwin"* ]]; then
            size_bytes=$(stat -f%z "$backup" 2>/dev/null)
            local mtime=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$backup" 2>/dev/null)
        else
            size_bytes=$(stat -c%s "$backup" 2>/dev/null)
            local mtime=$(stat -c "%y" "$backup" 2>/dev/null | cut -d'.' -f1)
        fi

        total_size=$((total_size + size_bytes))

        printf "%-45s %8s  %s\n" "$filename" "$size" "$mtime"
    done

    echo "--------------------------------------------------------------------------------"
    # Форматирование размера
    local total_human
    if command -v numfmt &> /dev/null; then
        total_human=$(numfmt --to=iec-i --suffix=B "$total_size" 2>/dev/null)
    else
        # Простое форматирование для macOS
        if [ "$total_size" -gt 1073741824 ]; then
            total_human="$((total_size / 1073741824))GB"
        elif [ "$total_size" -gt 1048576 ]; then
            total_human="$((total_size / 1048576))MB"
        else
            total_human="$((total_size / 1024))KB"
        fi
    fi
    echo "Total: $total_human"
    echo "Free space: $(get_free_space)GB"
}

# Показать логи
show_logs() {
    local lines=${1:-20}

    if [ ! -f "$LOG_FILE" ]; then
        echo "No log file found"
        return 0
    fi

    tail -n "$lines" "$LOG_FILE"
}

# Восстановление из бэкапа
restore_backup() {
    local backup_file="$1"

    if [ -z "$backup_file" ]; then
        echo "Usage: $0 restore <backup_file>"
        echo "Example: $0 restore backups/backup_2025-01-24_03-00.tar.gz"
        return 1
    fi

    if [ ! -f "$backup_file" ]; then
        echo "Error: Backup file not found: $backup_file"
        return 1
    fi

    echo "WARNING: This will DROP all existing data and restore from backup!"
    read -p "Are you sure? (yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        echo "Restore cancelled"
        return 0
    fi

    local temp_dir="/tmp/mongodb_restore_$$"
    mkdir -p "$temp_dir"

    echo "Extracting backup..."
    tar -xzf "$backup_file" -C "$temp_dir"

    echo "Copying to container..."
    docker cp "$temp_dir/dump" "${MONGO_CONTAINER}:/tmp/"

    echo "Restoring database..."
    docker exec "$MONGO_CONTAINER" mongorestore \
        --username "$MONGO_USER" \
        --password "$MONGO_PASS" \
        --authenticationDatabase admin \
        --drop /tmp/dump

    echo "Cleaning up..."
    docker exec "$MONGO_CONTAINER" rm -rf /tmp/dump
    rm -rf "$temp_dir"

    echo "Restore completed successfully!"
}

# ===== MAIN =====

# Создать директорию для бэкапов если не существует
mkdir -p "$BACKUP_DIR"

# Инициализировать лог
init_log

# Обработка команд
case "${1:-backup}" in
    backup)
        create_backup && rotate_backups
        ;;
    rotate)
        rotate_backups
        ;;
    list)
        list_backups
        ;;
    logs)
        show_logs "${2:-20}"
        ;;
    restore)
        restore_backup "$2"
        ;;
    help|--help|-h)
        echo "MongoDB Backup Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  backup   - Create a new backup and rotate old ones (default)"
        echo "  rotate   - Only rotate existing backups"
        echo "  list     - Show list of all backups"
        echo "  logs [n] - Show last n log entries (default: 20)"
        echo "  restore <file> - Restore from a backup file"
        echo "  help     - Show this help message"
        ;;
    *)
        echo "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
