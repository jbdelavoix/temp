FROM caddy/caddy:2.8.4-builder-alpine AS builder

RUN xcaddy build \
    --with github.com/aksdb/caddy-cgi/v2 \
    --with github.com/greenpau/caddy-security


FROM caddy/caddy:2.8.4-alpine

COPY --from=builder /usr/bin/caddy /usr/bin/caddy

RUN apk add python3 py3-pip
