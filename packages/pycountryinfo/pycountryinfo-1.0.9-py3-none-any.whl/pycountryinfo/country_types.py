from typing import TypedDict, List, Dict, Optional, Union

class IsoCodesTypes(TypedDict):
    alpha_2: str
    alpha_3: str
    numeric: str

class CurrencyTypes(TypedDict):
    name: str
    code: str
    symbol: str

class AreaGeometryTypes(TypedDict):
    type: str
    coordinates: List[List[float]]

class AdditionalCountryInfoTypes(TypedDict):
    provinces: List[str]
    area_geometry: AreaGeometryTypes | None

class CountryInfoTypes(TypedDict):
    common_name: str
    official_name: str
    iso_codes: IsoCodesTypes
    provinces: List[str]
    area_geometry: Union[AreaGeometryTypes, None]
    region: str
    subregion: str
    capital: Optional[str]
    languages: List[str]
    population: int
    area: float
    currency: CurrencyTypes
    timezones: List[str]
    borders: List[str]
    nationality: str
    flag: str
    translations: Dict[str, Dict[str, str]]
    latlng: List[float]
    gini_index: Dict[str, float]
    independent: bool
    calling_code: str
    alt_spellings: List[str]
    wiki: str