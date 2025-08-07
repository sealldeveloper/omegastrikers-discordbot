FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml ./

RUN pip install uv && \
    uv sync

COPY . .

CMD ["uv", "run", "python", "main.py"]