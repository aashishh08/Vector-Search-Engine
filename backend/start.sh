#!/bin/bash

echo "Starting Website Content Search API Backend..."
echo "Server will be available at http://localhost:8000"
echo "API documentation at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn main:app --reload --host 0.0.0.0 --port 8000 