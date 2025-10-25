import pandas as pd
import numpy as np
import re
import netCDF4 as nc
#from fuzzywuzzy import fuzz

from pfit.MetadataHandler import MetadataHandler
from pfit.ntgs_metdata import ACDD_globals, ACDD_variable_attributes, ntgs_global_default, v_names, Permafrost_globals

class NTGSTemperatureMetadataHandler(MetadataHandler):

    def __init__(self, xl_file):
        """ Reads and validates NTGS temperature metadata file """
        self.dir = {}
        self.file = xl_file
        self.readxl(xl_file)
        self._selected_site = None
    
    def __getitem__(self, item):
        return self.dir.get(item, "")

    @classmethod
    def from_xlsx(cls, xl_file):
        """ same as the default constructor for now"""
        C = cls(xl_file)
        return C

    def readxl(self, xl_file):
        self.read_tab(xl_file, "Location")
        self.read_tab(xl_file, "GTC Installation")
        self.read_tab(xl_file, "Ground Temperature Record")
        self.read_tab(xl_file, "Project Details")
        self.read_tab(xl_file, "Site Conditions")

    @property    
    def selected_site(self):
        if self._selected_site is None: 
            self.selected_site = 1
            print("No site selected. Selecting first record")    
        
        return self._selected_site
        
    @selected_site.setter
    def selected_site(self, value):
        """ Set the selected location
        site_id : int or str
            row number or site name 
            """
        if isinstance(value, int):
            self._selected_site = self["Project Details"].loc[value, "Site ID (mandatory)"]
        
        elif isinstance(value, str):
            if not value in self.get_sites():
                raise KeyError("Chosen site is not in the Project Details tab. Selection not possible")
            self._selected_site = value

    def get_sites(self, tab="Project Details"):
        if tab == "Project Details":
            return self["Project Details"]["Site ID (mandatory)"].values
        else:
            return self["Location"]["Site ID"].values

    def read_tab(self, xl_file, name):
        tab = pd.read_excel(xl_file, skiprows=[1], sheet_name=name, engine='openpyxl')
        self.dir[name] = tab.loc[~tab.iloc[:, 0].isna()]  # 0-index because name for Site ID changes by tab
        self._validate_tab(name)

    def read_disclaimer(self, xl_file):
        text = pd.read_excel(xl_file, sheet_name="Disclaimer-Copyright", engine='openpyxl').to_json()
        citation = re.search(r'Recommended citation:\s*(.*)"', text).group(1).replace(r"\n", "")
        terms = re.search('Terms of use(.*?)"', text).group(1).replace(r"\n", "")

    def _validate_tab(self, tab):
        validator = self._get_validator(tab)
        validator(self[tab])

    def _get_validator(self, tab):
        if tab == "Location":
            return self._validate_location_tab
        # elif tab == "GTC Installation":
        #     return self.validate_gtc_tab
        # elif tab == "Site Conditions":
        #     return self.validate_site_tab
        # elif tab == "Project Details":
        #     return self.validate_project_tab
        else:
            return self.null_validator

    def null_validator(self, tab):
        pass

    def _validate_location_tab(self, df):
        self._validate_location_headers(df)
        self.validate_latitude(df["Latitude (mandatory)"].to_numpy())

    def _validate_location_headers(self, df):
        for header in ["Site ID", "Latitude (mandatory)", "Longitude (mandatory)",
                        "Geodetic Datum", "Site Elevation (m) (mandatory)"]:
            if not header in df.columns:
                print(f"Warning, header {header} missing.")

    def match_name(self, tab, name):
        clean_name = name.strip().lower()
        metadata_sites = {s.strip().lower(): s for s in self.get_sites(tab)}
        
        if not clean_name in metadata_sites.keys():
            raise KeyError(f"Site name {name} not in {self.get_sites(tab)} on tab {tab}")
        else:
            return metadata_sites[clean_name]

    def get_value(self, tab, col, loc):
        site_name = self.match_name(tab, loc)
        return self[tab][col][np.where(self.get_sites(tab) == site_name)[0][0]]

    def get_ACDD_attr(self, attr, loc=None):
        return self.get_translated_attr(attr, ACDD_globals, loc=None)

    def get_translated_attr(self, attr, dictionary, loc=None):
        if loc is None:
            loc = self.selected_site

        tab, col = dictionary[attr]
        
        return self.get_value(tab, col, loc)
    @staticmethod
    def validate_latitude(lats):
        """[summary]

        Parameters
        ----------
        lats : array-like
            latitude values
        """
        assert(max(lats) >= -90)
        assert(min(lats) <= 90 )

    def write_attributes(self, nc_file, loc):
        with nc.Dataset(nc_file, 'a') as rootgrp:
            for att in ACDD_globals: 
                value = self.get_ACDD_attr(att, loc)
                rootgrp.setncattr(att, value)
            for att in Permafrost_globals:
                value = self.get_translated_attr(att, Permafrost_globals, loc)
                rootgrp.setncattr(att, value)
            for att, value in ntgs_global_default.items():
                rootgrp.setncattr(att, value)
    
    def write_variables(self, nc_file, loc):
        self._add_elevation(nc_file, loc)

    def _add_elevation(self, nc_file, loc):
        with nc.Dataset(nc_file, 'a') as rootgrp:
            rootgrp[v_names['elevation']][:] = self.get_value("Location","Site Elevation (m) (mandatory)", loc)



if __name__ == "__main__":
    
    xl_file = r"C:\Users\Nick\Downloads\NTGSref_2020April23\2019-007_2019-007\2019-007_Metadata\NWT_Open_Report_2019-007_metadata.xlsx"
    M = NTGSTemperatureMetadataHandler(xl_file)
    M.get_ACDD_attr('institution')