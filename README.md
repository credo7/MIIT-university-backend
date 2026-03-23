# MIIT Project

## Make-команды

### Docker

| Команда | Описание |
|---------|----------|
| `make up` | Запустить все контейнеры |
| `make down` | Остановить все контейнеры |
| `make restart` | Перезапустить контейнеры |
| `make logs` | Показать логи контейнеров |
| `make build` | Пересобрать контейнеры |

### Бэкапы MongoDB

| Команда | Описание |
|---------|----------|
| `make backup` | Создать бэкап сейчас |
| `make backup-list` | Показать список всех бэкапов |
| `make backup-logs` | Показать историю бэкапов |
| `make backup-restore` | Восстановить из бэкапа |

### Автоматические бэкапы (systemd)

| Команда | Описание |
|---------|----------|
| `make backup-install` | Установить systemd таймер (бэкап каждый день в 03:00) |
| `make backup-uninstall` | Удалить systemd таймер |
| `make backup-status` | Статус таймера |

### Перенос на Linux сервер без интернета

| Команда | Описание |
|---------|----------|
| `make pack` | Упаковать проект + Docker образы для Linux (amd64) |
| `make unpack` | Загрузить Docker образы из архива |
| `make up-pack` | Запустить из готовых образов |
| `make down-pack` | Остановить |

**Инструкция:**

На компе с интернетом (Mac/Linux):
```bash
make pack
# Создаст файл miit-pack-20260124.tar.gz (~500MB)
# Образы собираются для Linux amd64
```

На университетском сервере (Linux, без интернета):
```bash
# 1. Скопировать архив (флешка)
# 2. Распаковать
tar -xzf miit-pack-20260124.tar.gz
cd miit

# 3. Загрузить Docker образы
make unpack

# 4. Настроить
cp .env.example .env
nano .env  # изменить пароли

# 5. Запустить
make up-pack
```

## Стратегия бэкапов

Хранится 8 бэкапов:
- 2 ежедневных (вчера, позавчера)
- 2 еженедельных (1 и 2 недели назад)
- 4 месячных (покрывают семестр + летние каникулы)

Формат имени: `backup_2025-01-24_03-00.tar.gz`

## Логи бэкапов

Файл: `backups/backup_logs.txt`

```
[2025-01-24 03:00:15] SUCCESS | backup_2025-01-24_03-00.tar.gz | 12.5MB | 3s | Free: 45.2GB
[2025-01-23 03:00:12] SUCCESS | backup_2025-01-23_03-00.tar.gz | 12.3MB | 3s | Free: 45.8GB
```

## Восстановление из бэкапа

```bash
# Интерактивно через make
make backup-restore

# Или вручную
tar -xzf backups/backup_2025-01-24_03-00.tar.gz -C /tmp/
docker exec -i mongodb mongorestore --drop /tmp/dump/
```

## Установка на сервере

```bash
# 1. Запустить контейнеры
make up

# 2. Установить автобэкапы
make backup-install

# 3. Проверить статус
make backup-status
```

---

## Обновление существующего сервера (без потери данных)

Если система уже запущена и нужно обновить код + сменить пароль MongoDB:

### Шаг 1: Создать бэкап текущих данных

```bash
# На сервере, в папке текущего проекта

# Узнать текущий пароль MongoDB
cat .env | grep MONGO_PASSWORD

# Сделать бэкап вручную (используя ТЕКУЩИЙ пароль)
docker exec mongodb mongodump \
  --username admin \
  --password ТЕКУЩИЙ_ПАРОЛЬ \
  --authenticationDatabase admin \
  --out /tmp/backup_before_update

# Скопировать бэкап из контейнера
docker cp mongodb:/tmp/backup_before_update ./backup_before_update

# Проверить, что бэкап создался
ls -la backup_before_update/
```

### Шаг 2: Остановить текущие контейнеры

```bash
docker-compose down
# или
make down
```

### Шаг 3: Сменить пароль MongoDB

**Важно:** Данные MongoDB хранятся в `./db/data/`. Чтобы сменить пароль без потери данных:

```bash
# 1. Временно запустить MongoDB без авторизации
docker run -d --name mongo-temp \
  -v $(pwd)/db/data:/data/db \
  mongo:4.4.6 \
  mongod --noauth

# 2. Подождать 5 секунд пока запустится
sleep 5

# 3. Сменить пароль пользователя admin
docker exec mongo-temp mongo admin --eval '
  db.changeUserPassword("admin", "НОВЫЙ_ПАРОЛЬ")
'

# 4. Остановить временный контейнер
docker stop mongo-temp
docker rm mongo-temp
```

### Шаг 4: Обновить .env файл

```bash
# Заменить старый пароль на новый
nano .env

# Должно быть:
# MONGO_USERNAME=admin
# MONGO_PASSWORD=НОВЫЙ_ПАРОЛЬ
# DATABASE_URL=mongodb://admin:НОВЫЙ_ПАРОЛЬ@mongodb:27017
```

### Шаг 5: Обновить код (если нужно)

> **Примечание:** Скрипт бэкапа автоматически читает пароль из .env файла, поэтому его редактировать не нужно.

**Вариант A: Сервер с интернетом**
```bash
git pull origin main
make build
make up
```

**Вариант B: Сервер без интернета (через pack)**
```bash
# 1. На компе с интернетом:
make pack

# 2. Скопировать архив на сервер (флешка)

# 3. На сервере:
# Сохранить текущий .env
cp .env .env.backup

# Распаковать новый код
tar -xzf miit-pack-*.tar.gz --strip-components=1

# Вернуть .env
cp .env.backup .env

# Загрузить Docker образы
make unpack

# Запустить
make up-pack
```

### Шаг 6: Проверить работоспособность

```bash
# Проверить статус контейнеров
docker ps

# Проверить логи
make logs

# Проверить API
curl http://localhost/docs
```

### Шаг 7: Настроить автоматические бэкапы

```bash
# Установить systemd таймер
make backup-install

# Проверить статус
make backup-status

# Сделать тестовый бэкап
make backup

# Проверить, что бэкап создался
make backup-list
```

### Шаг 8: Удалить временный бэкап

```bash
# Если всё работает, можно удалить
rm -rf backup_before_update/
```

---

## Полный чеклист для обновления

- [ ] Создать бэкап существующих данных
- [ ] Остановить контейнеры
- [ ] Сменить пароль в MongoDB
- [ ] Обновить .env (пароль автоматически используется скриптом бэкапа)
- [ ] Обновить код (git pull или pack/unpack)
- [ ] Запустить контейнеры
- [ ] Проверить API работает
- [ ] Установить systemd таймер для бэкапов
- [ ] Сделать тестовый бэкап
- [ ] Удалить временные файлы
