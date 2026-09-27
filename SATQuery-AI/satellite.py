# satellite.py
# ============================================================
# SATQuery AI
# REAL SENTINEL-2 L2A SATELLITE DATA MODULE
#
# Source:
# Copernicus Data Space Ecosystem
# STAC API
#
# IMPORTANT:
# This file DOES NOT generate synthetic satellite images.
# It searches for real Sentinel-2 L2A scenes.
# ============================================================

import os
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

import requests


# ============================================================
# CONFIGURATION
# ============================================================

STAC_BASE_URL = "https://stac.dataspace.copernicus.eu/v1"

STAC_SEARCH_URL = (
    "https://stac.dataspace.copernicus.eu/v1/search"
)

SENTINEL_COLLECTION = "sentinel-2-l2a"

REQUEST_TIMEOUT = 60

# Local folder where downloaded preview images are stored
CACHE_DIR = (
    Path(__file__).resolve().parent
    / "satellite_cache"
)

CACHE_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# Local HTTP server
LOCAL_HOST = "127.0.0.1"
LOCAL_PORT = 8765

_server = None
_server_thread = None
_server_started = False


# ============================================================
# LOCAL HTTP SERVER
# ============================================================

class QuietHTTPRequestHandler(
    SimpleHTTPRequestHandler
):

    def log_message(
        self,
        format,
        *args
    ):
        pass


def _start_local_server():

    global _server
    global _server_thread
    global _server_started

    if _server_started:
        return

    try:

        # Do NOT permanently change the application's
        # working directory.
        old_directory = os.getcwd()

        os.chdir(
            str(CACHE_DIR)
        )

        _server = ThreadingHTTPServer(
            (
                LOCAL_HOST,
                LOCAL_PORT
            ),
            QuietHTTPRequestHandler
        )

        # Restore original working directory
        os.chdir(
            old_directory
        )

        def serve():

            old_dir = os.getcwd()

            try:

                os.chdir(
                    str(CACHE_DIR)
                )

                _server.serve_forever()

            finally:

                os.chdir(
                    old_dir
                )

        _server_thread = threading.Thread(
            target=serve,
            daemon=True
        )

        _server_thread.start()

        _server_started = True

        print(
            f"[SATQUERY] Local image server started:"
            f" http://{LOCAL_HOST}:{LOCAL_PORT}"
        )

    except OSError as e:

        # If another Streamlit rerun already started
        # the server, do not crash.
        if "Address already in use" in str(e):

            _server_started = True

            print(
                "[SATQUERY] Local image server "
                "already running."
            )

        else:

            raise RuntimeError(
                "Could not start local satellite "
                f"image server.\n\nError: {e}"
            )


# ============================================================
# DATE HELPERS
# ============================================================

def _parse_date(value):

    """
    Convert supported date inputs into datetime.
    """

    if isinstance(
        value,
        datetime
    ):

        return value.replace(
            tzinfo=None
        )

    # datetime.date
    if hasattr(
        value,
        "year"
    ) and hasattr(
        value,
        "month"
    ) and hasattr(
        value,
        "day"
    ):

        try:

            return datetime(
                value.year,
                value.month,
                value.day
            )

        except Exception:
            pass

    value = str(
        value
    ).strip()

    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y-%m-%d %H:%M:%S",
    ]

    for fmt in formats:

        try:

            return datetime.strptime(
                value,
                fmt
            )

        except ValueError:
            continue

    try:

        parsed = datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00"
            )
        )

        return parsed.replace(
            tzinfo=None
        )

    except Exception:

        raise ValueError(
            f"Invalid date format: {value}"
        )


def _iso_start(dt):

    return dt.strftime(
        "%Y-%m-%dT00:00:00Z"
    )


def _iso_end(dt):

    return dt.strftime(
        "%Y-%m-%dT23:59:59Z"
    )


# ============================================================
# GEO HELPERS
# ============================================================

def _make_bbox(
    latitude,
    longitude,
    size=0.05
):

    """
    Create a small bounding box around
    the requested coordinate.

    bbox order:
    [west, south, east, north]
    """

    latitude = float(
        latitude
    )

    longitude = float(
        longitude
    )

    return [

        longitude - size,

        latitude - size,

        longitude + size,

        latitude + size

    ]


