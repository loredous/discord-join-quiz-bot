FROM python:3-slim

ENV BOT_TOKEN=""
ENV QUIZ_CONFIG="/quiz_config.yaml"

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

COPY code /code/

RUN groupadd -g 10001 bot && \
   useradd -u 10000 -g bot bot \
   && chown -R bot:bot /code

USER bot

ENTRYPOINT [ "/usr/local/bin/python", "/code/bot.py" ]