FROM python:3.10-slim

WORKDIR /app

# 👉 Устанавливаем локали
RUN apt-get update && apt-get install -y locales \
    && sed -i '/ru_RU.UTF-8/s/^# //g' /etc/locale.gen \
    && locale-gen \
    && apt-get clean

# 👉 Устанавливаем переменные окружения
ENV LANG=ru_RU.UTF-8
ENV LC_ALL=ru_RU.UTF-8

COPY . /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Делаем скрипт запуска исполняемым и исправляем окончания строк
RUN sed -i 's/\r$//' start.sh && chmod +x start.sh

# Открываем порт для Flask
EXPOSE 80

CMD ["./start.sh"]
