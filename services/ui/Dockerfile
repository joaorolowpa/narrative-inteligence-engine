FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app

COPY pyproject.toml README.md ./
COPY libs ./libs
COPY services ./services
COPY tests ./tests

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e .[dev]

CMD ["streamlit", "run", "services/ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
