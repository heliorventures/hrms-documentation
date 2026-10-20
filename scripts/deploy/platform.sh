#!/usr/bin/env bash
# Explicit shared platform maintenance, independent of HRMS image rollout.
set -euo pipefail
platform_root="${1:-/opt/apps}"
hrms_root="${2:-/opt/apps/hrms}"
operation="${3:-validate}"
export PLATFORM_ROOT="$platform_root" HRMS_ROOT="$hrms_root"
export APP_NETWORK="${APP_NETWORK:-apps_app-network}"
compose=(docker compose --env-file "$platform_root/.env" --project-name apps --file "$platform_root/compose.platform.yaml")
test -f "$platform_root/.env"
test -d "$platform_root/data/postgres"
test -d "$platform_root/data/mongo"
test -f "$platform_root/Caddyfile"
test -f "$hrms_root/caddy/company-sites.caddy"
test -f "$hrms_root/caddy/legacy-routes.caddy"
docker network inspect "$APP_NETWORK" >/dev/null
"${compose[@]}" config --quiet
verify_mount() {
    local container="$1" target="$2" expected="$3" actual
    if docker container inspect "$container" >/dev/null 2>&1; then
        actual="$(docker inspect --format "{{range .Mounts}}{{if eq .Destination \"$target\"}}{{.Source}}{{end}}{{end}}" "$container")"
        [ "$actual" = "$expected" ] || { echo "Refusing storage change for $container; review exact existing mounts/project first." >&2; exit 1; }
    fi
}
verify_mount postgres /var/lib/postgresql/data "$platform_root/data/postgres"
verify_mount mongo /data/db "$platform_root/data/mongo"
for volume in apps_caddy_data apps_caddy_config; do docker volume inspect "$volume" >/dev/null; done
if docker container inspect caddy >/dev/null 2>&1; then
    actual_data="$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Name}}{{end}}{{end}}' caddy)"
    actual_config="$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/config"}}{{.Name}}{{end}}{{end}}' caddy)"
    [ "$actual_data" = apps_caddy_data ] && [ "$actual_config" = apps_caddy_config ] || { echo 'Refusing a Caddy state-volume identity change.' >&2; exit 1; }
fi
case "$operation" in
    validate) echo 'Platform configuration/storage identities checked; no containers changed.' ;;
    up)
        for network in hrms_organization hrms_metadata hrms_sources; do
            if ! docker network inspect "$network" >/dev/null 2>&1; then docker network create --internal "$network" >/dev/null; fi
            [ "$(docker network inspect --format '{{.Internal}}' "$network")" = true ] || { echo 'Private network is not internal' >&2; exit 1; }
        done
        # Validate complete root Caddy config/certificates before recreating shared services.
        "${compose[@]}" run --rm --no-deps caddy caddy validate --config /etc/caddy/Caddyfile
        "${compose[@]}" up --detach --no-build caddy postgres mongo
        ;;
    reload-caddy)
        docker exec caddy caddy validate --config /etc/caddy/Caddyfile
        docker exec caddy caddy reload --config /etc/caddy/Caddyfile
        ;;
    *) echo 'Use validate, up or reload-caddy' >&2; exit 1 ;;
esac
