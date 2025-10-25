import requests
import xml.etree.ElementTree as ET
from typing import Union, Optional

class CFNames:
    """ An object for accessing CF Standard Name information
    version : int
        version number of the standard names table to access
    """
    XML_URL = "https://cfconventions.org/Data/cf-standard-names/{version}/src/cf-standard-name-table.xml"

    def __init__(self, version: int):
        self.__cf_version = version
        self.names = self._retrieve_data(version)

    def _retrieve_data(self, version: int) -> ET.Element:
        if not isinstance(version, int):
            raise TypeError("version must be an integer")

        request_url = self._get_xml_url_for_version(version)
        response = requests.get(request_url)

        if response.status_code == 404:
            raise KeyError(f"Version {version} not found")

        cf_xml = ET.fromstring(response.content)
        
        return cf_xml

    def _get_xml_url_for_version(self, version: int) -> str:
        return self.XML_URL.format(version=version)

    def is_standard_name(self, name: str) -> bool:
        try:
            name_xml = self._get_standard_name(name)
            return True
        
        except KeyError:
            return False

    def get_description(self, name: str) -> Optional[str]:
        try:
            name_xml = self._get_standard_name(name)
        except KeyError:
            raise KeyError(f"Could not retrieve standard_name: {name}")
        
        description = name_xml.find("./description").text
        
        return description
    
    def get_units(self, name: str) -> str:
        try:
            name_xml = self._get_standard_name(name)
        except KeyError:
            raise KeyError(f"Could not retrieve standard_name: {name}")

        units = name.find("./canonical_units").text
        
        return units

    def get_version(self) -> int:
        return self.__cf_version

    def _get_standard_name(self, name: str, allow_alias: bool=True) -> ET.Element:
        standard_name = None
        try:
            standard_name = self.__get_standard_name(name)
        
        except KeyError:
            if allow_alias:
                try:
                    standard_name = self.__get_standard_name_by_alias(name)
                except:
                    pass
        
        if standard_name is None:
            raise KeyError("No entry by that name")

        return standard_name
            
    def __get_standard_name(self, name: str) -> Optional[ET.Element]:
        element = self.names.find(f"entry[@id='{name.lower()}']")
        
        if element == -1:
            raise KeyError("No entry by that name")
        
        return element

    def __get_standard_name_by_alias(self, name: str) -> Optional[ET.Element]:
        alias = self.names.find(f"alias[@id='{name.lower()}']")
        
        if alias == -1:
            raise KeyError("No alias by that name")
        
        standard_name = alias.find("entry_id").text
        element = self._get_standard_name(standard_name)
        
        return element
