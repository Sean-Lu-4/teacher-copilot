FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TEACHER_COPILOT_HOST=0.0.0.0 \
    PORT=8765

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8765
CMD ["sh", "-c", "python -m teacher_copilot.review_app --host 0.0.0.0 --port ${PORT:-8765}"]
