# Stage 1: Build Frontend
FROM node:20-alpine as frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Build Backend & Serve
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY pyproject.toml .
RUN pip install uv && uv pip install --system -e .

# Copy backend code
COPY backend/ ./backend/
COPY main.py .

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create data directory
RUN mkdir -p /app/data

# Environment variables
ENV PORT=8000
ENV HOST=0.0.0.0

EXPOSE 8000

# Start command
CMD ["python", "-m", "backend.main"]