# ============================================================
# SAFE CONVERSION
# ============================================================

def _safe_float(
    value,
    default=None
):

    try:

        return float(
            value
        )

    except (
        TypeError,
        ValueError
    ):

        return default


# ============================================================
# COPERNICUS STAC SEARCH
# ============================================================

def _search_stac(
    latitude,
    longitude,
    start_date,
    end_date,
    cloud_limit=30.0,
    limit=50
):

    """
    Search the Copernicus Data Space STAC API.

    Uses POST /search with JSON body.

    Returns:
        list of STAC features
    """

    bbox = _make_bbox(
        latitude,
        longitude,
        size=0.05
    )

    payload = {

        "collections": [
            SENTINEL_COLLECTION
        ],

        "datetime":
            f"{_iso_start(start_date)}/"
            f"{_iso_end(end_date)}",

        "bbox": bbox,

        "limit": int(
            limit
        ),

        "query": {

            "eo:cloud_cover": {

                "lte":
                    float(cloud_limit)

            }

        },

        "sortby": [

            {

                "field": "datetime",

                "direction": "desc"

            }

        ]
    }

    print()
    print("=" * 75)
    print("SATQUERY AI - COPERNICUS STAC SEARCH")
    print("=" * 75)

    print(
        "Endpoint:",
        STAC_SEARCH_URL
    )

    print(
        "Collection:",
        SENTINEL_COLLECTION
    )

    print(
        "Date:",
        payload["datetime"]
    )

    print(
        "BBox:",
        bbox
    )

    print(
        "Cloud limit:",
        cloud_limit
    )

    print("=" * 75)

    # --------------------------------------------------------
    # SEND REQUEST
    # --------------------------------------------------------

    try:

        response = requests.post(

            STAC_SEARCH_URL,

            json=payload,

            timeout=REQUEST_TIMEOUT,

            headers={

                "Accept":
                    "application/geo+json",

                "Content-Type":
                    "application/json",

                "User-Agent":
                    "SATQuery-AI/1.0"
            }

        )

    except requests.RequestException as e:

        raise RuntimeError(

            "Could not connect to the "
            "Copernicus STAC catalogue.\n\n"

            f"Error: {e}"

        )

    # --------------------------------------------------------
    # HTTP STATUS
    # --------------------------------------------------------

    print(
        "[SATQUERY] HTTP status:",
        response.status_code
    )

    # --------------------------------------------------------
    # NON-200 RESPONSE
    # --------------------------------------------------------

    if response.status_code != 200:

        content_type = (
            response.headers.get(
                "Content-Type",
                ""
            )
        )

        body = response.text[:2000]

        raise RuntimeError(

            "Copernicus STAC search failed.\n\n"

            f"HTTP Status: "
            f"{response.status_code}\n\n"

            f"Content-Type: "
            f"{content_type}\n\n"

            "Server response:\n"

            f"{body}"

        )

    # --------------------------------------------------------
    # EMPTY RESPONSE
    # --------------------------------------------------------

    if not response.content:

        raise RuntimeError(

            "Copernicus STAC returned an empty "
            "response."

        )

    # --------------------------------------------------------
    # JSON PARSING
    # --------------------------------------------------------

    try:

        data = response.json()

    except ValueError:

        content_type = (
            response.headers.get(
                "Content-Type",
                ""
            )
        )

        body = response.text[:2000]

        raise RuntimeError(

            "Copernicus STAC returned an invalid "
            "JSON response.\n\n"

            f"Content-Type: "
            f"{content_type}\n\n"

            "Response received:\n"

            f"{body}"

        )

    # --------------------------------------------------------
    # VERIFY STAC RESPONSE
    # --------------------------------------------------------

    if not isinstance(
        data,
        dict
    ):

        raise RuntimeError(

            "Copernicus STAC returned an "
            "unexpected response format."

        )

    # --------------------------------------------------------
    # FEATURES
    # --------------------------------------------------------

    features = data.get(
        "features"
    )

    if features is None:

        raise RuntimeError(

            "Copernicus STAC response does not "
            "contain a 'features' field.\n\n"

            f"Response keys: "
            f"{list(data.keys())}"

        )

    if not isinstance(
        features,
        list
    ):

        raise RuntimeError(

            "Copernicus STAC 'features' field "
            "is not a list."

        )

    print(
        "[SATQUERY] Products returned:",
        len(features)
    )

    # ========================================================
    # LOCAL CLOUD FILTER
    # ========================================================

    filtered = []

    for item in features:

        if not isinstance(
            item,
            dict
        ):
            continue

        properties = item.get(
            "properties",
            {}
        )

        cloud = properties.get(
            "eo:cloud_cover"
        )

        cloud = _safe_float(
            cloud,
            100.0
        )

        if cloud <= float(
            cloud_limit
        ):

            filtered.append(
                item
            )

    print(
        "[SATQUERY] Products after "
        "cloud filtering:",
        len(filtered)
    )

    # --------------------------------------------------------
    # PRINT SCENES
    # --------------------------------------------------------

    for item in filtered[:10]:

        metadata = _extract_metadata(
            item
        )

        print(
            "  •",
            metadata.get(
                "scene_id"
            ),
            "| date:",
            metadata.get(
                "date"
            ),
            "| cloud:",
            metadata.get(
                "cloud_cover"
            )
        )

    print("=" * 75)

    return filtered


