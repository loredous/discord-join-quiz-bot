FROM python:3-slim

ENV BOT_TOKEN=""
ENV RULES_CHANNEL_ID=""
ENV MEMBER_ROLE_ID=""

RUN pip install py-cord

COPY code /code/

ENTRYPOINT [ "/usr/local/bin/python", "/code/bot.py" ]