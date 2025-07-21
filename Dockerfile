FROM alpine:latest

LABEL maintainer="mbround18"

ARG CARGO_MAKE_VERSION
ARG ARTIFACT_NAME="cargo-make-v${CARGO_MAKE_VERSION}-x86_64-unknown-linux-musl"

RUN apk add --no-cache wget unzip cargo \
    && wget -O /tmp/cargo-make.zip \
       "https://github.com/sagiegurari/cargo-make/releases/download/${CARGO_MAKE_VERSION}/${ARTIFACT_NAME}.zip" \
    && unzip /tmp/cargo-make.zip -d /tmp/ \
    && mv "/tmp/${ARTIFACT_NAME}/cargo-make" /usr/local/bin/ \
    && chmod +x /usr/local/bin/cargo-make \
    && rm -rf /tmp/*

