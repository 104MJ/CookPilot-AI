FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN addgroup --system django \
    && adduser --system --ingroup django django \
    && mkdir -p staticfiles media \
    && chown -R django:django /app \
    && chmod +x entrypoint.sh

USER django

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
