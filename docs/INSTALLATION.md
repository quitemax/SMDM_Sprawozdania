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

## 5. Ollama

Do uzupełnienia.

## 6. Model językowy

Do uzupełnienia.

## 7. Test instalacji

Do uzupełnienia.

## Rozwiązywanie problemów

Problemy napotkane podczas pierwszej instalacji będą dokumentowane tutaj,
aby można było odtworzyć środowisko na innych komputerach.