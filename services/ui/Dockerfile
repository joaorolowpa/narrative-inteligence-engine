FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app
ARG PIP_TRUSTED_HOST_FLAGS=""
ARG PIP_NETWORK_FLAGS="--default-timeout=120 --retries=20"

COPY pyproject.toml README.md ./
COPY libs ./libs
COPY services ./services
COPY tests ./tests

RUN pip install --no-cache-dir --upgrade pip ${PIP_NETWORK_FLAGS} ${PIP_TRUSTED_HOST_FLAGS} \
    && pip install --no-cache-dir -e .[dev] ${PIP_NETWORK_FLAGS} ${PIP_TRUSTED_HOST_FLAGS}

CMD ["streamlit", "run", "services/ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
