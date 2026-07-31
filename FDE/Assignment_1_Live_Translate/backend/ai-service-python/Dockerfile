FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV TRANSLATION_DB_PATH=/data/translations.db
EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "::", "--port", "8000"]
