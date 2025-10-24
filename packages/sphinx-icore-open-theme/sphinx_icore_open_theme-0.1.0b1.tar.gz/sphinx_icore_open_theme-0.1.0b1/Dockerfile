# --- Python Stage ---
FROM python:3.14-slim

ENV NODE_VERSION=22.20.0

# Set the working directory in the container
WORKDIR /app

# Install Node.js
RUN apt-get update && apt-get install -y curl xz-utils \
    && curl -fsSL https://nodejs.org/dist/v$NODE_VERSION/node-v$NODE_VERSION-linux-x64.tar.xz \
       | tar -xJ -C /usr/local --strip-components=1 \
    && apt-get purge -y curl xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /uvx /bin/

# Install Node.js deps
COPY package.json package-lock.json ./
RUN npm ci

# Install Python deps
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Provide a fallback version for setuptools_scm, which fails when the
# .git directory is not available in the Docker build context.
ARG VERSION="0.0.1"
ENV SETUPTOOLS_SCM_PRETEND_VERSION_FOR_SPHINX_ICORE_OPEN=$VERSION

RUN uv pip install --system .[dev]

# Copy the rest of the application code
COPY . .

# Build the static assets
RUN npm run build

# Expose the port for the development server
EXPOSE 8000

CMD ["./entrypoint.sh"]
