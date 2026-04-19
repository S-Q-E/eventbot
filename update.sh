#!/bin/bash
git pull
docker compose up --build -d  # Пересобрать образ, если изменился Dockerfile

