#!/bin/sh
set -eu

model=${LLM_MODEL:-gemma2:2b}
host=${OLLAMA_HOST:-127.0.0.1:11434}
state_dir="$HOME/.ollama/ft-transcendance"
models_dir=

if [ -d "$HOME/goinfre" ]; then
    models_dir="$HOME/goinfre/$USER/ollama_models"
    mkdir -p "$models_dir"
fi

if [ -n "$models_dir" ]; then
    display_dir=$models_dir
    export OLLAMA_MODELS=$models_dir
else
    display_dir='Ollama default model directory'
    unset OLLAMA_MODELS
fi
export OLLAMA_HOST=$host

mkdir -p "$state_dir"

if command -v ollama >/dev/null 2>&1; then
    ollama_bin=$(command -v ollama)
elif [ "$(uname -s)" = Darwin ] && [ -x /Applications/Ollama.app/Contents/Resources/ollama ]; then
    ollama_bin=/Applications/Ollama.app/Contents/Resources/ollama
else
    case $(uname -s) in
        Darwin|Linux) ;;
        *) echo "Ollama's installer supports macOS and Linux only" >&2; exit 1 ;;
    esac
    command -v curl >/dev/null 2>&1 || { echo 'curl is required' >&2; exit 1; }
    installer=$(mktemp)
    trap 'rm -f "$installer"' EXIT
    echo 'Installing Ollama to its standard location...'
    curl -fsSL --retry 3 -o "$installer" https://ollama.com/install.sh
    OLLAMA_NO_START=1 sh "$installer"
    rm -f "$installer"
    trap - EXIT

    if command -v ollama >/dev/null 2>&1; then
        ollama_bin=$(command -v ollama)
    elif [ -x /Applications/Ollama.app/Contents/Resources/ollama ]; then
        ollama_bin=/Applications/Ollama.app/Contents/Resources/ollama
    else
        echo 'Ollama installation completed but its executable was not found' >&2
        exit 1
    fi
fi

command -v curl >/dev/null 2>&1 || { echo 'curl is required' >&2; exit 1; }
if curl -fsS --max-time 2 "http://$host/api/version" >/dev/null 2>&1; then
    if [ ! -f "$state_dir/ollama.pid" ] || ! kill -0 "$(cat "$state_dir/ollama.pid")" 2>/dev/null; then
        if [ -n "$models_dir" ]; then
            echo "Another Ollama server is using $host; stop it so the goinfre model directory can take effect." >&2
            exit 1
        fi
    elif [ ! -f "$state_dir/ollama.models-dir" ] || [ "$(cat "$state_dir/ollama.models-dir")" != "$models_dir" ]; then
        echo 'Running Ollama uses a different model directory. Restart it to use the selected directory.' >&2
        exit 1
    fi
    echo "Ollama server is already running at $host"
else
    echo "Starting Ollama at $host with models in $display_dir..."
    nohup "$ollama_bin" serve > "$state_dir/ollama.log" 2>&1 < /dev/null &
    echo $! > "$state_dir/ollama.pid"
    attempt=0
    until curl -fsS --max-time 2 "http://$host/api/version" >/dev/null 2>&1; do
        attempt=$((attempt + 1))
        if [ "$attempt" -ge 30 ] || ! kill -0 "$(cat "$state_dir/ollama.pid")" 2>/dev/null; then
            echo "Ollama did not start; see $state_dir/ollama.log" >&2
            exit 1
        fi
        sleep 1
    done
    printf '%s\n' "$models_dir" > "$state_dir/ollama.models-dir"
fi

if "$ollama_bin" show "$model" >/dev/null 2>&1; then
    echo "Model $model is already available"
else
    echo "Downloading model $model to $display_dir..."
    "$ollama_bin" pull "$model"
fi
echo "Ollama ready: http://$host (model: $model)"
