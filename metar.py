#!/usr/bin/env python3
"""
Return structured “pseudo‑METAR” data for one or more DMI stations.

$ python metar_structured.py 06170 06156 | jq .
"""

from __future__ import annotations

import json
import math
import sys
import time
from datetime import datetime, timezone
from dataclasses import asdict, dataclass
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv
import os

# --------------------------------------------------------------------------- #
#                              CONFIGURATION                                  #
# --------------------------------------------------------------------------- #
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_URL = "https://dmigw.govcloud.dk/v2/metObs/collections/observation/items"

STATIONS = {  # DMI id ➜ ICAO
    "06170": "EKRK",  # Roskilde
    "06156": "EKHK",
}

PARAMS = {
    "temp_dew": "temp_dew_c",
    "temp_dry": "temp_dry_c",
    "visib_mean_last10min": "visibility_m",
    "pressure_at_sea": "qnh_hpa",
    "wind_dir": "wind_dir_deg",
    "wind_speed": "wind_speed_ms",
    "wind_max": "wind_gust_ms",
    "cloud_cover": "cloud_cover_pct",
    "cloud_height": "cloud_height_m",
}


# --------------------------------------------------------------------------- #
#                               API HELPERS                                   #
# --------------------------------------------------------------------------- #
def fetch_station(station_id: str, period: str = "latest-hour") -> Dict[str, Any]:
    url = f"{API_URL}?stationId={station_id}&period={period}&api-key={API_KEY}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()


