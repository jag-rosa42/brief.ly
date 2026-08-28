#!/bin/bash

set -e

# ========================================
# Create .env files
# ========================================

echo
echo "========================================"
echo "Checking .env files"
echo "========================================"

SERVICES=(
  identity
  personalization
  content_management
  morning_briefing
  ai_processing
)

for service in "${SERVICES[@]}"; do
  env_file="srcs/services/$service/.env"
  example_file="srcs/services/$service/.env.example"

  echo
  echo "Service: $service"

  if [ -f "$env_file" ]; then
    echo "  ✓ .env already exists: $env_file"
  else
    echo "  ! .env not found: $env_file"
    echo "  → Creating .env from $example_file..."

    if [ ! -f "$example_file" ]; then
      echo "  ✗ ERROR: .env.example not found: $example_file"
      exit 1
    fi

    cp "$example_file" "$env_file"

    echo "  ✓ .env created: $env_file"
  fi
done

echo
echo "========================================"
echo "Verifying .env files"
echo "========================================"

all_env_present=true

for service in "${SERVICES[@]}"; do
  env_file="srcs/services/$service/.env"

  if [ -f "$env_file" ]; then
    echo "  ✓ $env_file"
  else
    echo "  ✗ $env_file"
    all_env_present=false
  fi
done

if [ "$all_env_present" = false ]; then
  echo
  echo "✗ ERROR: One or more .env files are missing."
  exit 1
fi

echo
echo "✓ All .env files are present."


# ========================================
# Create postgresql container
# ========================================
POSTGRES_CONTAINER="postgres-dev"
POSTGRES_IMAGE="pgvector/pgvector:pg18"

POSTGRES_USER="transcendence"
POSTGRES_PASSWORD="app_password"
POSTGRES_DB="identity_db"
POSTGRES_PORT="5432"

POSTGRES_DATABASES=(
  "identity_db"
  "identity_db_test"
  "personalization_db"
  "personalization_db_test"
  "content_management_db"
  "content_management_db_test"
  "morning_briefing_db"
  "morning_briefing_db_test"
  "ai_processing_db"
  "ai_processing_db_test"
)

# ========================================
# Create / start PostgreSQL
# ========================================

echo
echo "========================================"
echo "PostgreSQL"
echo "========================================"

# Create the container if it doesn't exist
if docker container inspect "$POSTGRES_CONTAINER" >/dev/null 2>&1; then
  echo "Container already exists."

  # Start it if it isn't running
  if [ "$(docker inspect -f '{{.State.Running}}' "$POSTGRES_CONTAINER")" = "true" ]; then
    echo "Container is already running."
  else
    echo "Starting container..."
    docker start "$POSTGRES_CONTAINER" >/dev/null
  fi
else
  echo "Creating container..."

  docker run \
    --name "$POSTGRES_CONTAINER" \
    -e POSTGRES_USER="$POSTGRES_USER" \
    -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
    -e POSTGRES_DB="$POSTGRES_DB" \
    -p "$POSTGRES_PORT:5432" \
    -d "$POSTGRES_IMAGE" >/dev/null
fi

# ========================================
# Wait for PostgreSQL
# ========================================

echo "Waiting for PostgreSQL..."

until docker exec "$POSTGRES_CONTAINER" \
  pg_isready \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" >/dev/null 2>&1
do
  sleep 1
done

echo "PostgreSQL is ready."

# ========================================
# Create databases
# ========================================

echo
echo "Creating databases..."

for db in "${POSTGRES_DATABASES[@]}"; do
  if docker exec "$POSTGRES_CONTAINER" \
    psql \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    -tAc "SELECT 1 FROM pg_database WHERE datname='$db'" \
    | grep -q 1
  then
    echo "Database '$db' already exists."
  else
    echo "Creating database '$db'..."

    docker exec "$POSTGRES_CONTAINER" \
      psql \
      -U "$POSTGRES_USER" \
      -d "$POSTGRES_DB" \
      -c "CREATE DATABASE \"$db\";" >/dev/null

    echo "Database '$db' created."
  fi
done

# ========================================
# Enable pgvector where needed
# ========================================

echo
echo "========================================"
echo "Enabling pgvector"
echo "========================================"

for db in \
  "ai_processing_db" \
  "ai_processing_db_test"
do
  echo "Enabling vector extension in '$db'..."

  docker exec "$POSTGRES_CONTAINER" \
    psql \
    -U "$POSTGRES_USER" \
    -d "$db" \
    -c "CREATE EXTENSION IF NOT EXISTS vector;" >/dev/null

  echo "pgvector enabled in '$db'."
done

# ========================================
# Summary
# ========================================

echo
echo "========================================"
echo "PostgreSQL is running"
echo "========================================"

docker ps \
  --filter "name=$POSTGRES_CONTAINER" \
  --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo
echo "Host: localhost"
echo "Port: $POSTGRES_PORT"
echo "User: $POSTGRES_USER"
echo "pgvector: available"
