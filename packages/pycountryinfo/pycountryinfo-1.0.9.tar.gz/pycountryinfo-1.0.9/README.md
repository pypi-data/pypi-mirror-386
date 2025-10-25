# pycountryinfo

**pycountryinfo** is a Python package that provides detailed, preloaded information about countries worldwide. The package comes with up-to-date data sourced from the [REST Countries API](https://restcountries.com/) (and enhanced by us) to ensure accuracy and comprehensiveness.


## Installation

```bash

pip install pycountryinfo

```

## Requirements
* Python 3.7 or higher

## Properties Available for a Country:

* **common_name:** The common name of the country (e.g., 'Ghana').
* **official_name:** The official name of the country (e.g., 'Republic of Ghana').
* **iso_codes:** The ISO codes associated with the country (e.g., {'alpha_2': 'GH', 'alpha_3': 'GHA', 'numeric': '288'}).
* **region:** The region the country belongs to (e.g., 'Africa').
* **subregion:** The subregion the country belongs to (e.g., 'Western Africa').
* **capital:** The capital city of the country (e.g., 'Accra').
* **languages:** A list of languages spoken in the country (e.g., ['English']).
* **population:** The population of the country (e.g., 31072945).
* **area:** The total area of the country in square kilometers (e.g., 238533.0).
* **currency:** The currency used in the country (e.g., {'name': 'Ghanaian cedi', 'code': 'GHS', 'symbol': '₵'}).
* **timezones:** A list of timezones the country falls under (e.g., ['UTC']).
* **borders:** A list of countries that share borders with this country (e.g., ['BFA', 'CIV', 'TGO']).
* **nationality:** The nationality associated with the country (e.g., 'Ghanaian').
* **flag:** The URL of the country's flag image (e.g., 'https://flagcdn.com/w320/gh.png').
* **translations:** Translations of the country's name in different languages
* **latlng:** The latitude and longitude of the country (e.g., [8.0, -2.0]).
* **gini_index:** The Gini index for income inequality in the country (e.g., {'2016': 43.5}).
* **independent:** A boolean indicating whether the country is independent (e.g., True).
* **calling_code:** The international calling code for the country (e.g., '+233').
* **alt_spellings:** Alternative spellings or names for the country (e.g., ['GH']).
* **wiki:** The URL for the country's Wikipedia page (e.g., '').
* **provinces:** A list of provinces or regions within the country (e.g., ['Ashanti', 'Ahafo', 'Bono', ...]).
* **area_geometry:** The geometric representation of the country's area (e.g., {'type': 'Polygon', 'coordinates': [[ [1.060122, 5.928837], [-0.507638, 5.343473], ...]]}).


## Example:
Here’s a quick example on how you might retrieve one of these properties:

```python

# Initialize the PyCountryInfo object for Ghana
pycountryinfo = PyCountryInfo('Ghana')

# Accessing country data
print(pycountryinfo.country_data['common_name'])  # Output: Ghana
print(pycountryinfo.country_data['official_name'])  # Output: Republic of Ghana
print(pycountryinfo.country_data['capital'])  # Output: Accra
print(pycountryinfo.country_data['region'])  # Output: Africa
print(pycountryinfo.country_data['subregion'])  # Output: Western Africa
print(pycountryinfo.country_data['languages'])  # Output: ['English']
print(pycountryinfo.country_data['population'])  # Output: 31072940
print(pycountryinfo.country_data['area'])  # Output: 238533
print(pycountryinfo.country_data['timezones'])  # Output: ['UTC']
print(pycountryinfo.country_data['alt_spellings'])  # Output: ['GH', 'GHA', 'Gold Coast']
print(pycountryinfo.country_data['calling_code'])  # Output: '+233'
print(pycountryinfo.country_data['translations'])  # Output: {'de': 'Ghana', 'es': 'Ghana', 'fr': 'Ghana', ...}
print(pycountryinfo.country_data['independent'])  # Output: True
print(pycountryinfo.country_data['latlng'])  # Output: [7.9465, -1.0232]
print(pycountryinfo.country_data['nationality'])  # Output: 'Ghanaian'
print(pycountryinfo.country_data['provinces'])  # Output: ['Ashanti', 'Ahafo', 'Bono', ...]


```

## Methods

**get_nationality(self, country:str) -> str**
Gets the nationality of the specified country.

* **country**: (str) The name of the country.

**get_nationalities(self) -> Tuple[str, ...]**
Returns a tuple of all nationalities available in the countries data.

**is_valid_country_nationality(self, country:str, nationality:str) -> bool**
Checks if the given nationality is valid for the specified country.

* **country**: (str) The name of the country.
* **nationality**: (str) The nationality to validate.

**is_valid_nationality(self, nationality:str) -> bool**
Checks if the given nationality is valid across all countries.

* **nationality**: (str) The nationality to validate.

**get_country_from_nationality(self, nationality:str) -> str**
Gets the country associated with a given nationality.

* **nationality**: (str) The nationality to get the country for.

**get_countries(self) -> Tuple[str, ...]**
Returns a tuple of all country names available in the data.

**is_valid_country(self, country:str) -> bool**
Checks if the given country name exists in the data.

* **country**: (str) The country name to validate.

**get_provinces(self, country:str) -> List[str]**
Gets a list of provinces for a given country.

* **country**: (str) The name of the country to get provinces for.

**is_valid_country_province(self, country:str, province:str) -> bool**
Checks if a province is valid for a specified country.

* **country**: (str) The name of the country.
* **province**: (str) The province name to validate.


## Example Method Usage

```python
from pycountryinfo.country_info import PyCountryInfo

# Initialize the PyCountryInfo object
country_info = PyCountryInfo(country_name_type='common')

# Get a country's nationality
nationality = country_info.get_nationality('Ghana')
print(nationality)  # Output: 'Ghanaian'

# Get all nationalities
nationalities = country_info.get_nationalities()
print(nationalities)  # Output: ('American', 'Canadian', 'Ghana', ...)

# Get a country's provinces (for example, Ghana)
provinces = country_info.get_provinces('Ghana')
print(provinces)  # Output: ['Ashanti', 'Ahafo', Bono, ...]

# Check if a country is valid
is_valid = country_info.is_valid_country('Ghana')
print(is_valid)  # Output: True

# Get a country from a nationality
country_from_nationality = country_info.get_country_from_nationality('Ghanaian')
print(country_from_nationality)  # Output: 'Ghana'

```


## Contributing

If you'd like to contribute to this package, feel free to fork the repository, make your changes, and submit a pull request.

## License
This project is licensed under the MIT License.

## Contact
If you have questions or suggestions, feel free to [open an issue](https://github.com/Jnyame21/pycountryinfo/issues) or contact [nyamejustice2000@gmail.com](mailto:nyamejustice2000@gmail.com).