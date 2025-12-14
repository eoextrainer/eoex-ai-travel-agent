FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend /app/backend
COPY frontend /app/frontend

ENV AMADEUS_CLIENT_ID=""
ENV AMADEUS_CLIENT_SECRET=""
ENV MYSQL_USER=eoex
ENV MYSQL_PASSWORD=eoex
ENV MYSQL_HOST=db
ENV MYSQL_DB=eoex_travel

EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
