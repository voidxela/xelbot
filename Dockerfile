FROM ghcr.io/astral-sh/uv:debian-slim AS build
WORKDIR /app
COPY . .
RUN uv build

FROM python:3-slim
COPY --from=build /app/dist/*.whl /tmp/
RUN pip install /tmp/xelbot*.whl && rm /tmp/xelbot*.whl
WORKDIR /app
COPY backup.sh backup_database.py ./
ENTRYPOINT ["xelbot"]
CMD ["run"]
