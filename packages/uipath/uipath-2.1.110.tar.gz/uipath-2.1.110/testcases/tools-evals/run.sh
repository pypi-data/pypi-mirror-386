#!/bin/bash

echo "Syncing dependencies..."
uv sync

echo "Authenticating with UiPath..."
uv run uipath auth --client-id="$CLIENT_ID" --client-secret="$CLIENT_SECRET" --base-url="$BASE_URL"

echo "Run init..."
uv run uipath init

echo "Running evaluations..."
uv run uipath eval ../../samples/weather_tools/main.py ../../samples/weather_tools/evals/eval-sets/default.json --no-report

#echo "Running assertions..."
#uv run python assert.py
