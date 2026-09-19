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

# Domyślne limity PHP (2M/8M) są za małe na wgrywanie nagrań audio
# (godziny nagrania to nierzadko 100-300 MB) — patrz RecordingController.
RUN { \
        echo 'upload_max_filesize = 1G'; \
        echo 'post_max_size = 1G'; \
        echo 'max_execution_time = 600'; \
        echo 'max_input_time = 600'; \
    } > /usr/local/etc/php/conf.d/uploads.ini

COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

WORKDIR /app

COPY . .
RUN composer install --no-interaction --no-progress --optimize-autoloader
