FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY app/ ./app/

# Create placeholder .env file (environment variables will be set at runtime)
RUN echo "# Environment variables will be set at runtime" > .env

CMD ["python", "src/bot.py"]
