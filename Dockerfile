# Obraz do uruchamiania pipeline'u SMDM (transkrypcja, diaryzacja, OCR,
# generowanie projektu sprawozdania) przez CLI z wnętrza kontenera —
# `docker compose exec app python scripts/...`. Wymaga hosta z GPU NVIDIA
# i NVIDIA Container Toolkit (na Windows: Docker Desktop z backendem WSL2 +
# włączonym wsparciem GPU — patrz docs/INSTALLATION.md).
#
# Obraz NIE zawiera modelu Ollama — ten działa w osobnym kontenerze
# (docker-compose.yml, usługa "ollama"), zgodnie z ustaleniem w
# docs/ROADMAP.md (Etap 8).
FROM python:3.13-slim-bookworm

# ffmpeg — dekodowanie audio (WhisperX, extract_speaker_samples.py).
# tesseract-ocr + pakiet polski — OCR skanów (pdf_to_markdown.py).
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        tesseract-ocr \
        tesseract-ocr-pol \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
        --extra-index-url https://download.pytorch.org/whl/cu128

# Osobna warstwa/plik dla zależności job_worker.py (Faza 3) — patrz komentarz
# w requirements-web.txt: to małe, częściej zmieniane zależności, nie mają
# unieważniać drogiej warstwy powyżej (torch/whisperx).
COPY requirements-web.txt .
RUN pip install --no-cache-dir -r requirements-web.txt

COPY scripts/ scripts/
COPY config/ config/
COPY prompts/ prompts/

# Kontener ma żyć w tle, żeby dało się do niego wejść po CLI
# (`docker compose exec app python scripts/transcribe.py ...`) —
# odpowiada to obecnemu sposobowi pracy (jeden skrypt na raz, ręcznie).
CMD ["sleep", "infinity"]
