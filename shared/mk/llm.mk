# Host-local Ollama commands. The scripts also work without Make.
LLM_MODEL ?= gemma2:2b
OLLAMA_HOST ?= 127.0.0.1:11434

.PHONY: ollama ollama-down
ollama:
	@LLM_MODEL="$(LLM_MODEL)" OLLAMA_HOST="$(OLLAMA_HOST)" sh shared/script/start_ollama.sh

ollama-down:
	@sh shared/script/stop_ollama.sh
