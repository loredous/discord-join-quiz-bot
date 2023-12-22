FROM python:3.11-slim

ENV BOT_TOKEN=""
ENV QUIZ_CONFIG="/conf/quiz.yaml"

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

COPY code /code/

RUN groupadd -g 10001 bot && \
   useradd -u 10000 -g bot bot \
   && mkdir /conf \
   && chown -R bot:bot /conf \
   && chown -R bot:bot /code

USER bot

ENTRYPOINT [ "/usr/local/bin/python", "/code/bot.py" ]