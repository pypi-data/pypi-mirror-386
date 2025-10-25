import netCDF4 as nc
import pandas as pd
from pfit.ntgs_metdata import ACDD_globals, ACDD_variable_attributes, ntgs_global_default
from pfit.variables_templates import add_variable
from numpy import diff, atleast_1d
from scipy.stats import mode

#    GCW / WMO recommends including only one borehole per dataset (erddap/opendap)
#    but this means that if you have a larger dataset that comprises many boreholes, 
#    each will be required to have its own title & ID, whereas you might want the files to be 
#    grouped into their own title, and especially if "ID" is used to be the DOI, you want one for
#    the larger datset.
#
#    Ground temperature stations are much less costly and easier to set up than ocean mooring cables,
#    so it is more likely that a dataset submission will have many more of them.
#     
#    Including multiple stations in a file would require having indices for depth and time, because
#    not all stations will have the same depths (or number of sensors), and they may not
#    record at the same time (and may not have the same number of recordings).
#
#    One solution is to not expect that individual sites have *all* of the ACDD information since
#    we are not using them to represent 'full' datasets. This keeps them useful as a way to store and
#    transmit data. If we want to combine them into 'full' datasets with IDs then that is possible with
#    some further work.


def make_temperature_base(file, ndepth, ntime=None, strings_as_strings=False):
    """ Create a NetCDF file with the standard structure for ground temperature profiles (CF DSG Time Series of Profiles)."""

    with nc.Dataset(file, 'w', format='NETCDF4') as rootgrp: 

        # Create dimensions
        ntime = None if ntime is None else int(ntime)

        _  = rootgrp.createDimension('depth_below_ground_surface', ndepth)
        _  = rootgrp.createDimension('time', ntime)

        if not strings_as_strings:
            _  = rootgrp.createDimension('nchar256', 256)

        # Create coordinate variables
        Lat = rootgrp.createVariable('latitude', 'f4', )
        Lat.standard_name = "latitude"
        Lat.long_name = "latitude"
        Lat.units = "degrees_north"
        Lat.axis  = "Y"
        Lat.ioos_category = "Location"

        Lon = rootgrp.createVariable('longitude', 'f4', )
        Lon.standard_name = "longitude"
        Lon.long_name = "longitude"
        Lon.units = "degrees_east"
        Lon.axis  = "X"
        Lon.ioos_category = "Location"

        Elev = rootgrp.createVariable('surface_elevation', 'f4')
        # Elev.standard_name = "height_above_reference_ellipsoid"
        Elev.long_name = "ground surface elevation"
        Elev.units = "m"
        Elev.ioos_category = "Location"

        Z = rootgrp.createVariable('depth_below_ground_surface', 'f4', ('depth_below_ground_surface',))
        Z.standard_name = "depth"
        Z.standard_name_url = "https://mmisw.org/ont/cf/parameter/depth"
        Z.long_name = "depth"
        Z.units = "m"
        Z.axis  = "Z"
        Z.positive = "down"
        Z.ioos_category = "Location"

        Time = rootgrp.createVariable('time', 'u8', ('time',))
        Time.standard_name = "time"
        Time.cf_role = 'profile_id'
        Time.units = "seconds since 1900-01-01"
        Time.calendar = "gregorian"
        Time.axis  = "T"
        Time.ioos_category = "Time"

        if strings_as_strings:  
            Profile = rootgrp.createVariable("site_name", str)
        else:
            Profile = rootgrp.createVariable('site_name', 'S1', ('nchar256',))
        Profile.standard_name = "platform_name"
        Profile._Encoding = "UTF-8"
        Profile.long_name = "borehole name"
        Profile.cf_role  = "timeseries_id"
        Profile.ioos_category = "Identifier"    

        T = rootgrp.createVariable('ground_temperature', 'f4', ('time', 'depth_below_ground_surface'))
        T.standard_name = "temperature_in_ground"
        T.standard_name_url = "https://mmisw.org/ont/cf/parameter/temperature_in_ground"
        T.units = "degree_C"
        T.coordinates = "site_name depth_below_ground_surface latitude longitude"
        T.long_name = "ground temperature"
        T.platform = "site_name"
        T.ioos_category = "Temperature"

        rootgrp.cdm_altitude_proxy = "depth_below_ground_surface"
        
        for key, value in standard_atts.items():
            rootgrp.setncattr(key, value)

    return file

standard_atts = {
    'featureType': 'timeSeriesProfile',
    'Conventions': "COARDS, CF-1.12, ACDD-1.3",
    'cdm_profile_variables': "time",
    'cdm_timeseries_variables': "latitude,longitude,elevation,site_name",
    "standard_name_vocabulary": "CF Standard Name Table v78"
    ""
}


