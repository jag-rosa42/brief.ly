#!/bin/sh
set -eu

state_dir="$HOME/.ollama/ft-transcendance"
pid_file="$state_dir/ollama.pid"

if [ ! -f "$pid_file" ]; then
    echo 'No Ollama server started by make is recorded'
    exit 0
fi

pid=$(cat "$pid_file")
case $pid in
    ''|*[!0-9]*) echo "Invalid Ollama PID in $pid_file" >&2; exit 1 ;;
esac
if [ "$pid" -eq 0 ]; then
    echo "Invalid Ollama PID in $pid_file" >&2
    exit 1
fi

if ! kill -0 "$pid" 2>/dev/null; then
    rm -f "$pid_file" "$state_dir/ollama.models-dir"
    echo 'Ollama server was already stopped'
    exit 0
fi

command_line=$(ps -ww -p "$pid" -o command=)
case $command_line in
    *ollama*' serve'*) ;;
    *) echo "PID $pid is not an ollama serve process; leaving it running" >&2; exit 1 ;;
esac

kill "$pid"
attempt=0
while kill -0 "$pid" 2>/dev/null; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 10 ]; then
        echo 'Ollama did not stop within 10 seconds' >&2
        exit 1
    fi
    sleep 1
done

rm -f "$pid_file" "$state_dir/ollama.models-dir"
echo 'Ollama server stopped'
