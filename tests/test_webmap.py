"""Tests de construccion del JSON del web map y utilidades relacionadas."""

from sheets_agol_kit import (
    build_webmap_json,
    gviz_csv_url,
    simple_marker,
    unique_value_renderer,
)

FIELDS = [
    {"name": "lat", "type": "esriFieldTypeDouble", "alias": "lat"},
    {"name": "lon", "type": "esriFieldTypeDouble", "alias": "lon"},
]


def test_gviz_csv_url():
    assert gviz_csv_url("ABC123", "mapa") == (
        "https://docs.google.com/spreadsheets/d/ABC123/gviz/tq?tqx=out:csv&sheet=mapa"
    )


def test_simple_marker():
    marker = simple_marker((230, 57, 53, 255), size=12, outline_width=2)
    assert marker["type"] == "esriSMS"
    assert marker["color"] == [230, 57, 53, 255]
    assert marker["size"] == 12
    assert marker["outline"]["width"] == 2


def test_unique_value_renderer():
    renderer = unique_value_renderer(
        "estado",
        {"reportado": (230, 57, 53, 255), "limpio": (67, 160, 71, 255)},
        default_label="Otro",
    )
    assert renderer["type"] == "uniqueValue"
    assert renderer["field1"] == "estado"
    assert renderer["defaultLabel"] == "Otro"
    infos = {info["value"]: info for info in renderer["uniqueValueInfos"]}
    assert infos["reportado"]["label"] == "Reportado"
    assert infos["reportado"]["symbol"]["color"] == [230, 57, 53, 255]
    assert infos["limpio"]["symbol"]["color"] == [67, 160, 71, 255]


class TestBuildWebmapJson:
    def build(self, **overrides):
        kwargs = {
            "csv_url": "https://example.com/data.csv",
            "fields": FIELDS,
            "layer_title": "Mis reportes",
            "renderer": {"type": "simple"},
        }
        kwargs.update(overrides)
        return build_webmap_json(**kwargs)

    def test_capa_csv(self):
        webmap = self.build()
        (layer,) = webmap["operationalLayers"]
        assert layer["layerType"] == "CSV"
        assert layer["url"] == "https://example.com/data.csv"
        assert layer["title"] == "Mis reportes"
        assert layer["refreshInterval"] == 1
        assert layer["locationInfo"]["latitudeFieldName"] == "lat"
        assert layer["layerDefinition"]["fields"] == FIELDS
        assert layer["layerDefinition"]["drawingInfo"]["renderer"] == {"type": "simple"}

    def test_campos_de_coordenadas_configurables(self):
        webmap = self.build(lat_field="latitud", lon_field="longitud")
        location = webmap["operationalLayers"][0]["locationInfo"]
        assert location["latitudeFieldName"] == "latitud"
        assert location["longitudeFieldName"] == "longitud"

    def test_sin_popup_ni_extent_por_defecto(self):
        webmap = self.build()
        assert "popupInfo" not in webmap["operationalLayers"][0]
        assert "initialState" not in webmap

    def test_popup_info(self):
        popup = {"title": "{lugar}"}
        webmap = self.build(popup_info=popup)
        assert webmap["operationalLayers"][0]["popupInfo"] == popup

    def test_extent_define_vista_inicial(self):
        extent = {"xmin": -67.5, "ymin": 17.6, "xmax": -65.1, "ymax": 18.7}
        webmap = self.build(extent=extent)
        geometry = webmap["initialState"]["viewpoint"]["targetGeometry"]
        assert geometry["xmin"] == -67.5
        assert geometry["spatialReference"] == {"wkid": 4326}

    def test_basemap_por_defecto_y_custom(self):
        assert self.build()["baseMap"]["title"] == "Topographic"
        custom = {"title": "Mi basemap", "baseMapLayers": []}
        assert self.build(basemap=custom)["baseMap"] == custom
