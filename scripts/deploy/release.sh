#!/usr/bin/env bash
# HRMS-only release. No infrastructure installation, SQL, credential rotation or retirement.
set -euo pipefail
app_dir="$1"
image_dir="$2"
tag="$3"
load_images="$4"
start_apps="$5"
validate_apps="$6"
mode="$7"
[ "$mode" = organization ] || { echo 'This release requires organization mode; rollback uses previous reviewed artifacts.' >&2; exit 1; }
cd "$app_dir"
compose=(docker compose --project-name apps --file "$app_dir/compose.json")
"${compose[@]}" config --quiet
if [ "$start_apps" = 1 ]; then
    retired_worker_running() {
        echo 'Retired delivery worker is running. Complete reviewed company delivery cutover before organization rollout; no worker is stopped automatically.' >&2
        exit 1
    }
    worker_inventory_failed() {
        echo 'Retired-worker safety inventory failed; rollout is blocked. No container is stopped automatically.' >&2
        exit 1
    }
    # Keep the old service-label and exact global-name guards, including a
    # global container created outside this Compose project. A failed query
    # cannot establish absence. Never print inspected commands or arguments.
    if ! workers="$(docker ps --filter label=com.docker.compose.project=apps --filter label=com.docker.compose.service=kabipay-outbox-worker --format '{{.ID}}' 2>/dev/null)"; then worker_inventory_failed; fi
    [ -z "$workers" ] || retired_worker_running
    if ! workers="$(docker ps --filter 'name=^/kabipay-outbox-worker$' --format '{{.ID}}' 2>/dev/null)"; then worker_inventory_failed; fi
    [ -z "$workers" ] || retired_worker_running
    # Old bound releases used outbox-<slug> service labels. Compose up leaves
    # these orphans running, so service names alone cannot fence retirement.
    if ! containers="$(docker ps --filter label=com.docker.compose.project=apps --format '{{.ID}}' 2>/dev/null)"; then worker_inventory_failed; fi
    retired_worker_pattern='(^|[^[:alnum:]_.-])kabipay-outbox-worker([^[:alnum:]_.-]|$)'
    for container in $containers; do
        [[ "$container" =~ ^[a-f0-9]{12,64}$ ]] || worker_inventory_failed
        if ! effective_command="$(docker inspect --format '{{range .Config.Entrypoint}}{{println .}}{{end}}{{range .Config.Cmd}}{{println .}}{{end}}' "$container" 2>/dev/null)"; then worker_inventory_failed; fi
        # Includes absolute executables and commands launched through sh -c.
        [[ ! "$effective_command" =~ $retired_worker_pattern ]] || retired_worker_running
        if ! old_service="$(docker inspect --format '{{index .Config.Labels "com.docker.compose.service"}}' "$container" 2>/dev/null)"; then worker_inventory_failed; fi
        # Compose up retains orphans. Do not run old company job writers beside
        # the shared processes, and never use --remove-orphans on this shared VPS.
        if [[ "$old_service" =~ ^(auth|gateway|ui|ingress|source|maintenance|employee|leave|attendance|payroll|tax|benefits|expense|recruitment|performance|lms|succession|compensation|assets|grievance|workflow|notification|analytics|survey)- ]]; then
            echo 'Previous company application containers are still running. Complete the reviewed writer freeze and stop the old company application fleet before shared rollout; no container is stopped automatically.' >&2
            exit 1
        fi
    done
fi
if [ "$start_apps" = 1 ]; then
    bash "$app_dir/scripts/check-inventory.sh" "$app_dir" "$tag"
fi
if [ "$load_images" = 1 ]; then
    # Validate the complete archive set before loading the first image.
    test -f "$image_dir/SHA256SUMS"
    [ "$(wc -l < "$image_dir/SHA256SUMS")" -eq 4 ] || { echo 'Exactly four image checksums required.' >&2; exit 1; }
    for image in svc gateway ui organization-events; do
        name="kabipay-$image-$tag.tar"
        expected="$(awk -v name="$name" '{sub(/\r$/, "")} $2 == name && NF == 2 {print $1}' "$image_dir/SHA256SUMS")"
        [[ "$expected" =~ ^[a-fA-F0-9]{64}$ ]] || { echo 'Missing or duplicate image checksum.' >&2; exit 1; }
        actual="$(sha256sum -- "$image_dir/$name")"
        [ "${actual%% *}" = "${expected,,}" ] || { echo 'Image checksum mismatch.' >&2; exit 1; }
    done
    python3 "$app_dir/scripts/image-archive.py" "$image_dir" "$tag" --load
fi
if [ "$start_apps" = 1 ]; then
    docker run --rm --network none --read-only --memory 128m --user 0 \
        --mount "type=bind,source=$app_dir,target=$app_dir,readonly" \
        --entrypoint node "kabipay-organization-events:$tag" \
        "$app_dir/scripts/check-shared-config.mjs" "$app_dir"
    while IFS= read -r files_path; do
        [ -n "$files_path" ] || continue
        test -d "$files_path"
        [ "$(realpath -e -- "$files_path")" = "$files_path" ] || { echo 'Company private-file path aliases/symlinks require an explicit canonical mapping.' >&2; exit 1; }
    done < "$app_dir/private-files.txt"
    # Finance safety preflight is mandatory even when post-release validation is skipped.
    while IFS='|' read -r config_file target_services; do
        [ -n "$config_file" ] || continue
        bash "$app_dir/scripts/reconcile-env.sh" "$app_dir" "$tag" --check-finance-file "$config_file"
    done < "$app_dir/finance-checks.txt"
    mapfile -t services < <("${compose[@]}" config --services)
    # Image loading and preflights can outlast the receipt or change artifacts.
    bash "$app_dir/scripts/check-inventory.sh" "$app_dir" "$tag"
    "${compose[@]}" up --detach --no-build "${services[@]}"
fi
if [ "$validate_apps" = 1 ]; then
    deadline=$((SECONDS+120))
    while :; do
        missing=0
        while read -r service; do
            id="$("${compose[@]}" ps --all --quiet "$service")"
            [ -n "$id" ] || { missing=1; continue; }
            state="$(docker inspect --format '{{.State.Status}}' "$id")"
            [ "$state" = running ] || missing=1
        done < <("${compose[@]}" config --services)
        [ "$missing" = 0 ] && break
        [ "$SECONDS" -lt "$deadline" ] || { echo 'HRMS services are not all running; inspect restricted logs.' >&2; exit 1; }
        sleep 2
    done
    while IFS='|' read -r config_file target_services; do
        [ -n "$config_file" ] || continue
        read -r -a targets <<< "$target_services"
        for service in "${targets[@]}"; do
            id="$("${compose[@]}" ps --all --quiet "$service")"
            bash "$app_dir/scripts/reconcile-env.sh" "$app_dir" "$tag" --check-finance-container "$config_file" "$id"
        done
    done < "$app_dir/finance-checks.txt"
    echo 'HRMS containers running. Complete public health, identity, source, CDC and restore acceptance from the runbook.'
fi
