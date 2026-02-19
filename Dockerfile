FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt /build/requirements.txt
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r /build/requirements.txt

FROM python:3.12-slim AS runtime
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1
WORKDIR /app

RUN adduser --disabled-password --gecos "" ontoti
COPY --from=builder /opt/venv /opt/venv
COPY app /app/app
COPY data /app/data
COPY skills /app/skills
COPY config.json /app/config.json

RUN chown -R ontoti:ontoti /app
USER ontoti

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
