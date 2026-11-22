# Base image pinned by digest so every build starts from the exact same bytes; Dependabot
# keeps the tag and the digest up to date together.
# ---- build stage: install dependencies into an isolated prefix ----
FROM python:3.15-slim@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928 AS build
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- runtime stage: minimal image, non-root, no build tooling ----
FROM python:3.15-slim@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
# Apply OS security patches released after the base image was built.
# pip/setuptools are not needed at runtime and are a common source of CVEs.
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*; \
    pip uninstall -y pip setuptools wheel 2>/dev/null; \
    useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin app
COPY --from=build /install /usr/local
WORKDIR /srv
COPY app/ app/
USER 10001
EXPOSE 8080
ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--no-server-header"]
