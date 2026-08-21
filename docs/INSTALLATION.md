# Instalacja i konfiguracja

## Status

Dokumentacja instalacji jest obecnie tworzona.

## Wymagane komponenty

- Windows 11
- Git
- Python
- FFmpeg
- NVIDIA CUDA / sterowniki
- PyTorch
- WhisperX
- Ollama
- Model językowy

## 1. Git

```powershell
winget install --id Git.Git -e --source winget
```

## 2. Python

```powershell
winget install Python.Python.3.13

python --version
py --version

python -m pip --version

python -m venv .venv

Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

.\.venv\Scripts\Activate.ps1
```

## 3. Nvidia

```powershell
nvidia-smi
```

## 4. FFmpeg

```powershell
winget install Gyan.FFmpeg

ffmpeg -version
```

## 5. PyTorch

Potrzebne jest środowisko gdzie następująca komneda daje przykładowo to co poniżej:

```
python -c "import torch; print('PyTorch:', torch.__version__); print('CUDA build:', torch.version.cuda); print('CUDA available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'BRAK')"
```

```
PyTorch: 2.x.x+cu128
CUDA build: 12.8
CUDA available: True
GPU: NVIDIA GeForce RTX 4060 Laptop GPU
```

instalacja pytorch:

```powershell
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

python -m pip install torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu128
```

## 6. WhisperX

```powershell
python -m pip install whisperx==3.8.6

python -m pip show whisperx
```

### hf_xet (szybsze pobieranie modeli z Hugging Face)

Bez tego pakietu Hugging Face Hub pobiera modele (np. Whisper, pyannote)
wolniejszą, zwykłą metodą HTTP i wypisuje ostrzeżenie o braku `hf_xet`.
Pakiet nie jest wymagany do działania, tylko przyspiesza pobieranie.

```powershell
python -m pip install hf_xet==1.6.0

python -m pip show hf_xet
```

### Token Hugging Face i dostęp do modeli pyannote (diaryzacja)

Diaryzacja (rozpoznawanie mówców) w WhisperX korzysta z modeli
`pyannote/segmentation-3.0` i `pyannote/speaker-diarization-3.1`, które są
„gated” — wymagają zalogowanego konta Hugging Face i ręcznej akceptacji
warunków, sam token nie wystarczy.

1. Załóż konto na https://huggingface.co (jeśli jeszcze nie masz).
2. Wygeneruj token dostępu: Settings → Access Tokens → New token, typ
   **Read**.
3. Zaakceptuj warunki użytkowania obu modeli (wymaga zalogowania w
   przeglądarce):
   - https://huggingface.co/pyannote/segmentation-3.0
   - https://huggingface.co/pyannote/speaker-diarization-3.1
4. Przekaż token do skryptu przez zmienną środowiskową — **nie
   hardkodować w kodzie** (zgodnie z `docs/AGENTS.md`):

```powershell
$env:HF_TOKEN = "hf_..."
```

Weryfikacja tokena i dostępu do plików modeli (przydatne przy
diagnozowaniu błędu 403):

```powershell
curl.exe -s -H "Authorization: Bearer $env:HF_TOKEN" https://huggingface.co/api/whoami-v2

curl.exe -s -o NUL -w "%{http_code}`n" -H "Authorization: Bearer $env:HF_TOKEN" https://huggingface.co/pyannote/segmentation-3.0/resolve/main/config.yaml
curl.exe -s -o NUL -w "%{http_code}`n" -H "Authorization: Bearer $env:HF_TOKEN" https://huggingface.co/pyannote/speaker-diarization-3.1/resolve/main/config.yaml
```

Kod `200` dla obu modeli oznacza, że warunki zaakceptowane i token działa.
Kod `403` oznacza brak akceptacji warunków (krok 3) — sam ważny token to
za mało.

## 5. Ollama

```powershell
winget install --id Ollama.Ollama -e --source winget
```

Instalator uruchamia serwer Ollama automatycznie jako usługę w tle (widoczna
ikona w zasobniku systemowym) — nie trzeba go uruchamiać ręcznie.

Po instalacji może być potrzebna nowa sesja terminala, żeby PATH się
odświeżył (`ollama` nie jest rozpoznawane w już otwartym oknie). Jeśli
problem się utrzymuje, `ollama.exe` domyślnie znajduje się w:

```
%LOCALAPPDATA%\Programs\Ollama\ollama.exe
```

Weryfikacja:

```powershell
ollama --version
ollama list
```

## 6. Model językowy

Wybrany model: `SpeakLeash/bielik-11b-v3.0-instruct:Q4_K_M` — dobre wsparcie
języka polskiego, kontekst do 32K, kwantyzacja Q4_K_M (6.7 GB) mieści się
niemal w całości w 8 GB VRAM (RTX 4060 Laptop).

```powershell
ollama pull SpeakLeash/bielik-11b-v3.0-instruct:Q4_K_M
```

Test podstawowy:

```powershell
ollama run SpeakLeash/bielik-11b-v3.0-instruct:Q4_K_M "Napisz jedno krótkie zdanie po polsku podsumowujące, czym jest spółdzielnia mieszkaniowa."
```

Podział obciążenia CPU/GPU dla wczytanego modelu:

```powershell
ollama ps
```

## 7. Test instalacji

Do uzupełnienia.

## Rozwiązywanie problemów

Problemy napotkane podczas pierwszej instalacji będą dokumentowane tutaj,
aby można było odtworzyć środowisko na innych komputerach.