def make_multi_temperature_base(file, ndepth):

    with nc.Dataset(file, 'w', format='NETCDF4') as rootgrp: 

        # Create dimensions
        _  = rootgrp.createDimension('station', 1)
        _  = rootgrp.createDimension('z', ndepth)
        _  = rootgrp.createDimension('time', None)
        _  = rootgrp.createDimension('nchar256', 256)

        # Create coordinate variables
        Lat = rootgrp.createVariable('latitude', 'f4', ('station',))
        Lat.standard_name = "latitude"
        Lat.long_name = "latitude"
        Lat.units = "degrees_north"
        Lat.axis  = "Y"
        Lat.ioos_category = "Location"

        Lon = rootgrp.createVariable('longitude', 'f4', ('station',))
        Lon.standard_name = "longitude"
        Lon.long_name = "longitude"
        Lon.units = "degrees_east"
        Lon.axis  = "X"
        Lon.ioos_category = "Location"

        Elev = rootgrp.createVariable('surface_elevation', 'f4', ('station',))
        Elev.standard_name = "height_above_reference_ellipsoid"
        Elev.units = "m"
        Elev.ioos_category = "Location"

        Time = rootgrp.createVariable('time', 'u8', ('time',))
        Time.standard_name = "time"
        Time.cf_role = 'profile_id'
        Time.units = "minutes since 1970-01-01"
        Time.calendar = "gregorian"
        Time.axis  = "T"
        Time.ioos_category = "Time"

        Profile = rootgrp.createVariable('site_name', 'S1', ('station', 'nchar256'))
        Profile.standard_name = "platform_name"
        Profile._Encoding = "UTF-8"
        Profile.long_name = "Borehole or site name"
        Profile.cf_role  = "timeseries_id"
        Profile.ioos_category = "Identifier"    

        T = rootgrp.createVariable('ground_temperature', 'f4', ('station', 'time', 'z'))
        T.standard_name = "temperature_in_ground"
        T.standard_name_url = "https://mmisw.org/ont/cf/parameter/temperature_in_ground"
        T.units = "degree_C"
        T.coordinates = "site_name depth latitude longitude"
        T.long_name = "Ground temperature"
        T.platform = "site_name"
        T.ioos_category = "Temperature"

        rootgrp.featureType = 'timeSeriesProfile' 
        rootgrp.cdm_altitude_proxy = "depth_below_ground_surface"
        
    return file


def add_global_vars(rootgrp, att_dict):
    for key in att_dict:
        rootgrp.setncattr(key, att_dict[key])

def add_variables(rootgrp, var_dict):
    for key in var_dict:
        var = var_dict[key]
        new_variable = rootgrp.createVariable(key, var['type'], var['dimensions'])
        for attr, value in var['attributes'].items():
            new_variable.setncattr(attr, value)

def write_variables(rootgrp, dataframe, var_dict):
    for key in var_dict:
        
        if rootgrp[key]._isvlen:
            for i in range(dataframe[key]):
                rootgrp[key][i] = dataframe[key][i]
        
        else:
            rootgrp[key][:] = dataframe[key]

def calculate_extent_metadata(rootgrp):
    """ calculate extents from data. Data variables must be populated"""
    lat = atleast_1d(rootgrp['latitude'][:])
    lon = atleast_1d(rootgrp['longitude'][:])
    depth = atleast_1d(rootgrp['depth_below_ground_surface'][:])
    elevation = atleast_1d(rootgrp['surface_elevation'][:])
    time = atleast_1d(rootgrp['time'][:])
    t_units = rootgrp['time'].units
    
    if len(time) > 0:
        min_date = nc.num2date(min(time), t_units)
        max_date = nc.num2date(max(time), t_units)

        rootgrp.time_coverage_start = min_date.isoformat()
        rootgrp.time_coverage_end = max_date.isoformat()
        
        if rootgrp['time'].shape:
            rootgrp.time_coverage_duration = pd.Timedelta(max_date - min_date).isoformat()
            frq_total_sec = [f.total_seconds() for f in diff(nc.num2date(time, t_units))]
            try:
                modal_frq = mode(frq_total_sec, nan_policy='omit').mode[0]
            except IndexError:
                modal_frq = mode(frq_total_sec, nan_policy='omit').mode
            except ValueError:
                modal_frq = None
            rootgrp.time_coverage_resolution = pd.Timedelta(seconds=modal_frq).isoformat()
    
    rootgrp.geospatial_bounds = f"POINT({lon[0]} {lat[0]})"

    if len(lat) > 0 and len(lon) > 0:
        rootgrp.geospatial_lat_min = min(lat)
        rootgrp.geospatial_lat_max = max(lat)
        rootgrp.geospatial_lon_min = min(lon)
        rootgrp.geospatial_lon_max = max(lon)

    if len(depth) > 0:
        rootgrp.observation_depth_min = min(abs(depth))
        rootgrp.observation_depth_max = max(abs(depth))

    if len(elevation) > 0:
        rootgrp.geospatial_vertical_min = min(elevation)
        rootgrp.geospatial_vertical_max = max(elevation)

