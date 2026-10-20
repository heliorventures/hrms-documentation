#!/usr/bin/env bash
# Operator evidence for a single shared fleet; this is not an authorization token.
set -euo pipefail
cd -- "$1"
app_dir="$(realpath -e .)"
tag="$2"
fail() { echo 'Company cutover inventory is missing, stale or does not match these release artifacts. Re-run the read-only database operator preflight.' >&2; exit 1; }
report=cutover-inventory.txt
test -f "$report" && test ! -L "$report" && test -f release.sha256 && test ! -L release.sha256 || fail
[ "$(wc -c < "$report")" -le 16384 ] || fail
[ "$(wc -c < release.sha256)" -le 1048576 ] || fail
declare -A receipt=()
while IFS='=' read -r key value || [ -n "$key" ]; do
    case "$key" in version|scope|tag|release_sha256|checked_at|expires_at|tenant_ids) ;; *) fail;; esac
    [[ ! -v "receipt[$key]" ]] || fail
    receipt[$key]="$value"
done < "$report"
[ "${#receipt[@]}" = 7 ] || fail
[ "${receipt[version]}" = 1 ] && [ "${receipt[scope]}" = single-shared-fleet ] && [ "${receipt[tag]}" = "$tag" ] || fail
[[ "${receipt[release_sha256]}" =~ ^[a-f0-9]{64}$ ]] || fail
[[ "${receipt[checked_at]}" =~ ^[1-9][0-9]{0,10}$ && "${receipt[expires_at]}" =~ ^[1-9][0-9]{0,10}$ ]] || fail
now="$(date -u +%s)"
checked="${receipt[checked_at]}"
expires="${receipt[expires_at]}"
# Thirty seconds of clock tolerance; never extend the fifteen-minute receipt.
(( checked <= now + 30 && expires > now && expires > checked && expires - checked <= 900 )) || fail
declare -A indexed=()
while IFS= read -r line || [ -n "$line" ]; do
    [[ "$line" =~ ^[a-f0-9]{64}\ \ [a-zA-Z0-9][a-zA-Z0-9_./-]*$ ]] || fail
    relative="${line:66}"
    case "/$relative/" in *'/../'*|*'/./'*|*'//'*) fail;; esac
    [[ ! -v "indexed[$relative]" && "$relative" != release.sha256 ]] || fail
    indexed[$relative]=1
    test -f "$relative" && test ! -L "$relative" || fail
    [ "$(realpath -e -- "$relative")" = "$app_dir/$relative" ] || fail
done < release.sha256
[[ -v 'indexed[release.json]' && -v 'indexed[compose.json]' && -v 'indexed[required-tenants.txt]' ]] || fail
sha256sum --check --strict --status release.sha256 2>/dev/null || fail
digest="$(sha256sum -- release.sha256)"
[ "${digest%% *}" = "${receipt[release_sha256]}" ] || fail
test "$(cat required-tenants.txt)" = "${receipt[tenant_ids]}" || fail