# ============================================================
# EXTRACT METADATA
# ============================================================

def _extract_metadata(
    item
):

    properties = item.get(
        "properties",
        {}
    )

    scene_id = item.get(
        "id",
        "unknown"
    )

    # --------------------------------------------------------
    # Date
    # --------------------------------------------------------

    datetime_value = (

        properties.get(
            "datetime"
        )

        or

        properties.get(
            "start_datetime"
        )

    )

    actual_date = None

    if datetime_value:

        try:

            actual_date = (
                datetime.fromisoformat(
                    str(
                        datetime_value
                    ).replace(
                        "Z",
                        "+00:00"
                    )
                )
                .date()
                .isoformat()
            )

        except Exception:

            actual_date = str(
                datetime_value
            )[:10]

    # --------------------------------------------------------
    # Cloud
    # --------------------------------------------------------

    cloud = _safe_float(

        properties.get(
            "eo:cloud_cover"
        ),

        None

    )

    if cloud is not None:

        cloud = round(
            cloud,
            2
        )

    # --------------------------------------------------------
    # Platform
    # --------------------------------------------------------

    platform = (

        properties.get(
            "platform"
        )

        or

        properties.get(
            "constellation"
        )

        or

        "Sentinel-2"

    )

    return {

        "scene_id":
            scene_id,

        "date":
            actual_date,

        "cloud_cover":
            cloud,

        "platform":
            platform,

        "source":
            "Copernicus Data Space / Sentinel-2 L2A",

        "collection":
            SENTINEL_COLLECTION,

        "product_type":
            "S2MSI2A"

    }


# ============================================================
# FIND IMAGE ASSET
# ============================================================

def _get_image_asset(
    item
):

    """
    Find a usable preview/thumbnail image
    from STAC assets.
    """

    assets = item.get(
        "assets",
        {}
    )

    if not isinstance(
        assets,
        dict
    ):

        return None, None

    # --------------------------------------------------------
    # Preferred asset names
    # --------------------------------------------------------

    preferred_names = [

        "thumbnail",

        "preview",

        "visual",

        "rendered_preview",

        "quicklook",

        "browse",

        "overview",

        "true-color",

        "true_color"

    ]

    for name in preferred_names:

        asset = assets.get(
            name
        )

        if not isinstance(
            asset,
            dict
        ):
            continue

        href = asset.get(
            "href"
        )

        if not href:
            continue

        asset_type = str(
            asset.get(
                "type",
                ""
            )
        ).lower()

        title = str(
            asset.get(
                "title",
                ""
            )
        ).lower()

        if (

            "image" in asset_type

            or

            any(
                ext in href.lower()
                for ext in [
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".webp"
                ]
            )

            or

            "thumbnail" in title

            or

            "preview" in title

        ):

            return (
                href,
                name
            )

    # --------------------------------------------------------
    # Generic image asset
    # --------------------------------------------------------

    for name, asset in assets.items():

        if not isinstance(
            asset,
            dict
        ):
            continue

        href = asset.get(
            "href"
        )

        if not href:
            continue

        asset_type = str(
            asset.get(
                "type",
                ""
            )
        ).lower()

        roles = asset.get(
            "roles",
            []
        )

        if not isinstance(
            roles,
            list
        ):

            roles = []

        roles = [
            str(x).lower()
            for x in roles
        ]

        if (

            "image" in asset_type

            or

            "thumbnail" in roles

            or

            "overview" in roles

            or

            "visual" in roles

        ):

            return (
                href,
                name
            )

    return (
        None,
        None
    )


