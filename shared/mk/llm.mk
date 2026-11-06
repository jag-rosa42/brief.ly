# Host-local Ollama commands. The scripts also work without Make.
OLLAMA_HOST ?= 127.0.0.1:11434

.PHONY: ollama ollama-down
ollama:
	@OLLAMA_HOST="$(OLLAMA_HOST)" sh shared/script/start_ollama.sh

ollama-down:
	@sh shared/script/stop_ollama.sh
