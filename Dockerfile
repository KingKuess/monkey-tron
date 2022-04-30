FROM python:3
WORKDIR /usr/src/app
COPY . .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir discord.py discord_buttons_plugin requests pytz python-dotenv

CMD ["monkeytron.py"]
ENTRYPOINT ["python3"]