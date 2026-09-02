FROM ghcr.io/home-assistant/aarch64-base-python:3.12

WORKDIR /app

RUN pip3 install --no-cache-dir telethon

COPY run.sh /app/run.sh
COPY parser.py /app/parser.py

RUN chmod +x /app/run.sh

CMD ["/app/run.sh"]
