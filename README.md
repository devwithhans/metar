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
   pip install fastapi uvicorn
   ```
4. Run the application:
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

The application uses a `.env` file for configuration (ignored by git).

## Development

The code is organized as follows:

- `main.py`: Main application file with FastAPI routes
- `metar.py`: Module for fetching and processing METAR data

To extend the application with additional stations, modify the station codes in the relevant endpoint handlers.
