"""Creacion de un Web Map en ArcGIS Online cuya capa es un CSV por URL.

Pensado para cuentas publicas de AGOL (sin hosted feature layers): el web map
lee un CSV remoto (ej. el endpoint gviz de un Google Sheet) con refresh
interval, simbologia por valores unicos y pop-ups.

Requiere el extra opcional: pip install sheets-agol-kit[agol]
(la libreria arcgis se importa solo dentro de create_webmap).
"""

import json
import uuid

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


def simple_marker(color, size=10, outline_width=1):
    """Simbolo de punto circular (color RGBA como lista de 4 enteros)."""
    return {
        "type": "esriSMS",
        "style": "esriSMSCircle",
        "color": list(color),
        "size": size,
        "outline": {"color": [255, 255, 255, 255], "width": outline_width},
    }


def unique_value_renderer(
    field, value_colors, default_color=(120, 120, 120, 255), default_label="Otro"
):
    """Renderer por valores unicos de un campo (dict valor -> color RGBA)."""
    return {
        "type": "uniqueValue",
        "field1": field,
        "defaultSymbol": simple_marker(default_color),
        "defaultLabel": default_label,
        "uniqueValueInfos": [
            {"value": value, "label": str(value).capitalize(), "symbol": simple_marker(color)}
            for value, color in value_colors.items()
        ],
    }


def build_webmap_json(
    *,
    csv_url,
    fields,
    layer_title,
    renderer,
    popup_info=None,
    extent=None,
    refresh_interval=1,
    lat_field="lat",
    lon_field="lon",
    basemap=None,
    authoring_app="sheets-agol-kit",
):
    """Construye el JSON del web map con una unica capa CSV por URL.

    Args:
        csv_url: URL del CSV (ej. sheets.gviz_csv_url()).
        fields: lista de campos esri ({"name", "type", "alias"}).
        layer_title: titulo de la capa operacional.
        renderer: drawingInfo renderer (ej. unique_value_renderer()).
        popup_info: dict popupInfo o None para no configurar pop-ups.
        extent: vista inicial {"xmin", "ymin", "xmax", "ymax"} en WGS84 o None.
        refresh_interval: minutos entre refrescos de la capa CSV.
        lat_field / lon_field: nombres de las columnas de coordenadas.
        basemap: dict baseMap; por defecto el topografico de Esri.
    """
    layer = {
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

    webmap = {
        "version": "2.30",
        "authoringApp": authoring_app,
        "authoringAppVersion": "1.0",
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
    username,
    password,
    title,
    webmap_json,
    tags="",
    snippet="",
    share_everyone=True,
    portal_url="https://www.arcgis.com",
):
    """Crea el item Web Map en ArcGIS Online y devuelve el item creado.

    Requiere la libreria arcgis (extra [agol]).
    """
    from arcgis.gis import GIS, ItemProperties, ItemTypeEnum

    gis = GIS(portal_url, username, password)
    # gis.content.add() esta roto en arcgis 2.4.3 con pandas 3.x
    # (AttributeError: _is_geoenabled); se usa la API nueva Folder.add()
    folder = gis.content.folders.get()  # carpeta raiz del usuario
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
