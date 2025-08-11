#!/bin/bash

# Cognitive Companion Agent Launcher
echo "🧠 Starting Cognitive Companion Agent..."
echo ""
echo "📱 Opening your browser to http://localhost:8501"
echo "⛔ Press Ctrl+C to stop the application"
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit not found. Please install it with:"
    echo "   pip install streamlit"
    exit 1
fi

# Run the Streamlit app
streamlit run app.py

echo ""
echo "✅ Application stopped."