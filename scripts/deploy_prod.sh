#!/usr/bin/env bash
set -Eeuo pipefail

# AXIOM Production Deployment Script (HTTPS via nginx reverse proxy)
# Deploys both frontend and API containers

frontend_image_uri="$1"
api_image_uri="$2"
registry="$3"
aws_region="$4"
app_directory="$5"
frontend_container_name="$6"
api_container_name="$7"
health_url="$8"

cd "$app_directory"

previous_frontend_image="$(
    docker inspect --format '{{.Image}}' "$frontend_container_name" 2>/dev/null || true
)"

previous_api_image="$(
    docker inspect --format '{{.Image}}' "$api_container_name" 2>/dev/null || true
)"

if [ -z "$previous_frontend_image" ] || [ -z "$previous_api_image" ]; then
    echo "Unable to identify the currently deployed images"
    exit 1
fi

aws ecr get-login-password --region "$aws_region" |
    docker login \
        --username AWS \
        --password-stdin \
        "$registry"

docker pull "$frontend_image_uri"
docker pull "$api_image_uri"

echo "Preparing persistent data for non-root runtime UID/GID 10001"
FRONTEND_IMAGE="$frontend_image_uri" \
    docker compose -f docker-compose.prod.yml run --rm --no-deps --user 0:0 --entrypoint sh frontend \
    -c 'chown -R 10001:10001 /data'

echo "Deploying frontend: $frontend_image_uri"
echo "Deploying API: $api_image_uri"

FRONTEND_IMAGE="$frontend_image_uri" \
API_IMAGE="$api_image_uri" \
    docker compose -f docker-compose.prod.yml up -d --no-build --force-recreate frontend api

healthy=false

for attempt in $(seq 1 36); do
    if curl -fsS --max-time 5 "$health_url" | grep -qx "ok"; then
        healthy=true
        break
    fi

    echo "Waiting for health check: attempt $attempt/36"
    sleep 10
done

if [ "$healthy" = "true" ]; then
    echo "Deployment health check passed"
    docker compose -f docker-compose.prod.yml ps
    exit 0
fi

echo "Deployment failed; restoring previous images"
docker compose -f docker-compose.prod.yml logs --tail=100 frontend || true
docker compose -f docker-compose.prod.yml logs --tail=100 api || true

rollback_frontend_image="portfolio-frontend:rollback"
rollback_api_image="portfolio-api:rollback"
docker tag "$previous_frontend_image" "$rollback_frontend_image"
docker tag "$previous_api_image" "$rollback_api_image"

FRONTEND_IMAGE="$rollback_frontend_image" \
API_IMAGE="$rollback_api_image" \
    docker compose -f docker-compose.prod.yml up -d --no-build --force-recreate frontend api

rollback_healthy=false

for attempt in $(seq 1 18); do
    if curl -fsS --max-time 5 "$health_url" | grep -qx "ok"; then
        rollback_healthy=true
        break
    fi

    echo "Waiting for rollback health check: attempt $attempt/18"
    sleep 10
done

if [ "$rollback_healthy" = "true" ]; then
    echo "Rollback succeeded"
else
    echo "Rollback also failed"
    docker compose -f docker-compose.prod.yml logs --tail=100 frontend || true
    docker compose -f docker-compose.prod.yml logs --tail=100 api || true
fi

# The GitHub deployment must remain failed even when rollback succeeds.
exit 1