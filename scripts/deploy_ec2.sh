#!/usr/bin/env bash
set -Eeuo pipefail

image_uri="$1"
registry="$2"
aws_region="$3"
app_directory="$4"
container_name="$5"
health_url="$6"

cd "$app_directory"

previous_image="$(
    docker inspect --format '{{.Image}}' "$container_name" 2>/dev/null || true
)"

if [ -z "$previous_image" ]; then
    echo "Unable to identify the currently deployed image"
    exit 1
fi

aws ecr get-login-password --region "$aws_region" |
    docker login \
        --username AWS \
        --password-stdin \
        "$registry"

docker pull "$image_uri"

echo "Deploying $image_uri"

FRONTEND_IMAGE="$image_uri" \
    docker compose up -d --no-build --force-recreate frontend

healthy=false

for attempt in $(seq 1 18); do
    if curl -fsS --max-time 5 "$health_url" | grep -qx "ok"; then
        healthy=true
        break
    fi

    echo "Waiting for health check: attempt $attempt/18"
    sleep 10
done

if [ "$healthy" = "true" ]; then
    echo "Deployment health check passed"
    docker compose ps
    exit 0
fi

echo "Deployment failed; restoring previous image"
docker compose logs --tail=100 frontend || true

rollback_image="portfolio-frontend:rollback"
docker tag "$previous_image" "$rollback_image"

FRONTEND_IMAGE="$rollback_image" \
    docker compose up -d --no-build --force-recreate frontend

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
    docker compose logs --tail=100 frontend || true
fi

# The GitHub deployment must remain failed even when rollback succeeds.
exit 1