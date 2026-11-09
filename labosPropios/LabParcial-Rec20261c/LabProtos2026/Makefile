# Atajos para el LabProtos2026. Uso: make <target>
# (no agrega nada nuevo, solo abrevia los comandos de docker compose)

.DEFAULT_GOAL := help
DC := docker compose

.PHONY: help up ws check logs ps down restart

help:   ## muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	 | awk 'BEGIN{FS=":.*?## "}{printf "  make %-10s %s\n",$$1,$$2}'

up:     ## construye y levanta todo el lab (espera a que este listo)
	@./levantar.sh

ws:     ## entra a la terminal del workstation (donde practicas)
	@$(DC) exec workstation bash

check:  ## corre la verificacion de los 7 ejercicios
	@./verificar.sh

logs:   ## logs de un servicio: make logs s=mail  (dns|mail|metadata|ej3|proxy|pampero|parcial|workstation)
	@$(DC) logs -f $(s)

ps:     ## estado de los contenedores
	@$(DC) ps

restart: ## reinicia un servicio: make restart s=proxy
	@$(DC) restart $(s)

down:   ## apaga y limpia el lab
	@./bajar.sh