def make_profile_base(file, strings_as_strings=False):

    with nc.Dataset(file, 'w', format='NETCDF4') as rootgrp: 

        # Create dimensions
        _ = rootgrp.createDimension('depth_below_ground_surface', None)
        _ = rootgrp.createDimension('nbnd', 2)
        
        if not strings_as_strings:
            _ = rootgrp.createDimension('nchar64', 64)

        # Create coordinate variables
        Lat = rootgrp.createVariable('latitude', 'f4', ())
        Lat.standard_name = "latitude"
        Lat.standard_name_url = "https://mmisw.org/ont/cf/parameter/latitude"
        Lat.long_name = "latitude"
        Lat.units = "degrees_north"
        Lat.axis  = "Y"
        Lat.ioos_category = "Location"

        Lon = rootgrp.createVariable('longitude', 'f4', ())
        Lon.standard_name = "longitude"
        Lon.standard_name_url = "https://mmisw.org/ont/cf/parameter/longitude"
        Lon.long_name = "longitude"
        Lon.units = "degrees_east"
        Lon.axis  = "X"
        Lon.ioos_category = "Location"
        
        if strings_as_strings:  
            Profile = rootgrp.createVariable('profile', str)
        else:
            Profile = rootgrp.createVariable('profile', 'S1', ('nchar64',))
        Profile.cf_role = 'profile_id'
        Profile._Encoding = "UTF-8"
        Profile.long_name = "Unique profile identifier"
        Profile.ioos_category = "Identifier"

        Elev = rootgrp.createVariable('surface_elevation', 'f4', ())
        Elev.long_name = "Ground surface elevation"
        Elev.standard_name = "height_above_reference_ellipsoid"
        Elev.units = "m"
        Elev.ioos_category = "Location"

        Time = rootgrp.createVariable('time', 'u8', ())
        Time.long_name = "Date of measurement"
        Time.standard_name_url = "https://mmisw.org/ont/cf/parameter/time"
        Time.standard_name = "time"
        Time.units = "seconds since 1900-01-01"
        Time.calendar = "standard"
        Time.axis  = "T"
        Time.ioos_category = "Time"

        if strings_as_strings:  
            Name = rootgrp.createVariable('platform_name', str)
        else:
            Name = rootgrp.createVariable('platform_name', 'S1', ('nchar64',))
        Name.standard_name = "platform_name"
        Name.long_name = "Borehole or site name"
        Name.ioos_category = "Identifier"
        Name._Encoding = "UTF-8"

        Z = rootgrp.createVariable('depth_below_ground_surface', 'f8', ('depth_below_ground_surface',))
        Z.standard_name = "depth"
        Z.standard_name_url = "https://mmisw.org/ont/cf/parameter/depth"
        Z.long_name = "Depth to midpoint of interval"
        Z.units = "m"
        Z.axis  = "Z"
        Z.positive = "down"
        Z.ioos_category = "Location"
        Z.bounds = "depth_bounds"

        Zbnd = rootgrp.createVariable('depth_bounds', 'f8', ('depth_below_ground_surface','nbnd'))
        Zbnd.long_name = "Depth below ground surface"
        Zbnd.ioos_category = "Location"

        Ztop = rootgrp.createVariable('top_of_interval', 'f8', ('depth_below_ground_surface',))
        Ztop.standard_name = "depth"
        Ztop.standard_name_url = "https://mmisw.org/ont/cf/parameter/depth"
        Ztop.long_name = "Depth to top of interval"
        Ztop.units = "m"
        Ztop.positive = "down"
        Ztop.ioos_category = "Location"

        Zbot = rootgrp.createVariable('bottom_of_interval', 'f8', ('depth_below_ground_surface',))
        Zbot.standard_name = "depth"
        Zbot.standard_name_url = "https://mmisw.org/ont/cf/parameter/depth"
        Zbot.long_name = "Depth to bottom of interval"
        Zbot.units = "m"
        Zbot.positive = "down"
        Zbot.ioos_category = "Location"

        rootgrp.featureType = 'profile'
        rootgrp.cdm_data_type = "profile"
        rootgrp.cdm_altitude_proxy = "depth_below_ground_surface"
        rootgrp.Conventions = "CF-1.12, ACDD-1.3"
        rootgrp.cdm_profile_variables = "platform_name,time,latitude,longitude,surface_elevation,profile"
        rootgrp.standard_name_vocabulary = "CF Standard Name Table v78"

        
    return file


