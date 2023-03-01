FROM python:3-slim

ENV BOT_TOKEN=""

RUN pip install py-cord

COPY code /code/

ENTRYPOINT [ "/usr/local/bin/python", "/code/bot.py" ]