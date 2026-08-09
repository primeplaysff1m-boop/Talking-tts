FROM python:3.11-slim

WORKDIR /app
COPY index.html .

# Railway provides the port to listen on via the $PORT env var
CMD sh -c "python3 -m http.server ${PORT:-8080}"
