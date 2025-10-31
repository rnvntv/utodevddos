# 🚀 Быстрый старт для стресс-тестирования

## 📋 Краткая справка

### Основные команды:

#### 1. Запуск сервера:
```bash
python3 launcher.py server <URL_ЦЕЛИ> \
    -p 6666 \              # Порт для клиентов (по умолчанию 6666)
    -m 50 \                # Макс. количество ботов (по умолчанию 100)
    --persistent False     # Не продолжать после падения цели
```

**Примеры:**
```bash
# Локальный сайт
python3 launcher.py server http://localhost:8000

# Удаленный сайт
python3 launcher.py server https://test.example.com

# С настройками
python3 launcher.py server https://test.example.com -p 6666 -m 100
```

#### 2. Запуск клиентов:
```bash
python3 launcher.py client \
    -r localhost \         # IP сервера (по умолчанию localhost)
    -p 6666 \              # Порт сервера (по умолчанию 6666)
    -n 4 \                 # Количество процессов (по умолчанию = CPU ядра)
    -s                     # Скрытый режим (только ошибки)
```

**Примеры:**
```bash
# Локальный сервер, количество = CPU ядра
python3 launcher.py client

# Удаленный сервер, 8 ботов
python3 launcher.py client -r 192.168.1.100 -p 6666 -n 8

# Скрытый режим
python3 launcher.py client -s
```

---

## 🎯 Типичные сценарии

### Сценарий 1: Тестирование локального сайта

```bash
# Терминал 1: Запуск сервера
python3 launcher.py server http://localhost:8000 -m 50

# Терминал 2: Запуск клиентов
python3 launcher.py client -n 4
```

### Сценарий 2: Тестирование удаленного сайта

```bash
# Терминал 1: Запуск сервера
python3 launcher.py server https://test.example.com -m 100

# Терминал 2: Запуск клиентов
python3 launcher.py client -r <IP_СЕРВЕРА> -n 8
```

### Сценарий 3: Распределенное тестирование (несколько машин)

```bash
# Машина 1 (Сервер, IP: 192.168.1.100)
python3 launcher.py server https://test.example.com -m 200

# Машина 2, 3, 4 (Клиенты)
python3 launcher.py client -r 192.168.1.100 -n 8
```

---

## 📊 Интерпретация результатов

### Коды статусов:

- **200 (NO_LUCK)** → Сайт работает нормально ✅
- **400 (ANTI_DDOS)** → Обнаружена защита от DDoS ⚠️
- **403 (FORBIDDEN)** → Доступ запрещен ⚠️
- **404 (NOT_FOUND)** → URL не найден ❌
- **429** → Rate Limiting работает ✅
- **500+ (PWNED)** → Сайт перегружен/упал ⚠️

---

## 🔧 Параметры для настройки нагрузки

### Легкая нагрузка (для тестирования защиты):
```bash
python3 launcher.py server https://test.example.com -m 10
python3 launcher.py client -n 2
```
**Результат:** ~1,000 запросов

### Средняя нагрузка:
```bash
python3 launcher.py server https://test.example.com -m 50
python3 launcher.py client -n 4
```
**Результат:** ~10,000 запросов

### Высокая нагрузка:
```bash
python3 launcher.py server https://test.example.com -m 100
python3 launcher.py client -n 8
```
**Результат:** ~40,000 запросов

### Очень высокая нагрузка (распределенная):
```bash
# 4 машины по 8 ботов каждая = 32 бота
python3 launcher.py server https://test.example.com -m 50
# На каждой машине:
python3 launcher.py client -r <IP_СЕРВЕРА> -n 8
```
**Результат:** ~16,000 запросов × 32 = ~512,000 запросов

---

## 🛑 Остановка теста

### Остановка клиентов:
```bash
# Нажмите Ctrl+C в терминале с клиентами
```

### Остановка сервера:
```bash
# Нажмите Ctrl+C в терминале с сервером
# Или введите 'quit' для выхода
```

### Принудительная остановка:
```bash
# Остановка всех процессов
pkill -f launcher.py

# Проверка процессов
ps aux | grep launcher.py
```

---

## 📈 Мониторинг во время теста

### Мониторинг системы:
```bash
# CPU и память
top

# Сеть
iftop -i eth0

# Дисковый ввод-вывод
iostat -x 1
```

### Мониторинг веб-сервера (если у вас есть доступ):
```bash
# Nginx
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Apache
tail -f /var/log/apache2/access.log
tail -f /var/log/apache2/error.log
```

---

## ⚠️ Важные напоминания

1. ✅ **Тестируйте только свои сайты**
2. ✅ **Используйте тестовую среду (staging)**
3. ✅ **Предупреждайте администраторов**
4. ✅ **Проводите тесты в нерабочее время**
5. ✅ **Ограничивайте нагрузку**
6. ❌ **Не используйте против чужих сайтов**

---

## 🆘 Решение проблем

### Проблема: "ModuleNotFoundError: No module named 'aiohttp'"
**Решение:**
```bash
python3 -m pip install --break-system-packages -r requirements_linux.txt
```

### Проблема: "Connection refused" при подключении клиента
**Решение:**
- Проверьте, что сервер запущен
- Проверьте правильность IP/порта
- Проверьте firewall

### Проблема: Клиенты не получают команды
**Решение:**
- Проверьте соединение: `netstat -tulpn | grep 6666`
- Перезапустите сервер и клиенты

---

## 📞 Полезные команды

```bash
# Проверка версии Python
python3 --version

# Проверка установленных пакетов
pip list | grep aiohttp

# Проверка портов
netstat -tulpn | grep 6666

# Мониторинг процессов
ps aux | grep python3
```

---

**Удачи в тестировании! 🚀**

