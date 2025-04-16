# SPEL - METAR Data Service

A simple FastAPI application that provides METAR (Meteorological Terminal Air Report) data.

## Overview

This service fetches and displays METAR weather data for aviation purposes. It provides both human-readable HTML and machine-readable JSON endpoints.

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv pyenv
   source pyenv/bin/activate  # On Windows: pyenv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   - Create a `.env` file in the project root
   - Add your API key(s) to the file:
     ```
     METAR_API_KEY=your_api_key_here
     # Add any other required configuration variables
     ```
5. Run the application:
   ```
   uvicorn main:app --reload
   ```

## Available Endpoints

### `/ekhk`

Returns a styled HTML page displaying METAR data for EKHK (Hokksund, Norway).

**Method:** GET  
**Response:** HTML page with formatted METAR information that auto-refreshes every 60 seconds

### `/json`

Returns the raw METAR data in JSON format.

**Method:** GET  
**Response:** JSON object with METAR data

### `/health`

Simple health check endpoint to verify the service is running.

**Method:** GET  
**Response:** JSON `{"status": "ok"}`

## Environment Variables

The application uses a `.env` file for configuration (ignored by git for security). Here's how to set it up:

1. Create a `.env` file in the project root directory
2. Add the required API keys and configuration values:

```
# API Keys
METAR_API_KEY=your_api_key_here

# Other Configuration
# PROXY_URL=http://your-proxy-if-needed
# DEBUG=True
```

3. The application will automatically load these variables using the python-dotenv package.

## Development

The code is organized as follows:

- `main.py`: Main application file with FastAPI routes
- `metar.py`: Module for fetching and processing METAR data

To extend the application with additional stations, modify the station codes in the relevant endpoint handlers.
