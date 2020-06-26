FROM python:3.7-alpine
RUN apk add build-base
RUN python -m pip install discord.py
COPY . /app
WORKDIR /app
VOLUME /data
CMD python3 toster.py
