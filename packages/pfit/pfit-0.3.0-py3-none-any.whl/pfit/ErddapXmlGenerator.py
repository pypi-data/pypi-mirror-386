import xml.etree.ElementTree as ElementTree
from netCDF4 import Dataset
from typing import Any
from uuid import uuid1
from xml.dom import minidom
from pathlib import Path
import re
import warnings


def add_nested_elements(top_element:str, element_type:str, add_attributes:"list[tuple[Any, dict]]") -> ElementTree.Element:
    _add_attributes = ElementTree.Element(top_element)
    
    for tup in add_attributes:
        _attr = ElementTree.SubElement(_add_attributes, element_type)
        _attr.text = str(tup[0])
        
        for key in tup[1].keys():
            _attr.set(str(key), str(tup[1][key]))
    
    return _add_attributes


class ErddapXmlGenerator:

    ERDDAP_BOOL = {True:'true', False:'false'}
    ERDDAP_DTYPE = {'float32': 'float',
                    'float64': 'float',
                    'S1': 'String',
                    '|S1': 'String',
                    'str': "String",
                    str : "String",
                    "<class 'str'>":"String",
                    'uint64': 'int'}

    def __init__(self, datasetType="EDDTableFromNcCFFiles", datasetID=None, active=True):
        if not datasetID:
            datasetID = str(uuid1())
        
        self.xml = ElementTree.ElementTree(self.dataset(datasetType, datasetID, active))
        

    @classmethod
    def from_nc(cls,
                nc_file: str,
                datasetType="EDDTableFromNcCFFiles",
                datasetID=None, active=True,
                header_mods:"dict[str,str]"={},
                omit_variables:"list[str]"=[],
                copy_globals:"list[str]"=["cdm_altitude_proxy", "sourceUrl", "cdm_data_type", "featureType","subsetVariables","infoUrl"]):
        """_summary_

        Parameters
        ----------
        nc_file : str
            _description_
        datasetType : str, optional
            _description_, by default "EDDTableFromNcCFFiles"
        datasetID : _type_, optional
            _description_, by default None
        active : bool, optional
            _description_, by default True
        header_mods : dict[str,str], optional
            _description_, by default {}
        copy_globals : list[str], optional
            global attributes in the netcdf file to copy to the addAttributes, by default []

        Returns
        -------
        _type_
            _description_
        """
        
        with Dataset(nc_file) as rootgrp:
            has_id = hasattr(rootgrp, 'id')
            
            if datasetID:
                if has_id and id != datasetID:
                    warnings.warn(f"parameter datasetID ({datasetID}) differs from dataset id attribute ({id})")
            
            elif has_id:
                datasetID = rootgrp.getncattr('id')

            else:
                new_id = str(uuid1())
                warnings.warn(f"Missing id attribute. Auto-generating {str(uuid1())}")
                datasetID = new_id

        this = cls(datasetType, datasetID, active)
        
        this.writeHeaderDict(this.xml.getroot(), this.erddapHeaderDict(fileNameRegex=Path(nc_file).name))

        # modify header
        this.modify_xml(header_mods)

        # Write addAttributes for globals
        add_attrs = this.globals_from_nc(nc_file, copy_globals)
        this.xml.getroot().append(add_attrs)

        # Get data variable xml
        dv = this.dataset_variables_from_nc(nc_file)

        for e in dv:
            if e.find("sourceName").text in omit_variables:
                continue
            this.xml.getroot().append(e)

        return this

    @staticmethod
    def dataset_variables_from_nc(nc_file:str) -> "list[ElementTree.Element]":
        dv = list()
        with Dataset(nc_file, 'r') as rootgrp:
            for var in rootgrp.variables:
                dat_var = ErddapXmlGenerator.dataVariable(source_name=var,
                                                destination_name=var,
                                                data_type=ErddapXmlGenerator.get_dtype(str(rootgrp[var].dtype)))
                dv.append(dat_var)
        
        return dv

    def modify_xml(self, mods:"dict[str,str]"={}):
        for key, value in mods.items():
            
            if isinstance(value, bool):
                value = self.ERDDAP_BOOL[value]

            e = self.xml.getroot().find(key)
            
            if e.text:
                e.text = value  
    
    @staticmethod
    def globals_from_nc(nc_file:str, attrs:"list[str]") -> "ElementTree.Element":
        
        dv = list()
        with Dataset(nc_file, 'r') as rootgrp:
            for attr in rootgrp.ncattrs():
                if attr in attrs:
                    dv.append((attr, rootgrp.getncattr(attr)))
        
        return ErddapXmlGenerator.addAttributes(dv)


    @classmethod
    def from_csv(cls, csv: str):
        this = cls()
        return this
    
    def __add_essentials(self):
        root = self.xml.getroot()
        
        if not root.findall("att[@name='sourceUrl']"):
            if not root.find("addAttributes"):
                root.append(ElementTree.Element("addAttributes"))

            add_attributes = root.find("addAttributes")
            
            source_url = ElementTree.Element("att")
            source_url.set("name", "sourceUrl")
            source_url.text = "(local files)"
            add_attributes.append(source_url)

    def write_xml(self, file: str):
        self.__add_essentials()
        rough_string = ElementTree.tostring(self.xml.getroot()) 
        reparsed = minidom.parseString(rough_string)
        cleaned = reparsed.toprettyxml(indent="  ")
        no_header = re.sub(r"<\?xml .*\?>\n", "", cleaned)
        
        with open(file, 'wb') as f:
            f.write(no_header.encode('utf-8'))
                
    @staticmethod
    def get_dtype(dtype:str):
        return ErddapXmlGenerator.ERDDAP_DTYPE[dtype]

    @staticmethod
    def dataset(datasetType:str, datasetID:str, active:bool=True) -> ElementTree.Element:
        _dataset = ElementTree.Element("dataset")
        _dataset.set("type", datasetType)
        _dataset.set("datasetID", datasetID)
        _dataset.set("active", ErddapXmlGenerator.ERDDAP_BOOL[active])
        
        return _dataset

    @staticmethod
    def addAttributes(attrs:"list[tuple[str,str]]") -> ElementTree.Element:
        """Create XML addAttributes element with <att> children

        Parameters
        ----------
        attrs : list[tuple[str,str]]
            list of (key, value) e.g. [("sourceUrl", "www.myurl.com")]

        Returns
        -------
        ElementTree.Element
            _description_
        """
        a = [(text, {'name': attr}) for attr, text in attrs]
        e = add_nested_elements("addAttributes", "att", a)
        return e

    @staticmethod
    def dataVariable(source_name:str, destination_name:str, data_type:str, add_attributes:"list[tuple[Any, dict]]"=None) -> ElementTree.Element:
        e = ElementTree.Element("dataVariable")
        
        if source_name:
            _source_name = ElementTree.SubElement(e, "sourceName")
            _source_name.text = source_name
        
        if destination_name:
            _destination_name = ElementTree.SubElement(e, "destinationName")
            _destination_name.text = destination_name
        
        if data_type:
            _data_type = ElementTree.SubElement(e, "dataType")
            _data_type.text = data_type
        
        if add_attributes:
            e.append(ErddapXmlGenerator.addAttributes(add_attributes))
        
        return e
    
    @staticmethod
    def writeHeaderDict(element:ElementTree.Element, header_dict:dict) -> None:
        for key in header_dict:
            line = ElementTree.Element(key)
            value = header_dict[key] if header_dict[key] else ""
            line.text = str(value)
            
            element.append(line)
        
    @staticmethod
    def erddapHeaderDict(reloadEveryNMinutes=10080, updateEveryNMillis=10000,
                    fileDir="/", fileNameRegex=".*", recursive=False, pathRegex=".*", 
                    metadataFrom='last', standardizeWhat=0, sortFilesBySourceNames="",
                    fileTableInMemory=False, accessibleViaFiles=False) -> "dict[str,str]":
    
        _header = {"reloadEveryNMinutes": str(reloadEveryNMinutes), 
                  "updateEveryNMillis": str(updateEveryNMillis),
                  "fileDir": str(fileDir), 
                  "fileNameRegex": str(fileNameRegex), 
                  "recursive": ErddapXmlGenerator.ERDDAP_BOOL[recursive], 
                  "pathRegex": str(pathRegex), 
                  "metadataFrom": str(metadataFrom),
                  "standardizeWhat": str(standardizeWhat), 
                  "sortFilesBySourceNames": sortFilesBySourceNames,
                  "fileTableInMemory": ErddapXmlGenerator.ERDDAP_BOOL[fileTableInMemory],
                  "accessibleViaFiles": ErddapXmlGenerator.ERDDAP_BOOL[accessibleViaFiles]
                  }
        
        return _header

dataVariableDefaults = {
    ""
}


if __name__ == "__main__":
    E = ErddapXmlGenerator.from_nc(r"C:\Users\Nick\ESJ2.nc-pink_west_merged_clean1.nc", header_mods={"fileDir":"/cats/"})
    E.write_xml("C:/Users/Nick/xml2.xml")