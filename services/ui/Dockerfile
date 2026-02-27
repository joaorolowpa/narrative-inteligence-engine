FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app

COPY pyproject.toml README.md ./
COPY libs ./libs
COPY services ./services
COPY tests ./tests

RUN pip install --no-cache-dir --upgrade pip \
    --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org \
    --default-timeout=120 --retries=20 \
    && pip install --no-cache-dir -e .[dev] \
    --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org \
    --default-timeout=120 --retries=20

CMD ["streamlit", "run", "services/ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
