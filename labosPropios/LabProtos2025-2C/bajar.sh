#!/usr/bin/env bash
cd "$(dirname "$0")"
export COMPOSE_BAKE=false
docker compose down --remove-orphans
