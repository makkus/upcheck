FROM debian:stable

RUN \
   apt update -y && \
   apt install -y wget git

COPY upcheck /usr/bin/upcheck

RUN \
   chmod +x /usr/bin/upcheck
