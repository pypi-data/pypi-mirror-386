import argparse
import netCDF4 as nc
import pandas as pd
import pathlib
import textwrap
from typing import Union

from pfit.CSVColMelter import CSVMelter
from pfit.pfnet_standard import make_multi_temperature_base, add_global_vars, calculate_extent_metadata, standard_atts

Filepath = Union[str, pathlib.Path]

class NtgsThermalDataset():
    """ Ground temperature data """
    def __init__(self, data_file, metadata, timezoneOffset = -7):
        self.data_file = data_file
        self.metadata = metadata
        self.timezoneOffset = timezoneOffset
        self.melted_data = self.read_NTGS(data_file)
    
    @classmethod
    def data_only(cls, data_file, timezoneOffset=-7):
        this = cls(data_file, timezoneOffset)
        return this

    @staticmethod
    def dirExists(path):
        if pathlib.Path(path).is_dir():
            return path
        else:
            raise argparse.ArgumentTypeError(f"The directory specified does not exist: {path}")

    def read_NTGS(self, ntgs_file):
        melter = CSVMelter(self.timezoneOffset)
        return melter.getMeltedDataframe(ntgs_file)

    def to_netcdf(self, nc_file:"Filepath"=None) -> str:
        """ Write dataset to a netcdf file """
        melted_df = self.melted_data 
        
        info = self.extract_info(melted_df)
        if nc_file is None:
            nc_file = pathlib.Path(self.data_file).with_suffix(".nc")
        else:
            nc_file = pathlib.Path(nc_file).with_suffix(".nc")

        rootgroup = self.make_ntgs_nc(nc_file,
                                     depths=info['depths'],
                                     times=info['times'],
                                     borehole=info['site_name'],
                                     data=info['data'],
                                     latitude=info['latitude'],
                                     longitude=info['longitude'])
        
        return str(nc_file)

    @staticmethod 
    def make_ntgs_nc(nc_target, depths, times, borehole, data, latitude: float, longitude: float) -> None:
        make_multi_temperature_base(nc_target, len(depths))
        
        with nc.Dataset(nc_target, 'a') as rootgrp:
        
            add_global_vars(rootgrp, standard_atts)
            rootgrp['latitude'][:] = latitude
            rootgrp['longitude'][:] = longitude
            rootgrp['depth'][:] = depths
            rootgrp['site_name'][:] = nc.stringtoarr(borehole, rootgrp['site_name'].shape[1])
            rootgrp['time'][:] = nc.date2num(times, rootgrp['time'].units)
            rootgrp['ground_temperature'][0, :, :] = data
            
            calculate_extent_metadata(rootgrp)
        
        return nc_target

    @staticmethod
    def extract_info(melted_df: pd.DataFrame) -> dict:
        """ Get data out of melted dataframe """
        info = dict()
        
        data = melted_df.pivot(index='time', columns='depth', values='temperature')
        data.replace(r"^\s*$", "nan", regex=True, inplace=True)  # TODO: make sure this is cleaned earlier

        info['data'] = data
        info['site_name'] = melted_df['site_id'][0]
        info['latitude'] = melted_df['latitude'][0]
        info['longitude'] = melted_df['longitude'][0]
        info['depths'] = data.columns.to_numpy()
        info['times'] = pd.to_datetime(data.index).to_pydatetime()
        info['n_depths'] = len(melted_df['depth'].unique())

        return info


# def nc_from_melted(nc_target, melted_file, metadata, metadata_id=None):
    
#     melted = pd.read_csv(melted_file)
#     data = melted.pivot(index='time', columns='depth', values='temperature')
    
#     if metadata_id is None:
#         metadata_id = melted["site_id"]

#     depths = data.columns.to_numpy()
#     times = pd.to_datetime(data.index)

#     borehole = melted['site_id'][0]
#     latitude = melted['latitude'][0]
#     longitude = melted['longitude'][0]
#     make_ntgs_nc(nc_target, depths, times, borehole, data,  latitude, longitude)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''
        Converts CSV, XLS, or XLSX files in the NTGS-style "wide" format to NetCDF files.
        The file being transformed must be free of errors prior to running this.
        '''))
    parser.add_argument('location', metavar='path', type=CSVMelter.pathExists, help='Path to input dataset file')
    parser.add_argument('output-path', metavar='output-path', type=NtgsThermalDataset.dirExists, help='Directory where the NetCDF file will be written to')
    parser.add_argument('--timezone-offset', metavar='timezone-offset', type=CSVMelter.timezone_check, help='Optional value indicating timezone offset from UTC-0 (default: UTC-7). To represent half hour, use "-3.5" for Newfoundland time as an example.')
    arguments = vars(parser.parse_args())
    dataset = None
    if arguments['timezone_offset'] is not None:
        dataset = NtgsThermalDataset(arguments['location'], None, arguments['timezone_offset'])
    else:
        dataset = NtgsThermalDataset(arguments['location'], None)
    dataset.to_netcdf(arguments['output-path'])
