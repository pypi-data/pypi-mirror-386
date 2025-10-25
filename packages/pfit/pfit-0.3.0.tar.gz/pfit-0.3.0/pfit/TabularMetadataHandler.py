from pfit.MetadataHandler import MetadataHandler
from netCDF4 import Dataset, chartostring
import pandas as pd
from numpy import atleast_1d
from typing import Type, Union
import re

class TabularMetadataHandler(MetadataHandler):
    """ 
    index_column : str or int
        index of the index column (starting from 1) or name of column with unique records
        corresponding to which file or site to write to
        
    column names mini-language: Use these patterns to write your metadata attributes
    "att_name" create global attribute with name "att_name"
    "!var:dest" create attribute "dest" for variable "var"
    "![@att='val']:dest" create attribute "dest" for all variables where attribute "att" has value "val"
    "!$var" write value to a single-value scalar variable "var"
    "!$[@att='val'] write value to single value scalar variable which has attribute "att" with value "val"
    """
    R_SIMPLE_VARIABLE = re.compile(r"^!(\w*):(\w*)$")
    R_SCALAR_VALUE = re.compile(r"^!\$(\w*)$")

    def __init__(self, table: pd.DataFrame, index_column: Union[int, str]):
        self.table=table
        self.index = index_column
        self.table = self.table.set_index(self.index)
        self.tabledict = self.table.to_dict("index")

    @classmethod
    def from_csv(cls):
        pass

    @classmethod
    def from_xlsx(cls, xl_file, sheet_index: int, index_column: Union[int, str], **kwargs):
        xl_data = pd.read_excel(xl_file, sheet_name=sheet_index, skiprows=[1], engine='openpyxl', **kwargs)
        this = cls(xl_data, index_column)
        return this

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value):
        if isinstance(value, int):
            value = self.table.columns[1 + value]
        
        self._index= value

    def write_variables(self, nc_file: Dataset, loc:str) -> None:
        pass

    def _lookup_loc(self, ncDataset: Dataset, lookup) -> str:
        locations = atleast_1d(ncDataset[lookup][:])
        
        if locations.dtype == "S1": 
            sites = chartostring(locations)

        elif hasattr(ncDataset[lookup], "_Encoding"):
            sites = locations

        else:
            raise TypeError(f"Variable {lookup} is not a string or cannot be read")

        if len(sites) != 1:
            raise ValueError("too many sites returned. Only works for a dataset with one site")

        return sites[0]

    def write_attributes(self, nc_file: str, loc:str=None, loc_lookup:str=None) -> None:
        """ 
        loc_name : str
            Identifier to match against index_column. ignored if loc_lookup is provided
        loc_lookup : str
            the name of a variable in nc_file that contains strings matching strings in 
            the defined index_column """
        if (not loc and not loc_lookup):
            raise ValueError("one of 'loc' or 'loc_lookup' must be provided")
        
        with Dataset(nc_file, 'a') as rootgrp:
            if loc_lookup:
                loc = self._lookup_loc(rootgrp, loc_lookup)

            for key in self.get_attributes(loc):
                value = self.get_attribute(loc, key) 
                
                if not self._is_special_attribute(key):
                    rootgrp.setncattr(key, value)
                
                elif self.R_SIMPLE_VARIABLE.match(key):
                    var, att = self._get_simple_variable_assignment(key)
                    rootgrp[var].setncattr(att, value)
                
                elif self.R_SCALAR_VALUE.match(key):
                    scalar_variable = self._get_scalar_value_assignment(key)
                    rootgrp[scalar_variable][:] = value

                else:
                    pass
    
    def _get_scalar_value_assignment(self, string:str) -> str:
        match = self.R_SCALAR_VALUE.match(string)

        if match:
            return match.group(1)
        else:
            return ""

    def _get_simple_variable_assignment(self, string: str) -> tuple:
        match = self.R_SIMPLE_VARIABLE.match(string)
        
        if match:
            assignment = (match.group(1), match.group(2))
            return assignment
        else:
            return (None, None)

    def _is_special_attribute(self, name: str) -> bool:
        special_chars = ["!", "$", "@"]
        is_special = any([x in name for x in special_chars])

        return is_special

    def get_attributes(self, loc: str) -> dict:
        return self.tabledict[loc]

    def get_attribute(self, loc: str, attribute: str) -> str:
        return self.tabledict[loc][attribute]

if __name__ == "__main__":
    t = TabularMetadataHandler.from_xlsx(r"C:/Users/Nick/Downloads/ESJ_Metadata.xlsx", 0, "platform_name")