# LabProtos2025-2C — atajos.   Uso: make <objetivo>
.DEFAULT_GOAL := help
export COMPOSE_BAKE := false
DC := docker compose

.PHONY: help up ws check corregir reset reset-todo logs ps restart down clean

help:        ## muestra esta ayuda
	@echo "LabProtos2025-2C — Parcial Práctico 2Q2025"
	@grep -E '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  make %-12s %s\n",$$1,$$2}'

up:          ## construye y levanta el lab (espera a que esté listo)
	@./levantar.sh

ws:          ## entra a tu VM del parcial (contenedor alumno)
	@$(DC) exec alumno bash

check:       ## verifica que la infraestructura del lab funcione
	@./verificar.sh

corregir:    ## autocorrige tus resoluciones (make corregir ej=1|2|3|4|4b)
	@./corregir.sh $(ej)

reset:       ## vuelve tu VM al estado inicial del parcial (borra lo que configuraste)
	@$(DC) up -d --force-recreate --no-deps alumno
	@echo "Tu VM volvió al estado inicial. Entrá con: make ws"

reset-todo:  ## recrea todos los contenedores del lab
	@$(DC) up -d --force-recreate
	@./levantar.sh

logs:        ## logs de un servicio: make logs s=gateway  (dns|web|parcial|gateway|alumno)
	@$(DC) logs --tail=80 $(s)

ps:          ## estado de los contenedores
	@$(DC) ps

restart:     ## reinicia un servicio: make restart s=dns
	@$(DC) restart $(s)

down:        ## apaga el lab
	@./bajar.sh

clean:       ## apaga el lab y borra sus imágenes
	@$(DC) down --remove-orphans --rmi local
