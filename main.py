from typing import Any, Dict, List, Optional
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import json
from streamfeed import preview_feed

from metar import get_metar, metar_string

app = FastAPI()

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from metar import get_metar  # <-- add this

app = FastAPI()


@app.get("/ekhk", response_class=HTMLResponse)
def ekhg_page() -> HTMLResponse:
    data = get_metar(["06156"])
    if not data:
        return HTMLResponse("<h3>Service temporarily unavailable</h3>", status_code=503)

    metar = metar_string(data[0])

    return HTMLResponse(
        f"""
     <html>
        <head>
            <meta charset="utf-8">
            <meta http-equiv="refresh" content="60">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
              * {{
                box-sizing: border-box;
              }}
              html, body {{
                margin: 0;
                padding: 0;
                height: 100%;
                width: 100%;
                background-color: #0d0f11;
                color: #00f5b3;
                font-family: monospace;
                font-size: 1.4rem;
                letter-spacing: 0.04em;
                display: flex;
                align-items: center;
                justify-content: center;
              }}
              .container {{
                text-align: center;
                padding: 1rem;
                max-width: 90%;
                width: 50%;
                line-height: 1.4;
              }}
              span {{
                display: inline-block;
                white-space: pre-wrap;
                word-break: break-word;
              }}
            </style>
        </head>
        <body>
            <div class="container">
                <span>{metar}</span>
            </div>
        </body>
        </html>
    """
    )


@app.get("/json")
def ekhk():
    data = get_metar(["06156"])
    metar = json.dumps(data, ensure_ascii=False, indent=2)
    print(metar)

    return data


# Health check endpoint.
@app.get("/health")
def health_check():
    return {"status": "ok"}