# ============================================================
# DOWNLOAD IMAGE
# ============================================================

def _download_image(
    image_url,
    output_path
):

    """
    Download a real Copernicus preview image.
    """

    print()
    print(
        "[SATQUERY] Downloading real "
        "Sentinel-2 preview:"
    )

    print(
        image_url
    )

    try:

        response = requests.get(

            image_url,

            timeout=REQUEST_TIMEOUT,

            headers={

                "User-Agent":
                    "SATQuery-AI/1.0",

                "Accept":
                    "image/avif,image/webp,"
                    "image/apng,image/svg+xml,"
                    "image/*,*/*;q=0.8"
            }

        )

    except requests.RequestException as e:

        raise RuntimeError(

            "Could not download the "
            "Sentinel-2 preview image.\n\n"

            f"URL: {image_url}\n\n"

            f"Error: {e}"

        )

    print(
        "[SATQUERY] Image HTTP status:",
        response.status_code
    )

    if response.status_code != 200:

        raise RuntimeError(

            "Sentinel-2 image download failed.\n\n"

            f"HTTP Status: "
            f"{response.status_code}\n\n"

            f"URL: {image_url}\n\n"

            f"Response: "
            f"{response.text[:1000]}"

        )

    content = response.content

    if not content:

        raise RuntimeError(

            "Copernicus returned an empty "
            "image file."

        )

    # --------------------------------------------------------
    # Basic image signature validation
    # --------------------------------------------------------

    is_jpeg = (
        content[:3]
        ==
        b"\xff\xd8\xff"
    )

    is_png = (
        content[:8]
        ==
        b"\x89PNG\r\n\x1a\n"
    )

    is_webp = (
        len(content) >= 12
        and content[:4] == b"RIFF"
        and content[8:12] == b"WEBP"
    )

    if not (
        is_jpeg
        or is_png
        or is_webp
    ):

        content_type = (
            response.headers.get(
                "Content-Type",
                ""
            )
        )

        raise RuntimeError(

            "Copernicus returned something "
            "that is not a supported image.\n\n"

            f"Content-Type: "
            f"{content_type}\n\n"

            f"First bytes: "
            f"{content[:30]!r}\n\n"

            "This usually means the selected "
            "STAC asset is not a public preview."

        )

    with open(
        output_path,
        "wb"
    ) as file:

        file.write(
            content
        )

    print(
        "[SATQUERY] Image saved:",
        output_path
    )

    return output_path


# ============================================================
# PREPARE SCENE
# ============================================================

def _prepare_scene(
    item,
    label
):

    metadata = _extract_metadata(
        item
    )

    image_url, asset_name = (
        _get_image_asset(
            item
        )
    )

    if not image_url:

        assets = item.get(
            "assets",
            {}
        )

        available_assets = list(
            assets.keys()
        ) if isinstance(
            assets,
            dict
        ) else []

        raise RuntimeError(

            "No usable preview image was found "
            "for Sentinel-2 scene.\n\n"

            f"Scene: "
            f"{metadata['scene_id']}\n\n"

            f"Available assets: "
            f"{available_assets}"

        )

    metadata[
        "asset_name"
    ] = asset_name

    metadata[
        "remote_url"
    ] = image_url

    # --------------------------------------------------------
    # Safe filename
    # --------------------------------------------------------

    scene_id = str(
        metadata[
            "scene_id"
        ]
    )

    safe_id = "".join(

        character
        if (
            character.isalnum()
            or character in "-_"
        )
        else "_"

        for character in scene_id

    )

    # --------------------------------------------------------
    # Determine extension
    # --------------------------------------------------------

    lower_url = image_url.lower()

    if ".png" in lower_url:

        extension = ".png"

    elif ".webp" in lower_url:

        extension = ".webp"

    else:

        extension = ".jpg"

    filename = (
        f"{label}_{safe_id}{extension}"
    )

    output_path = (
        CACHE_DIR
        / filename
    )

    # --------------------------------------------------------
    # Download / cache
    # --------------------------------------------------------

    if (

        not output_path.exists()

        or

        output_path.stat().st_size < 1000

    ):

        _download_image(

            image_url,

            output_path

        )

    else:

        print(
            "[SATQUERY] Using cached image:",
            output_path
        )

    # --------------------------------------------------------
    # Local HTTP server
    # --------------------------------------------------------

    _start_local_server()

    local_url = (

        f"http://{LOCAL_HOST}:"
        f"{LOCAL_PORT}/"
        f"{filename}"

    )

    metadata[
        "local_path"
    ] = str(
        output_path
    )

    metadata[
        "image_url"
    ] = local_url

    metadata[
        "local_url"
    ] = local_url

    return metadata


