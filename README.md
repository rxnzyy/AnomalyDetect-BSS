# Киберимунная система обнаружения аномалий

Проект представляет собой распределённую систему мониторинга и обнаружения аномалий, построенную по **киберимунному принципу** (cyberimmune approach). Все компоненты изолированы, общаются только через брокер сообщений Apache Kafka, каждое сообщение подписывается HMAC для обеспечения целостности и подлинности.

## Основные возможности

- Генерация потока событий (логи, метрики, действия пользователей)
- Обнаружение аномалий: частотные всплески, редкие типы событий
- Отправка уведомлений в Telegram при обнаружении аномалии
- Визуализация метрик в Grafana
- Полная изоляция компонентов (Docker-контейнеры)
- HMAC-подпись каждого сообщения
- Минимизация поверхности атаки (нет прямых HTTP-входов, всё через Kafka)

## 📁 Структура проекта

```
anomaly-detection/
├── generator/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── generator.py
├── detector/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── detector.py
├── alerter/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── alerter.py
├── common/
│   ├── __init__.py
│   └── hmac_auth.py
├── grafana/
│   └── provisioning/
│       ├── datasources/
│       │   └── influxdb.yml
│       └── dashboards/
│           ├── dashboard.yml
│           └── anomaly_dashboard.json
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

### Компоненты

| Компонент | Роль | Технологии |
|-----------|------|-------------|
| **Generator** | Эмулирует легитимный трафик и редкие аномалии | Python, Kafka Producer |
| **Kafka** | Маршрутизация сообщений, буферизация, воспроизведение | Apache Kafka, Zookeeper |
| **Detector** | Анализирует поток, проверяет HMAC, ищет аномалии | Python, Kafka Consumer/Producer |
| **Alerter** | Получает аномалии, отправляет уведомления | Python, requests, Telegram Bot API |
| **InfluxDB** | Хранит метрики для визуализации | InfluxDB 2.x |
| **Grafana** | Отображает дашборды с событиями и аномалиями | Grafana |

## Киберимунные принципы

- **Изоляция**: каждый сервис в отдельном контейнере, общая сеть только для Kafka.
- **Минимальные привилегии**: ни один сервис не имеет shell (slim-образы), не работает от root.
- **Целостность данных**: все сообщения подписаны HMAC-SHA256, подпись проверяется перед обработкой.
- **Минимизация поверхности атаки**: нет публичных портов у сервисов, кроме Kafka (9092), Grafana (3000), InfluxDB (8086) для отладки.
- **Разделение ответственности**: Alerter не имеет доступа к сырым событиям.

## Установка и запуск

### Требования

- Docker Desktop (Windows/Mac) или Docker Engine + Docker Compose (Linux)
- Git
- Telegram аккаунт (опционально, для уведомлений)

### Шаг 1: Клонирование репозитория

```bash
git clone https://github.com/rxnzyy/AnomalyDetect-BSS.git
cd anomaly-detection
```

### Шаг 2: Настройка секретов

Скопируйте файл `.env.example` в `.env` и отредактируйте его:

```bash
cp .env.example .env
```

Заполните следующие переменные (обязательно измените `HMAC_SECRET` на случайную строку):

```ini
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
HMAC_SECRET=ваш_случайный_ключ_минимум_32_символа
TELEGRAM_BOT_TOKEN=токен_от_BotFather
TELEGRAM_CHAT_ID=ваш_chat_id
```

> **Важно:** файл `.env` добавлен в `.gitignore` и не попадёт в репозиторий.

### Шаг 3: Создание Telegram бота (опционально)

1. Найти в Telegram **@BotFather**, отправить `/newbot`
2. Получить токен вида `7234567890:AAGk7T3...`
3. Найти **@AnoAlertBot**, отправить `/start` — получить `chat_id`
4. Вставить значения в `.env`

### Шаг 4: Запуск

```bash
docker-compose up --build
```

После запуска вы увидите логи от всех сервисов. Пример:

```
generator    | [Generator] Sent: login_success from app-server-1 value=42
detector     | [Detector] !! ANOMALY: login_failed occurred 35 times in last 5s
alerter      | [Alerter] Alert: !! SECURITY ALERT ...
```

### Шаг 5: Просмотр дашборда Grafana

Откройте браузер: [http://localhost:3000](http://localhost:3000)  
Логин: `admin`  
Пароль: `admin`

Дашборд `Anomaly Detection Dashboard` загрузится автоматически через provisioning.

## Тестирование аномалий

Генератор эмулирует аномалии с вероятностью 5%. Для принудительного теста:

1. Временно измените `random.random() < 0.05` на `random.random() < 0.5` в `generator/generator.py`
2. Пересоберите и запустите:
   ```bash
   docker-compose up --build
   ```
3. В течение 10–20 секунд детектор обнаружит аномалию и алертер отправит сообщение в Telegram.


## Команды управления

| Действие | Команда |
|----------|---------|
| Запустить все сервисы | `docker-compose up` |
| Запустить в фоне | `docker-compose up -d` |
| Остановить все | `docker-compose down` |
| Остановить и удалить volumes | `docker-compose down -v` |
| Посмотреть логи детектора | `docker logs -f detector` |
| Перезапустить конкретный сервис | `docker-compose restart alerter` |
| Зайти в контейнер (отладка) | `docker exec -it generator bash` |


##  Лицензия

MIT (свободное использование, модификация, распространение).

##  Авторы

- Ефремов Роман (efremov.r.a@edu.mirea.ru)
- Бычков Oлег (bychkov.o.i@edu.mirea.ru)

Проект выполнен в рамках курса по киберимунным системам и конструктивной информационной безопасности.


