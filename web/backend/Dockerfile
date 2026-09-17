# Backend API (Symfony) — Etap 8, Krok 2, Faza 0/1. Kontener PHP-FPM,
# serwowany przez nginx (patrz web/nginx/).
FROM php:8.4-fpm-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
        libicu-dev \
        libzip-dev \
        unzip \
        git \
    && docker-php-ext-install pdo_mysql intl opcache zip \
    && rm -rf /var/lib/apt/lists/*

COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

WORKDIR /app

COPY . .
RUN composer install --no-interaction --no-progress --optimize-autoloader
