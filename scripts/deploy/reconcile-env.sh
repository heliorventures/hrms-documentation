#!/usr/bin/env bash
# Reconcile defaults without replacing operator-owned credentials or configuration.
set -euo pipefail
export LC_ALL=C
umask 077

APP_DIR="$1"
TAG="$2"
MODE="${3:---reconcile}"
cd "$APP_DIR"

fail() { echo "ERROR: $*" >&2; exit 1; }
get_env_value() {
    awk -F= -v key="$2" '
        { sub(/\r$/, "") }
        $1 == key { value = substr($0, length(key) + 2) }
        END { print value }
    ' "$1"
}
has_env_key() { grep -q "^${2}=" "$1"; }
set_env_value() {
    # ENVIRON preserves literal backslashes, unlike awk -v value=... .
    local file="$1" key="$2" value="$3" tmp
    tmp="$(mktemp "${file}.value.XXXXXX")"
    ENV_KEY="$key" ENV_VALUE="$value" awk '
        BEGIN { key = ENVIRON["ENV_KEY"]; value = ENVIRON["ENV_VALUE"]; done = 0 }
        index($0, key "=") == 1 { if (!done) print key "=" value; done = 1; next }
        { print }
        END { if (!done) print key "=" value }
    ' "$file" > "$tmp"
    mv "$tmp" "$file"
}
remove_env_key() {
    local file="$1" tmp
    tmp="$(mktemp "${file}.remove.XXXXXX")"
    awk -F= -v key="$2" '$1 != key' "$file" > "$tmp"
    mv "$tmp" "$file"
}
literal_value() {
    local value
    value="$(get_env_value "$1" "$2")"
    [[ "$value" != [[:space:]]* ]] || fail "$2 must start immediately after '='; quote intentional leading spaces"
    # Finance values must be literals; never evaluate a dotenv file as shell code.
    if [[ "$value" == \"* ]]; then
        [[ "$value" =~ ^\"([^\"]*)\"[[:space:]]*(#.*)?$ ]] || fail "$2 must be a single-line literal"
        value="${BASH_REMATCH[1]}"
    elif [[ "$value" == \'* ]]; then
        [[ "$value" =~ ^\'([^\']*)\'[[:space:]]*(#.*)?$ ]] || fail "$2 must be a single-line literal"
        value="${BASH_REMATCH[1]}"
    else
        value="${value%%[[:space:]]#*}"
        value="${value%"${value##*[![:space:]]}"}"
    fi
    [[ "$value" != *'$'* && "$value" != *'\'* ]] || fail "$2 must use a literal value without interpolation or escapes"
    printf '%s' "$value"
}
validate_host() {
    local host="$1" key="$2" ip left right part count=0
    local -a parts
    if [[ "$host" == \[*\] ]]; then
        ip="${host:1:${#host}-2}"
        if [[ "$ip" == *::* ]]; then
            left="${ip%%::*}"; right="${ip#*::}"
            [[ "$right" != *::* && "$left" != :* && "$left" != *: && "$right" != :* && "$right" != *: ]] ||
                fail "$key contains an invalid IPv6 host"
            ip="${left}${left:+:}${right}"
        else
            [[ "$ip" != :* && "$ip" != *: ]] || fail "$key contains an invalid IPv6 host"
        fi
        IFS=: read -r -a parts <<< "$ip"
        for part in "${parts[@]}"; do
            [ -n "$part" ] || continue
            [[ "$part" =~ ^[[:xdigit:]]{1,4}$ ]] || fail "$key contains an invalid IPv6 host"
            count=$((count + 1))
        done
        if [[ "$host" == *::* ]]; then
            [ "$count" -lt 8 ] || fail "$key contains an invalid IPv6 host"
        else
            [ "$count" -eq 8 ] || fail "$key contains an invalid IPv6 host"
        fi
    elif [[ "$host" =~ ^[0-9.]+$ ]]; then
        [[ "$host" != .* && "$host" != *. ]] || fail "$key contains an invalid IPv4 host"
        IFS=. read -r -a parts <<< "$host"
        [ "${#parts[@]}" -eq 4 ] || fail "$key must use a complete IPv4 address"
        for part in "${parts[@]}"; do
            [[ "$part" =~ ^(0|[1-9][0-9]{0,2})$ ]] && ((10#$part <= 255)) || fail "$key contains an invalid IPv4 host"
        done
    else
        [ "${#host}" -le 253 ] || fail "$key contains an invalid DNS host"
        # Runtime URL parsing treats a numeric final label as an IPv4 address.
        part="${host%.}"; part="${part##*.}"
        [[ ! "$part" =~ ^[0-9]+$ && ! "$part" =~ ^0[xX][[:xdigit:]]+$ ]] ||
            fail "$key must use a canonical IPv4 address or DNS host"
        IFS=. read -r -a parts <<< "$host"
        for part in "${parts[@]}"; do
            [[ "$part" =~ ^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$ ]] || fail "$key contains an invalid DNS host"
        done
    fi
}
validate_finance() {
    local file="$1" key secret jwt url port host
    secret="$(literal_value "$file" KABIPAY_FINANCE_SERVICE_SECRET)"
    [ "${#secret}" -ge 32 ] || fail "KABIPAY_FINANCE_SERVICE_SECRET must contain at least 32 bytes"
    if has_env_key "$file" KABIPAY_JWT_SECRET; then
        jwt="$(literal_value "$file" KABIPAY_JWT_SECRET)"
        [ -n "$jwt" ] || fail 'KABIPAY_JWT_SECRET must not be empty'
        [ "$secret" != "$jwt" ] || fail "KABIPAY_FINANCE_SERVICE_SECRET must be independent of KABIPAY_JWT_SECRET"
    fi
    for key in KABIPAY_FINANCE_EMPLOYEE_URL KABIPAY_FINANCE_PAYROLL_URL; do
        url="$(literal_value "$file" "$key")"
        [[ "$url" =~ ^https://(\[[[:xdigit:]:]+\]|[a-zA-Z0-9.-]+)(:([0-9]{1,5}))?/?$ ]] ||
            fail "$key must be an HTTPS origin without credentials, path, query or fragment"
        host="${BASH_REMATCH[1]}"; port="${BASH_REMATCH[3]:-}"
        if [ -n "$port" ]; then
            ((10#$port >= 1 && 10#$port <= 65535)) || fail "$key contains an invalid port"
        fi
        validate_host "$host" "$key"
    done
}

validate_env() {
    local file="$1" key
    for key in POSTGRES_HOST POSTGRES_PORT POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD KABIPAY_JWT_SECRET; do
        [ -n "$(get_env_value "$file" "$key")" ] || fail "$key is missing in $APP_DIR/.env"
    done
    validate_finance "$file"
}
validate_finance_container() {
    local file="$1" container="$2" container_env key expected actual
    # Capture internally; never log full inspect output or secret values.
    container_env="$(docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "$container")" || fail "Cannot inspect $container environment"
    for key in KABIPAY_FINANCE_SERVICE_SECRET KABIPAY_FINANCE_EMPLOYEE_URL KABIPAY_FINANCE_PAYROLL_URL; do
        expected="$(literal_value "$file" "$key")"
        actual="$(printf '%s\n' "$container_env" | awk -F= -v key="$key" '$1 == key { print substr($0, length(key) + 2) }')"
        [ "$actual" = "$expected" ] || fail "$container $key does not match the configured environment"
    done
}
case "$MODE" in
    --check-finance-file|--check-finance-container)
        finance_file="${4:-}"
        [[ "$finance_file" = /* ]] && [ -f "$finance_file" ] || fail 'Explicit absolute Finance environment file is required'
        if [ "$MODE" = --check-finance-file ]; then
            [ "$#" -eq 4 ] || fail 'Finance file check requires exactly one filename'
        else
            [ "$#" -eq 5 ] && [[ "$5" =~ ^[a-f0-9]{12,64}$ ]] || fail 'Finance container check requires an explicit container ID'
        fi
        validate_finance "$finance_file"
        if [ "$MODE" = --check-finance-container ]; then validate_finance_container "$finance_file" "$5"; fi
        echo '==> Finance configuration validation passed'
        exit 0 ;;
    --check-only|--check-container)
        test -f .env || fail "$APP_DIR/.env does not exist"
        validate_env .env
        if [ "$MODE" = --check-container ]; then
            validate_finance_container .env kabipay-subgraphs
        fi
        echo '==> Finance configuration validation passed'
        exit 0 ;;
    --reconcile) ;;
    *) fail "Unknown environment preparation mode" ;;
esac

test -f .env.example || fail "$APP_DIR/.env.example does not exist"
next="$(mktemp .env.next.XXXXXX)"
trap 'rm -f "$next"' EXIT
if [ -f .env ]; then cp .env "$next"; fi

# Preserve an existing legacy signing key before introducing new template defaults.
if [ -z "$(get_env_value "$next" KABIPAY_JWT_SECRET)" ]; then
    for key in KABIPAY_CLIENT_JWT_SECRET KABIPAY_OPERATOR_JWT_SECRET; do
        legacy="$(get_env_value "$next" "$key")"
        if [ -n "$legacy" ]; then set_env_value "$next" KABIPAY_JWT_SECRET "$legacy"; break; fi
    done
fi
while IFS= read -r line || [ -n "$line" ]; do
    line="${line%$'\r'}"
    case "$line" in ''|\#*) continue ;; esac
    [[ "$line" == *=* ]] || continue
    key="${line%%=*}"
    [[ "$key" =~ ^[A-Za-z_][A-Za-z_0-9]*$ ]] || fail 'Invalid key in .env.example'
    # This key is created locally from randomness, never copied from a template.
    [ "$key" != KABIPAY_FINANCE_SERVICE_SECRET ] || continue
    has_env_key "$next" "$key" || set_env_value "$next" "$key" "${line#*=}"
done < .env.example

if [ -z "$(get_env_value "$next" KABIPAY_FINANCE_SERVICE_SECRET)" ]; then
    secret="$(od -An -N32 -tx1 /dev/urandom | tr -d ' \n')"
    [ "${#secret}" -eq 64 ] || fail 'Could not generate private Finance secret'
    set_env_value "$next" KABIPAY_FINANCE_SERVICE_SECRET "$secret"
fi
set_env_value "$next" KABIPAY_IMAGE_TAG "$TAG"
for key in KABIPAY_CLIENT_JWT_SECRET KABIPAY_OPERATOR_JWT_SECRET KABIPAY_CLIENT_JWT_EXPIRY_HOURS KABIPAY_OPERATOR_JWT_EXPIRY_HOURS KABIPAY_CLIENT_REFRESH_EXPIRY_DAYS DATABASE_URL POSTGRES_SSLMODE; do
    remove_env_key "$next" "$key"
done
validate_env "$next"
if [ -f .env ]; then
    backup="$(mktemp ".env.backup.$(date +%Y%m%d-%H%M%S).XXXXXX")"
    cp .env "$backup"
    chmod 600 "$backup"
fi
chmod 600 "$next"
mv "$next" .env
echo '==> Environment prepared: existing values preserved; missing defaults added; private Finance configured'
