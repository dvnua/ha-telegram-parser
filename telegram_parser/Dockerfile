FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir telethon

COPY run.sh /app/run.sh
COPY parser.py /app/parser.py

RUN chmod +x /app/run.sh

CMD ["/app/run.sh"]
