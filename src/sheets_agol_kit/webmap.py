"""Create an ArcGIS Online Web Map whose layer is a CSV by URL.

Aimed at public AGOL accounts (no hosted feature layers): the web map
reads a remote CSV (e.g. a Google Sheet gviz endpoint) with a refresh
interval, unique-value symbology, and pop-ups.

Requires the optional extra: pip install sheets-agol-kit[agol]
(the arcgis library is imported only inside create_webmap).
"""

import json
import uuid
from collections.abc import Mapping, Sequence
from typing import Any

DEFAULT_BASEMAP = {
    "title": "Topographic",
    "baseMapLayers": [
        {
            "id": "basemap",
            "layerType": "ArcGISTiledMapServiceLayer",
            "url": (
                "https://services.arcgisonline.com/ArcGIS/rest/services/"
                "World_Topo_Map/MapServer"
            ),
            "title": "World Topographic Map",
        }
    ],
}

# RGBA color as a sequence of 4 integers 0-255
Color = Sequence[int]


def simple_marker(
    color: Color, size: int = 10, outline_width: int = 1
) -> dict[str, Any]:
    """Circular point symbol (RGBA color as a list of 4 integers)."""
    return {
        "type": "esriSMS",
        "style": "esriSMSCircle",
        "color": list(color),
        "size": size,
        "outline": {"color": [255, 255, 255, 255], "width": outline_width},
    }


def unique_value_renderer(
    field: str,
    value_colors: Mapping[Any, Color],
    default_color: Color = (120, 120, 120, 255),
    default_label: str = "Other",
) -> dict[str, Any]:
    """Unique-value renderer for a field (dict value -> RGBA color)."""
    return {
        "type": "uniqueValue",
        "field1": field,
        "defaultSymbol": simple_marker(default_color),
        "defaultLabel": default_label,
        "uniqueValueInfos": [
            {
                "value": value,
                "label": str(value).capitalize(),
                "symbol": simple_marker(color),
            }
            for value, color in value_colors.items()
        ],
    }


def build_webmap_json(
    *,
    csv_url: str,
    fields: list[dict[str, str]],
    layer_title: str,
    renderer: dict[str, Any],
    popup_info: dict[str, Any] | None = None,
    extent: Mapping[str, float] | None = None,
    refresh_interval: float = 1,
    lat_field: str = "lat",
    lon_field: str = "lon",
    basemap: dict[str, Any] | None = None,
    authoring_app: str = "sheets-agol-kit",
) -> dict[str, Any]:
    """Build the web map JSON with a single CSV layer by URL.

    Args:
        csv_url: CSV URL (e.g. sheets.gviz_csv_url()).
        fields: list of esri fields ({"name", "type", "alias"}).
        layer_title: operational layer title.
        renderer: drawingInfo renderer (e.g. unique_value_renderer()).
        popup_info: popupInfo dict or None to skip pop-ups.
        extent: initial view {"xmin", "ymin", "xmax", "ymax"} in WGS84 or None.
        refresh_interval: minutes between CSV layer refreshes.
        lat_field / lon_field: coordinate column names.
        basemap: baseMap dict; defaults to Esri topographic.
    """
    from . import __version__

    layer: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "title": layer_title,
        "layerType": "CSV",
        "url": csv_url,
        "refreshInterval": refresh_interval,
        "columnDelimiter": ",",
        "locationInfo": {
            "locationType": "coordinates",
            "latitudeFieldName": lat_field,
            "longitudeFieldName": lon_field,
        },
        "layerDefinition": {
            "geometryType": "esriGeometryPoint",
            "objectIdField": "__OBJECTID",
            "fields": fields,
            "drawingInfo": {"renderer": renderer},
        },
    }
    if popup_info:
        layer["popupInfo"] = popup_info

    webmap: dict[str, Any] = {
        "version": "2.30",
        "authoringApp": authoring_app,
        "authoringAppVersion": __version__,
        "spatialReference": {"wkid": 102100, "latestWkid": 3857},
        "baseMap": basemap or DEFAULT_BASEMAP,
        "operationalLayers": [layer],
    }
    if extent:
        webmap["initialState"] = {
            "viewpoint": {
                "targetGeometry": {
                    **extent,
                    "spatialReference": {"wkid": 4326},
                }
            }
        }
    return webmap


def create_webmap(
    *,
    username: str,
    password: str,
    title: str,
    webmap_json: dict[str, Any],
    tags: str = "",
    snippet: str = "",
    share_everyone: bool = True,
    portal_url: str = "https://www.arcgis.com",
) -> Any:
    """Create the Web Map item on ArcGIS Online and return the created item.

    Requires the arcgis library ([agol] extra).
    """
    from arcgis.gis import GIS, ItemProperties, ItemTypeEnum

    gis = GIS(portal_url, username, password)
    # gis.content.add() is broken in arcgis 2.4.3 with pandas 3.x
    # (AttributeError: _is_geoenabled); use the newer Folder.add() API
    folder = gis.content.folders.get()  # user root folder
    job = folder.add(
        item_properties=ItemProperties(
            title=title,
            item_type=ItemTypeEnum.WEB_MAP,
            tags=tags,
            snippet=snippet,
        ),
        text=json.dumps(webmap_json),
    )
    item = job.result()
    if share_everyone:
        item.share(everyone=True)
    return item
