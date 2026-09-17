# Frontend (Nuxt) — Etap 8, Krok 2, Faza 0/1. Tryb dev (hot reload) — build
# produkcyjny to temat na później, gdy będzie potrzebny (patrz docs/DOCKER.md).
FROM node:22-bookworm

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY . .

ENV NUXT_HOST=0.0.0.0
ENV NUXT_PORT=3000
EXPOSE 3000

CMD ["npm", "run", "dev"]
