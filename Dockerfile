FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source and pyproject.toml to install stride package
COPY stride/ stride/
COPY pyproject.toml ./

# Install stride package itself without reinstalling dependencies
RUN pip install --no-cache-dir --no-deps .

# Persistent data volume — SQLite file lives here
ENV DATA_DIR=/data
RUN mkdir -p /data

# Expose the default Dash port
EXPOSE 8050

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8050/health')" || exit 1

CMD ["python", "-m", "stride", "run"]
