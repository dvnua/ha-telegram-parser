FROM ghcr.io/home-assistant/base:latest

RUN apk add --no-cache \
    python3 \
    py3-pip

RUN pip3 install --no-cache-dir --break-system-packages \
    telethon

WORKDIR /app

COPY run.sh /app/run.sh
COPY parser.py /app/parser.py

RUN chmod +x /app/run.sh

CMD ["/app/run.sh"]