def make_multi_profile_base(file):

    with nc.Dataset(file, 'w', format='NETCDF4') as rootgrp: 

        # Create dimensions
        _ = rootgrp.createDimension('z', None)
        _ = rootgrp.createDimension('station', None)
        _ = rootgrp.createDimension('nchar64', 64)
        _ = rootgrp.createDimension('nbnd', 2)

        # Create coordinate variables
        Lat = rootgrp.createVariable('latitude', 'f4', ('station',))
        Lat.standard_name = "latitude"
        Lat.standard_name_url = "https://mmisw.org/ont/cf/parameter/latitude"
        Lat.long_name = "latitude"
        Lat.units = "degrees_north"
        Lat.axis  = "Y"
        Lat.ioos_category = "Location"

        Lon = rootgrp.createVariable('longitude', 'f4', ('station',))
        Lon.standard_name = "longitude"
        Lon.standard_name_url = "https://mmisw.org/ont/cf/parameter/longitude"
        Lon.long_name = "longitude"
        Lon.units = "degrees_east"
        Lon.axis  = "X"
        Lon.ioos_category = "Location"
        
        Profile = rootgrp.createVariable('profile', 'S1', ('station','nchar64'))
        Profile.cf_role = 'profile_id'
        Profile._Encoding = "UTF-8"
        Profile.long_name = "Unique profile identifier"
        Profile.ioos_category = "Identifier"

        Elev = rootgrp.createVariable('surface_elevation', 'f4', ('station',))
        Elev.long_name = "Ground surface elevation"
        Elev.standard_name = "height_above_reference_ellipsoid"
        Elev.units = "m"
        Elev.ioos_category = "Location"

        Time = rootgrp.createVariable('time', 'u8', ('station',))
        Time.long_name = "Date of measurement"
        Time.standard_name_url = "https://mmisw.org/ont/cf/parameter/time"
        Time.standard_name = "time"
        Time.units = "seconds since 1900-01-01"
        Time.calendar = "standard"
        Time.axis  = "T"
        Time.ioos_category = "Time"

        Name = rootgrp.createVariable('platform_name', 'S1', ('station','nchar64'))
        Name.standard_name = "platform_name"
        Name.long_name = "Borehole or site name"
        Name.ioos_category = "Identifier"
        Name._Encoding = "UTF-8"

        Z = rootgrp.createVariable('depth_below_ground_surface', 'f4', ('station','z',))
        Z.standard_name = "depth"
        Z.standard_name_url = "https://mmisw.org/ont/cf/parameter/depth"
        Z.long_name = "Depth to midpoint of interval"
        Z.units = "m"
        Z.axis  = "Z"
        Z.positive = "down"
        Z.ioos_category = "Location"
        Z.bounds = "depth_bounds"

        Zbnd = rootgrp.createVariable('depth_bounds', 'f4', ('station','z','nbnd'))
        Zbnd.long_name = "Depth below ground surface"
        Zbnd.ioos_category = "Location"

        Ztop = rootgrp.createVariable('top_of_interval', 'f4', ('station','z',))
        Ztop.standard_name = "depth"
        Ztop.standard_name_url = "https://mmisw.org/ont/cf/parameter/depth"
        Ztop.long_name = "Depth to top of interval"
        Ztop.units = "m"
        Ztop.positive = "down"
        Ztop.ioos_category = "Location"

        Zbot = rootgrp.createVariable('bottom_of_interval', 'f4', ('station','z',))
        Zbot.standard_name = "depth"
        Zbot.standard_name_url = "https://mmisw.org/ont/cf/parameter/depth"
        Zbot.long_name = "Depth to bottom of interval"
        Zbot.units = "m"
        Zbot.positive = "down"
        Zbot.ioos_category = "Location"

        rootgrp.featureType = 'profile'
        rootgrp.cdm_data_type = "profile"
        rootgrp.cdm_altitude_proxy = "depth_below_ground_surface"
        rootgrp.Conventions = "CF-1.6, ACDD-1.3"
        rootgrp.cdm_profile_variables = "platform_name,time,latitude,longitude,surface_elevation"
        rootgrp.standard_name_vocabulary = "CF Standard Name Table v78"

        
    return file

if __name__ == "__main__":
    x  =make_profile_base(r"C:/tmp/ncprofile2.nc")
    