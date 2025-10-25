from abc import ABC, abstractmethod
from netCDF4 import Dataset


class MetadataHandler(ABC):

    @abstractmethod
    def write_attributes(nc_file: Dataset, loc:str) -> None:
        """ Write metadata to attributes in netcdf file for location """
        pass

    @abstractmethod
    def write_variables(nc_file: Dataset, loc:str) -> None:
        """ Write metadata to variables in netcdf file for location """
        pass

    def write_global_attribute(self, nc_file: Dataset, key, value, overwrite=False) -> None:
        with Dataset(nc_file) as dataset:
            if hasattr(dataset, key) and not overwrite:
                raise ValueError(f"Attribute {key} already exists for dataset {nc_file}")
            else:
                dataset.setncattr(key, value)