# ============================================================
# SELECT BEFORE / AFTER
# ============================================================

def _select_before_after(
    products
):

    """
    Select two scenes with different acquisition dates.

    Returns:
        before_item, after_item
    """

    if not products:

        return (
            None,
            None
        )

    # --------------------------------------------------------
    # Sort oldest -> newest
    # --------------------------------------------------------

    sorted_products = sorted(

        products,

        key=lambda item:
            str(
                item.get(
                    "properties",
                    {}
                ).get(
                    "datetime",
                    ""
                )
            )

    )

    unique_products = []

    seen_dates = set()

    for item in sorted_products:

        metadata = _extract_metadata(
            item
        )

        scene_date = metadata.get(
            "date"
        )

        if not scene_date:

            continue

        if scene_date in seen_dates:

            continue

        seen_dates.add(
            scene_date
        )

        unique_products.append(
            item
        )

    if len(
        unique_products
    ) < 2:

        return (
            unique_products[0]
            if unique_products
            else None,
            None
        )

    # --------------------------------------------------------
    # Oldest and newest
    # --------------------------------------------------------

    return (

        unique_products[0],

        unique_products[-1]

    )


# ============================================================
# MAIN SATELLITE COMPARISON FUNCTION
# ============================================================

def get_satellite_comparison(
    latitude,
    longitude,
    from_date,
    to_date
):

    """
    Main function called by app.py.

    Returns a dictionary containing:
        before_url
        after_url
        metadata
        actual dates
        coordinates
        source
        scene IDs
    """

    started = time.perf_counter()

    # ========================================================
    # VALIDATE COORDINATES
    # ========================================================

    try:

        latitude = float(
            latitude
        )

        longitude = float(
            longitude
        )

    except (
        TypeError,
        ValueError
    ):

        raise ValueError(
            "Invalid latitude/longitude."
        )

    if not (
        -90 <= latitude <= 90
    ):

        raise ValueError(
            "Latitude must be between "
            "-90 and 90."
        )

    if not (
        -180 <= longitude <= 180
    ):

        raise ValueError(
            "Longitude must be between "
            "-180 and 180."
        )

    # ========================================================
    # PARSE DATES
    # ========================================================

    start = _parse_date(
        from_date
    )

    end = _parse_date(
        to_date
    )

    if end < start:

        raise ValueError(
            "The AFTER date must be greater "
            "than or equal to the BEFORE date."
        )

    print()
    print("#" * 75)
    print("SATQUERY AI - REAL SENTINEL-2")
    print("#" * 75)

    print(
        "Latitude:",
        latitude
    )

    print(
        "Longitude:",
        longitude
    )

    print(
        "Requested from:",
        start.date()
    )

    print(
        "Requested to:",
        end.date()
    )

    print("#" * 75)

    # ========================================================
    # SEARCH STRATEGY
    # ========================================================

    # First strict search.
    #
    # If only one scene is available, progressively
    # increase cloud limit.
    #
    # This does NOT create fake data.
    # ========================================================

    cloud_limits = [

        20.0,

        30.0,

        50.0

    ]

    products = []

    used_cloud_limit = None

    # --------------------------------------------------------
    # Search requested date range
    # --------------------------------------------------------

    for cloud_limit in cloud_limits:

        print()
        print(
            "[SATQUERY] Trying cloud limit:",
            cloud_limit
        )

        products = _search_stac(

            latitude=latitude,

            longitude=longitude,

            start_date=start,

            end_date=end,

            cloud_limit=cloud_limit,

            limit=50

        )

        if len(
            products
        ) >= 2:

            used_cloud_limit = (
                cloud_limit
            )

            break

    # --------------------------------------------------------
    # No products
    # --------------------------------------------------------

    if not products:

        raise RuntimeError(

            "No suitable Sentinel-2 L2A image "
            "was found.\n\n"

            f"Location: "
            f"{latitude:.6f}, "
            f"{longitude:.6f}\n\n"

            f"Date range: "
            f"{start.date()} to "
            f"{end.date()}\n\n"

            "Try increasing the date range."

        )

    # ========================================================
    # SELECT BEFORE / AFTER
    # ========================================================

    before_item, after_item = (
        _select_before_after(
            products
        )
    )

    # ========================================================
    # ONLY ONE UNIQUE SCENE
    # ========================================================

    if (
        before_item is None
        or after_item is None
    ):

        print()
        print(
            "[SATQUERY] Only one unique "
            "acquisition date found."
        )

        # ----------------------------------------------------
        # Search wider range
        # ----------------------------------------------------

        wider_start = (
            start
            - timedelta(
                days=60
            )
        )

        wider_end = (
            end
            + timedelta(
                days=60
            )
        )

        print(
            "[SATQUERY] Expanding temporal "
            "window:"
        )

        print(
            wider_start.date(),
            "to",
            wider_end.date()
        )

        wider_products = []

        for cloud_limit in cloud_limits:

            wider_products = _search_stac(

                latitude=latitude,

                longitude=longitude,

                start_date=wider_start,

                end_date=wider_end,

                cloud_limit=cloud_limit,

                limit=100

            )

            if len(
                wider_products
            ) >= 2:

                used_cloud_limit = (
                    cloud_limit
                )

                break

        before_item, after_item = (
            _select_before_after(
                wider_products
            )
        )

    # ========================================================
    # FINAL VALIDATION
    # ========================================================

    if (
        before_item is None
        or after_item is None
    ):

        raise RuntimeError(

            "Could not find two different "
            "Sentinel-2 acquisition dates "
            "for temporal comparison.\n\n"

            f"Requested period: "
            f"{start.date()} to "
            f"{end.date()}\n\n"

            "Try a wider date range."

        )

    # ========================================================
    # PREPARE BEFORE
    # ========================================================

    before = _prepare_scene(

        before_item,

        "before"

    )

    # ========================================================
    # PREPARE AFTER
    # ========================================================

    after = _prepare_scene(

        after_item,

        "after"

    )

    # ========================================================
    # ENSURE DIFFERENT SCENES
    # ========================================================

    if (

        before["scene_id"]
        ==
        after["scene_id"]

    ):

        raise RuntimeError(

            "Before and after scenes are "
            "identical.\n\n"

            "Temporal change detection requires "
            "two different Sentinel-2 scenes."

        )

    if (

        before["date"]
        ==
        after["date"]

    ):

        raise RuntimeError(

            "Before and after images have "
            "the same acquisition date.\n\n"

            "Two different dates are required."

        )

    # ========================================================
    # PROCESSING TIME
    # ========================================================

    elapsed = (
        time.perf_counter()
        - started
    )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    result = {

        # ----------------------------------------------------
        # Main URLs
        # ----------------------------------------------------

        "before_url":
            before["image_url"],

        "after_url":
            after["image_url"],

        "before_image":
            before["image_url"],

        "after_image":
            after["image_url"],

        "image_before":
            before["image_url"],

        "image_after":
            after["image_url"],

        # ----------------------------------------------------
        # Before metadata
        # ----------------------------------------------------

        "before": {

            "image_url":
                before["image_url"],

            "before_url":
                before["image_url"],

            "scene_id":
                before["scene_id"],

            "date":
                before["date"],

            "cloud_cover":
                before["cloud_cover"],

            "platform":
                before["platform"],

            "source":
                before["source"],

            "collection":
                before["collection"],

            "product_type":
                before["product_type"],

            "asset_name":
                before["asset_name"],

            "remote_url":
                before["remote_url"],

            "local_path":
                before["local_path"]

        },

        # ----------------------------------------------------
        # After metadata
        # ----------------------------------------------------

        "after": {

            "image_url":
                after["image_url"],

            "after_url":
                after["image_url"],

            "scene_id":
                after["scene_id"],

            "date":
                after["date"],

            "cloud_cover":
                after["cloud_cover"],

            "platform":
                after["platform"],

            "source":
                after["source"],

            "collection":
                after["collection"],

            "product_type":
                after["product_type"],

            "asset_name":
                after["asset_name"],

            "remote_url":
                after["remote_url"],

            "local_path":
                after["local_path"]

        },

        # ----------------------------------------------------
        # Global source
        # ----------------------------------------------------

        "source":
            "Copernicus Data Space / Sentinel-2 L2A",

        "mode":
            "REAL_SENTINEL_2_STAC",

        "collection":
            SENTINEL_COLLECTION,

        "product_type":
            "S2MSI2A",

        # ----------------------------------------------------
        # Scene ID
        # ----------------------------------------------------

        "scene_id":
            after["scene_id"],

        "before_scene_id":
            before["scene_id"],

        "after_scene_id":
            after["scene_id"],

        # ----------------------------------------------------
        # Coordinates
        # ----------------------------------------------------

        "coordinates": {

            "latitude":
                latitude,

            "longitude":
                longitude

        },

        # ----------------------------------------------------
        # Requested dates
        # ----------------------------------------------------

        "dates": {

            "from":
                start.strftime(
                    "%Y-%m-%d"
                ),

            "to":
                end.strftime(
                    "%Y-%m-%d"
                )

        },

        # ----------------------------------------------------
        # Actual acquisition dates
        # ----------------------------------------------------

        "actual_dates": {

            "before":
                before["date"],

            "after":
                after["date"]

        },

        # ----------------------------------------------------
        # Cloud information
        # ----------------------------------------------------

        "cloud_limit_used":
            used_cloud_limit,

        "before_cloud_cover":
            before["cloud_cover"],

        "after_cloud_cover":
            after["cloud_cover"],

        # ----------------------------------------------------
        # Performance
        # ----------------------------------------------------

        "processing_time_seconds":
            round(
                elapsed,
                2
            ),

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        "status":
            "SUCCESS",

        "real_data":
            True

    }

    # ========================================================
    # LOG RESULT
    # ========================================================

    print()
    print("=" * 75)
    print("REAL SENTINEL-2 DATA SUCCESSFULLY LOADED")
    print("=" * 75)

    print()
    print("BEFORE")
    print(
        "Scene:",
        before["scene_id"]
    )
    print(
        "Date:",
        before["date"]
    )
    print(
        "Cloud:",
        before["cloud_cover"]
    )

    print()
    print("AFTER")
    print(
        "Scene:",
        after["scene_id"]
    )
    print(
        "Date:",
        after["date"]
    )
    print(
        "Cloud:",
        after["cloud_cover"]
    )

    print()
    print(
        "Before URL:",
        before["image_url"]
    )

    print(
        "After URL:",
        after["image_url"]
    )

    print()
    print(
        "Processing time:",
        round(
            elapsed,
            2
        ),
        "seconds"
    )

    print("=" * 75)

    return result


# ============================================================
# OPTIONAL TEST
# ============================================================

if __name__ == "__main__":

    print()
    print(
        "Testing SATQuery AI satellite module..."
    )

    try:

        test_result = (
            get_satellite_comparison(

                latitude=28.6139,

                longitude=77.2090,

                from_date="2024-08-01",

                to_date="2024-09-30"

            )
        )

        print()
        print(
            "TEST SUCCESS"
        )

        print(
            "Before:",
            test_result[
                "actual_dates"
            ][
                "before"
            ]
        )

        print(
            "After:",
            test_result[
                "actual_dates"
            ][
                "after"
            ]
        )

    except Exception as e:

        print()
        print(
            "TEST FAILED"
        )

        print(
            str(e)
        )