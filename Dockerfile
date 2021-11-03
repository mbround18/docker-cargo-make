FROM alpine:latest

LABEL docker.cargo-make.maintainer="mbround18"

ARG CARGO_MAKE_VERSION
ARG ARTIFACT_NAME="cargo-make-v${CARGO_MAKE_VERSION}-x86_64-unknown-linux-musl"

RUN apk --update add openssl wget unzip cargo \
    && rm -rf /var/cache/apk/* \
    && mkdir -p /tmp/cargo-make \
    && wget -O /tmp/cargo-make/cargo-make.zip \
    https://github.com/sagiegurari/cargo-make/releases/download/${CARGO_MAKE_VERSION}/${ARTIFACT_NAME}.zip \
    && unzip /tmp/cargo-make/cargo-make.zip -d /tmp/cargo-make/ \
    && cp /tmp/cargo-make/${ARTIFACT_NAME}/cargo-make /usr/local/bin \
    && chmod +x /usr/local/bin/cargo-make



