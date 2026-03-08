#!/usr/bin/env bash
# Zatrzymuje skrypt, jeśli jakakolwiek komenda zwróci błąd
set -e

IMAGE_NAME="ardusub_gazebo_env"
# Pobiera dokładną ścieżkę folderu, w którym znajduje się ten skrypt (czyli Twoje repozytorium)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== 1. Budowanie obrazu Docker: $IMAGE_NAME ==="
# Docker użyje cache'u, więc jeśli nic nie zmienisz w Dockerfile, potrwa to sekundę
docker build -t "$IMAGE_NAME" "$PROJECT_ROOT"

echo "=== 2. Konfiguracja wyświetlania grafiki (X11) ==="
# Zezwala na wyświetlanie okien z kontenera na Twoim ekranie
xhost +local:root > /dev/null 2>&1 || true

# Automatyczny wybór akceleracji sprzętowej
GPU_FLAG="--device=/dev/dri"
if command -v nvidia-smi &> /dev/null; then
    echo "=== Wykryto kartę NVIDIA. Używam akceleracji CUDA/NVENC ==="
    GPU_FLAG="--gpus all"
else
    echo "=== Używam standardowej akceleracji wideo (/dev/dri) ==="
fi

echo "=== 3. Uruchamianie środowiska ==="
# Odpalamy kontener z odpowiednimi flagami sieciowymi i podmontowanym repozytorium
docker run -it --rm \
    --net=host \
    --env="DISPLAY=$DISPLAY" \
    --env="QT_X11_NO_MITSHM=1" \
    --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
    --volume="$PROJECT_ROOT:/workspace/BS_oceans:rw" \
    $GPU_FLAG \
    "$IMAGE_NAME" \
    bash