def latest_values(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return the newest value for every parameter in PARAMS
    (falling back to -1 if missing).
    """
    result: Dict[str, Any] = {alias: -1 for alias in PARAMS.values()}
    for feat in payload["features"]:
        pid = feat["properties"]["parameterId"]
        alias = PARAMS.get(pid)
        if alias and result[alias] == -1:
            result[alias] = feat["properties"]["value"]
            # early exit: all collected
            if all(v != -1 for v in result.values()):
                break
    return result


# --------------------------------------------------------------------------- #
#                        DOMAIN‑SPECIFIC CALCULATIONS                         #
# --------------------------------------------------------------------------- #
def kt(ms: float) -> float:
    """Metre/sec ➜ knots."""
    return ms * 1.94384


def zfill_int(n: float | int, width: int) -> str:
    return str(int(round(n))).zfill(width)


def cloud_code(cover: float) -> str:
    if cover <= 0:
        return "NCD"
    if cover <= 10:
        return "SKC"
    if cover <= 25:
        return "FEW"
    if cover <= 50:
        return "SCT"
    if cover <= 90:
        return "BKN"
    return "OVC"


def runway_and_components(wdir: float, wspd_ms: float) -> Dict[str, Any]:
    """Return active runway, head‑/crosswind in kt, and direction of crosswind."""
    if 10 < wdir < 190:
        rwy, offset = 10, wdir - 100
    else:
        rwy = 28
        offset = wdir - 280 if wdir >= 190 else wdir + 80

    wspd = kt(wspd_ms)
    av_rad = math.radians(offset)
    hw, xw = abs(round(math.cos(av_rad) * wspd)), abs(round(math.sin(av_rad) * wspd))
    return dict(
        runway=str(rwy),
        headwind_kt=hw,
        crosswind_kt=xw,
        crosswind_from="left" if offset < 0 else "right",
    )


def build_metar_dict(station_id: str, raw: Dict[str, Any]) -> Dict[str, Any]:
    """Transform API payload ➜ one structured dict."""
    vals = latest_values(raw)
    name = STATIONS.get(station_id, station_id)
    obs_time_iso = raw["features"][0]["properties"]["observed"]
    obs_dt = datetime.fromisoformat(obs_time_iso.replace("Z", "+00:00"))

    metar_bits: Dict[str, Any] = {
        "station": name,
        "observed": obs_dt.isoformat(timespec="seconds"),
        **vals,
    }

    # enrich with extra derived values -------------------------------------- #
    metar_bits["wind_speed_kt"] = round(kt(vals["wind_speed_ms"]))
    metar_bits["wind_gust_kt"] = round(kt(vals["wind_gust_ms"]))
    metar_bits["cloud_code"] = cloud_code(vals["cloud_cover_pct"])
    if vals["cloud_height_m"] > 15:
        metar_bits["cloud_height_ft"] = int(round(vals["cloud_height_m"] * 3.28084))
    else:
        metar_bits["cloud_height_ft"] = None

    metar_bits.update(
        runway_and_components(
            vals["wind_dir_deg"],
            vals["wind_speed_ms"],
        )
    )

    return metar_bits


# --------------------------------------------------------------------------- #
#                                   MAIN                                      #
# --------------------------------------------------------------------------- #
def get_metar(station_ids: List[str] | None = None) -> List[Dict[str, Any]]:
    if not station_ids:
        station_ids = list(STATIONS)

    out: List[Dict[str, Any]] = []
    for sid in station_ids:
        try:
            raw = fetch_station(sid)
            out.append(build_metar_dict(sid, raw))
            time.sleep(0.15)  # polite to API
        except requests.HTTPError as e:
            print(
                f"[{sid}] HTTP error {e.response.status_code}: {e.response.reason}",
                file=sys.stderr,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[{sid}] Unable to decode obs: {exc}", file=sys.stderr)
    return out


def metar_string(d: Dict[str, Any]) -> str:
    """
    Convert the dict returned by build_metar_dict() into a single
    aviation‑style METAR line.

    Example output:
      EKHG METAR 161250Z 14009KT BKN009 9999 06/04 Q1008 R10 HW06 XW←05
    """
    ts = datetime.fromisoformat(d["observed"]).strftime("%d%H%MZ")

    wdir = int(round(d["wind_dir_deg"] / 10) * 10)
    wspd = str(d["wind_speed_kt"]).zfill(2)

    gust = ""
    if d["wind_gust_kt"] - d["wind_speed_kt"] > 10:
        gust = f"G{str(d['wind_gust_kt']).zfill(2)}"

    clouds = d["cloud_code"]
    if clouds != "SKC" and d["cloud_height_ft"]:
        clouds += str(d["cloud_height_ft"] // 100).zfill(3)

    vis = (
        "9999"
        if d["visibility_m"] > 9999
        else (
            "0000"
            if d["visibility_m"] < 100
            else f"{str(int(d['visibility_m'] // 100)).zfill(2)}00"
        )
    )

    temp_dew = f"{round(d['temp_dry_c'])}/{round(d['temp_dew_c'])}"

    qnh = f"Q{round(d['qnh_hpa'])}"

    rwy = (
        f"R{d['runway']} HW{str(d['headwind_kt']).zfill(2)} "
        f"XW{'←' if d['crosswind_from']=='right' else '→'}"
        f"{str(d['crosswind_kt']).zfill(2)}"
    )
    print(gust)
    return (
        f"{d['station']} METAR {ts} \n"
        f"{str(wdir).zfill(3)}{wspd}{'G' if gust else ''}{gust}KT \n"
        f"{vis} {clouds} {qnh} {temp_dew} \n {rwy}\n"
    )


if __name__ == "__main__":
    data = get_metar(sys.argv[1:])
    print(json.dumps(data, ensure_ascii=False, indent=2))

# ----------------------------------------------------------------------------
# If you prefer a dataclass instead of a dict, uncomment ↓ and
# return MetarData(**metar_bits) in build_metar_dict()
#
# @dataclass
# class MetarData:
#     station: str
#     observed: str
#     temp_dew_c: float
#     temp_dry_c: float
#     visibility_m: float
#     qnh_hpa: float
#     wind_dir_deg: float
#     wind_speed_ms: float
#     wind_gust_ms: float
#     cloud_cover_pct: float
#     cloud_height_m: float
#     wind_speed_kt: int
#     wind_gust_kt: int
#     cloud_code: str
#     cloud_height_ft: int | None
#     runway: str
#     headwind_kt: int
#     crosswind_kt: int
#     crosswind_from: str
#
#     def asdict(self) -> Dict[str, Any]:
#         return asdict(self)
# ----------------------------------------------------------------------------
