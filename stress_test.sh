#!/bin/bash

# Скрипт для автоматического стресс-тестирования
# Использование: ./stress_test.sh <URL> <ВРЕМЯ_ТЕСТА_СЕКУНД>

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка аргументов
if [ $# -lt 1 ]; then
    echo -e "${RED}Ошибка: Не указан URL для тестирования${NC}"
    echo "Использование: $0 <URL> [ВРЕМЯ_ТЕСТА_СЕКУНД] [КОЛИЧЕСТВО_БОТОВ]"
    echo "Пример: $0 http://localhost:8000 60 4"
    exit 1
fi

URL=$1
TEST_DURATION=${2:-60}  # По умолчанию 60 секунд
NUM_BOTS=${3:-$(nproc)} # По умолчанию количество CPU ядер

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Стресс-тестирование сайта${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "URL: $URL"
echo "Длительность теста: $TEST_DURATION секунд"
echo "Количество ботов: $NUM_BOTS"
echo ""

# Проверка установки зависимостей
echo -e "${YELLOW}Проверка зависимостей...${NC}"
if ! python3 -c "import aiohttp" 2>/dev/null; then
    echo -e "${YELLOW}Установка зависимостей...${NC}"
    python3 -m pip install --break-system-packages -r requirements_linux.txt
fi

# Проверка доступности URL
echo -e "${YELLOW}Проверка доступности URL...${NC}"
if ! curl -s --head "$URL" > /dev/null; then
    echo -e "${RED}Ошибка: URL недоступен!${NC}"
    exit 1
fi
echo -e "${GREEN}URL доступен${NC}"
echo ""

# Запуск сервера в фоне
echo -e "${YELLOW}Запуск сервера UtodevBotnet...${NC}"
cd "$(dirname "$0")"
python3 launcher.py server "$URL" -m $((NUM_BOTS * 2)) > /tmp/utodevbotnet_server.log 2>&1 &
SERVER_PID=$!
sleep 2

# Проверка запуска сервера
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo -e "${RED}Ошибка: Не удалось запустить сервер${NC}"
    exit 1
fi
echo -e "${GREEN}Сервер запущен (PID: $SERVER_PID)${NC}"

# Запуск клиентов в фоне
echo -e "${YELLOW}Запуск клиентов...${NC}"
python3 launcher.py client -r localhost -n "$NUM_BOTS" > /tmp/utodevbotnet_client.log 2>&1 &
CLIENT_PID=$!
sleep 2

# Проверка запуска клиентов
if ! kill -0 $CLIENT_PID 2>/dev/null; then
    echo -e "${RED}Ошибка: Не удалось запустить клиентов${NC}"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi
echo -e "${GREEN}Клиенты запущены (PID: $CLIENT_PID)${NC}"
echo ""

# Мониторинг
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Запуск теста на $TEST_DURATION секунд...${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

START_TIME=$(date +%s)
END_TIME=$((START_TIME + TEST_DURATION))

# Функция для сбора метрик
collect_metrics() {
    local timestamp=$(date +%H:%M:%S)
    local response_time=$(curl -o /dev/null -s -w '%{time_total}' "$URL" 2>/dev/null || echo "N/A")
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
    local mem_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    
    printf "%-10s | Время отклика: %-8s | CPU: %-6s | RAM: %-6s%%\n" \
        "$timestamp" "${response_time}s" "$cpu_usage%" "$mem_usage%"
}

# Вывод заголовка
printf "%-10s | %-25s | %-10s | %-10s\n" "Время" "Время отклика" "CPU" "RAM"
printf "%-10s | %-25s | %-10s | %-10s\n" "--------" "-------------------------" "----------" "----------"

# Сбор метрик каждую секунду
while [ $(date +%s) -lt $END_TIME ]; do
    collect_metrics
    sleep 1
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Тест завершен${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Остановка процессов
echo -e "${YELLOW}Остановка процессов...${NC}"
kill $CLIENT_PID $SERVER_PID 2>/dev/null || true
sleep 2

# Финальная проверка доступности
echo -e "${YELLOW}Финальная проверка доступности сайта...${NC}"
if curl -s --head "$URL" > /dev/null; then
    echo -e "${GREEN}✅ Сайт доступен после теста${NC}"
else
    echo -e "${RED}❌ Сайт недоступен после теста${NC}"
fi

echo ""
echo -e "${GREEN}Логи сохранены в:${NC}"
echo "  Сервер: /tmp/utodevbotnet_server.log"
echo "  Клиенты: /tmp/utodevbotnet_client.log"
echo ""
echo -e "${GREEN}Тестирование завершено!${NC}"

