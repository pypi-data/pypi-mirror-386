import netCDF4 as nc
import functools
import re
from pprint import pprint

REQUIRED = ['summary', 'title', 'infoUrl', 'institution']

CONDITIONAL = {  # If A=B then C required
        ("cdm_data_type", "TimeSeriesProfile", "cdm_profile_variables"),
        ("cdm_data_type", "profile", "cdm_profile_variables")
}

BAD_MATCHES = [
    ("id", r"\s+", "Spaces in id field")
]

CODES = [
    (200, "Could not test"),
    (100, "Missing required attribute"),
    (101, "Problem with attribute value"),
    (102, "Required attribute is empty"),
    (0, "Passed"),
    (-1, "Not applicable"),
]


def is_error(check: "tuple[int, str]") -> bool:
    return 100 <= check[0] < 200


def is_warning(check: "tuple[int, str]") -> bool:
    return 200 <= check[0] < 300


def is_ok(check: "tuple[int, str]") -> bool:
    return 0 <= check[0] <100

def is_n_a(check: "tuple[int, str]") -> bool:
    return check[0] == -1


class Result:

    def __init__(self, checks: "list[tuple]"):
        self.checks = checks

    @property
    def errors(self) -> "list[str]":
        return [check[1] for check in self.checks if is_error(check)]

    @property
    def warnings(self) -> "list[str]":
        return [check[1] for check in self.checks if is_warning(check)]

    @property
    def passes(self) -> "list[str]":
        return [check[1] for check in self.checks if is_ok(check)]

    @property
    def skipped(self) -> "list[str]":
        return [check[1] for check in self.checks if is_n_a(check)]

    def summary(self):
        return((f"{len(self.checks)} checks performed:\n{len(self.errors)} Errors\n{len(self.warnings)} Warnings\n"
                f"{len(self.passes)} Passed checks\n{len(self.skipped)} Skipped checks"))

    def print_errors(self):
        pprint(self.errors)
    
    def print_warnings(self):
        pprint(self.warnings)


@functools.singledispatch
def check_erd_compatibility(ncdf: "nc.Dataset", silent=False) -> Result:
    """Check file compatibilty for ERDDAP

    Parameters
    ----------
    ncdf : nc.Dataset
        netCDF file to check

    Returns
    -------
    Result
        Result object
    """
    checks = []

    for attr in REQUIRED:
        checks.append(check_attribute(ncdf, attr))
    
    # has conditional metadata
    for (conditional, value, required) in CONDITIONAL:
        check = check_conditional_attribute(ncdf, conditional, value, required)
        checks.append(check) 
    
    # Problems with fields
    for (attr, expr, message) in BAD_MATCHES:
        checks.append(check_field_values(ncdf, attr, re.compile(expr), message))

    result = Result(checks)
    
    if not silent:
        print(result.summary())
    
    return result
    

@check_erd_compatibility.register
def _(ncdf: str, *args, **kwargs) -> Result:
    with nc.Dataset(ncdf) as filepath:
        return check_erd_compatibility(filepath, *args, **kwargs)


def check_attribute(ncdf: "nc.Dataset", attr_name: "str") -> "tuple[int, str]":
    if not hasattr(ncdf, attr_name):
        return (100, f"Missing attribute: {attr_name}")
    
    if getattr(ncdf, attr_name) in [None, ""]:
         return (102, f"Attribute {attr_name} must not be blank")
         
    else:
        return (0, "")


def check_field_values(ncdf, attr, pattern: "re.Pattern", message) -> "tuple[int, str]":
    if not hasattr(ncdf, attr):
        return (200, f"Could not test. Missing attribute {attr}")

    if pattern.search(getattr(ncdf, attr)):
        return (101, message)
    
    else:
        return (0, "")

def check_conditional_attribute(ncdf: "nc.Dataset", conditional_attr: "str", conditional_value: "str", required_attr: "str") -> "tuple[int, str]":
    
    if not hasattr(ncdf, conditional_attr):
        return (200, f"Missing attribute {conditional_attr}. Could not test {required_attr}.")

    check_value = getattr(ncdf, conditional_attr)

    if check_value != conditional_value:
        return (-1, "")

    if hasattr(ncdf, required_attr):
        return (0, "")
    
    else:
        return (100, f"Missing attribute {required_attr}. (Because {conditional_attr} == {conditional_value}")


def main():
    result = check_erd_compatibility(r"C:\Users\Nick\Downloads\noodle.nc")
    result.print_errors()


if __name__ == "__main__":
    main()




