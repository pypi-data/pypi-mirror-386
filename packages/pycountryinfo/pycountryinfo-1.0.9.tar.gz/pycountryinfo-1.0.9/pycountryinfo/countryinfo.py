import json
from typing import List, Dict, Tuple
from pycountryinfo.country_types import CountryInfoTypes
from importlib.resources import files

associated_countries = [
    "American Samoa",
    "Anguilla",
    "Antarctica",
    "Aruba",
    "Bermuda",
    "Bouvet Island",
    "British Indian Ocean Territory",
    "British Virgin Islands",
    "Caribbean Netherlands",
    "Cayman Islands",
    "Christmas Island",
    "Cocos (Keeling) Islands",
    "Cook Islands",
    "Curaçao",
    "Falkland Islands",
    "Faroe Islands",
    "French Guiana",
    "French Polynesia",
    "French Southern and Antarctic Lands",
    "Gibraltar",
    "Greenland",
    "Guadeloupe",
    "Guam",
    "Guernsey",
    "Heard Island and McDonald Islands",
    "Hong Kong",
    "Isle of Man",
    "Jersey",
    "Kosovo",
    "Macau",
    "Martinique",
    "Mayotte",
    "Montserrat",
    "New Caledonia",
    "Niue",
    "Norfolk Island",
    "Northern Mariana Islands",
    "Pitcairn Islands",
    "Puerto Rico",
    "Réunion",
    "Saint Barthélemy",
    "Saint Helena, Ascension and Tristan da Cunha",
    "Saint Martin",
    "Saint Pierre and Miquelon",
    "Sint Maarten",
    "South Georgia",
    "Svalbard and Jan Mayen",
    "Tokelau",
    "Turks and Caicos Islands",
    "United States Minor Outlying Islands",
    "United States Virgin Islands",
    "Wallis and Futuna",
    "Western Sahara",
    "Åland Islands",
    "Dominica",
    "DR Congo",
    "British Indian Ocean Territory",
]

class PyCountryInfo:
    def __init__(self, country:str = ""):
        self.country_name_type:str = 'common'
        self.countries_list:List[CountryInfoTypes] | None = None
        if self.country_name_type not in ['common', 'official']:
            raise ValueError("Invalid country name type. Use 'common' or 'official'.")
        
        try:
            countries_file = files('pycountryinfo.data').joinpath('countries.json')
            with countries_file.open('r') as file:
                self.countries_list = json.load(file)
        except FileNotFoundError:
            raise ValueError("The countries data file is missing.")
        except json.JSONDecodeError:
            raise ValueError("The countries data file is not in a valid JSON format.")
        
        if not self.countries_list:
            raise ValueError("The countries data is empty or invalid.")
        
        self.name_key = 'common_name' if self.country_name_type == 'common' else 'official_name'
        self.countries_dict: Dict[str, CountryInfoTypes] = {item[self.name_key].title(): item for item in self.countries_list}
        self.country = country
        self.country_data:CountryInfoTypes | None = self.countries_dict.get(self.country.title()) 
        if self.country and not self.country_data:
            raise ValueError(f"{country} is not a valid country name. If you are using the country's official name, make sure you set the 'country_name_type' argument to 'official'.")
        
        self.nationalities:Tuple[str, ...] | None = None
        self.countries:Tuple[str, ...] | None = None
            
    def validate_country(self, country: str) -> CountryInfoTypes:
        country_data = self.countries_dict.get(country.title())
        if not country_data:
            raise ValueError(f"{country} is not a valid country name. If you are using the country's official name, make sure you set the 'country_name_type' argument to 'official'.")
        return country_data
        
    def get_nationality(self, country:str) -> str:
        return self.validate_country(country).get('nationality')
    
    def get_nationalities(self) -> Tuple[str, ...]:
        if not self.nationalities:
            self.nationalities = tuple(item['nationality'] for item in self.countries_list)
        return self.nationalities

    def is_valid_country_nationality(self, country:str, nationality:str) -> bool:
        return nationality.title() == self.validate_country(country).get('nationality', '').title()
    
    def is_valid_nationality(self, nationality:str) -> bool:
        return nationality.title() in self.get_nationalities()

    def get_country_from_nationality(self, nationality:str) -> str:
        country = None
        countries = [item[self.name_key] for item in self.countries_list if nationality.title() == item['nationality'].title()]
        if len(countries) > 1:
            country = [item for item in countries if item not in associated_countries]
            if not country:
                country = countries
        elif len(countries) == 1:
            country = countries
        
        if not country:
            raise ValueError(f"{nationality} is not a valid nationality")
        return country[0]

    def get_countries(self) -> Tuple[str, ...]:
        if not self.countries:
            self.countries = tuple(item[self.name_key] for item in self.countries_list)
        return self.countries

    def is_valid_country(self, country:str) -> bool:
        return country.title() in self.countries_dict
    
    def get_provinces(self, country:str) -> List[str]:
        return self.validate_country(country.title()).get('provinces')

    def is_valid_country_province(self, country:str, province:str) -> bool:
        return province in self.get_provinces(country)