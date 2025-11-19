#!/bin/bash
echo "Killing any existing Node processes..."
taskkill //F //IM node.exe 2>/dev/null || true
sleep 2

echo "Starting frontend dev server..."
npm run dev
