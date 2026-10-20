FROM alpine:3.20

RUN apk add --no-cache \
    bash \
    coreutils \
    findutils \
    gzip \
    postgresql-client \
    rclone \
    tzdata \
    util-linux

COPY backup-entrypoint.sh /usr/local/bin/backup-entrypoint.sh
COPY backup-now.sh /usr/local/bin/backup-now.sh

RUN chmod +x /usr/local/bin/backup-entrypoint.sh /usr/local/bin/backup-now.sh

ENTRYPOINT ["/usr/local/bin/backup-entrypoint.sh"]
