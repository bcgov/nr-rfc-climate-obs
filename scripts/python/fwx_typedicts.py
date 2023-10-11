# auto generated using: https://json2pyi.pages.dev/#Dataclass

from __future__ import annotations

from typing import Any, List, TypedDict, Union


class WeatherStation(TypedDict):
    type: str
    elevation: float
    fineFuelMoistureCode: float
    fireCentre: str
    fireWeatherIndex: float
    geometry: Geometry
    initialSpreadIndex: float
    links: List[Any]
    precipPluvio1Status: float
    precipPluvio1Total: float
    precipPluvio2Status: float
    precipPluvio2Total: float
    precipRitTotalPrecipRGT: float
    precipitation: float
    recordType: str
    relativeHumidity: float
    rn1Pluvio1: None
    rn1Pluviop2: float
    rn1RitPrecipRitStatus: float
    snowDepth: float
    snowDepthQuality: None
    solarRadiationCM3: None
    solarRadiationLicor: float
    stationAcronym: str
    stationCode: str
    stationName: str
    temperature: float
    weatherTimestamp: str
    windDirection: float
    windGust: float
    windSpeed: float

class Geometry(TypedDict):
    coordinates: List[float]
    crs: Crs
    type: str

class Crs(TypedDict):
    properties: Properties
    type: str

class Properties(TypedDict):
    name: str


class Station(TypedDict):
    type: str
    aspect: Union[str, None]
    elevation: float
    fireCentre: str
    fireZone: str
    geometry: Geometry
    latitude: float
    links: List[Any]
    longitude: float
    overwinterPrecipInd: bool
    pluvioSnowGaugeInd: bool
    slope: Union[None, float]
    stationAcronym: Union[str, None]
    stationCode: str
    stationName: str
