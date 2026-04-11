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

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "bot.py"]
