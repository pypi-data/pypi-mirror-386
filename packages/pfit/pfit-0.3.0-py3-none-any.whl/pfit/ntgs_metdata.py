""" CF-style metdata key-value pairs
"""
ntgs_global_default = {
    "publisher_name": "Northwest Territories Geological Survey",
    "publisher_email": "NTGS@gov.nt.ca",
    "publisher_url": "https://www.nwtgeoscience.ca/",
    "publisher_type": "institution",
    "license": "The use of the published data will not carry restrictions. Full citation of referenced publications and reports by users is required.",
    "publisher_institution": "Northwest Territories Geological Survey",
}


"""
These map NTGS excel sheets into ACDD
# "ACDD attribute name" : ("NTGS Excel sheet", "Column Name")
"""

ACDD_globals = {
    "institution": ("Project Details", "Organization (mandatory)"),
    "creator_email": ("Project Details", "Email (mandatory)"),
    "geospatial_vertical_min": ("Location", "Site Elevation (m) (mandatory)"),
    "geospatial_vertical_max": ("Location", "Site Elevation (m) (mandatory)"),
    "geospatial_lat_min": ("Location", "Latitude (mandatory)"),
    "geospatial_lat_max": ("Location", "Latitude (mandatory)"),
    "geospatial_lon_min": ("Location", "Longitude (mandatory)"),
    "geospatial_lon_max": ("Location", "Longitude (mandatory)"),
    "project": ("Project Details", "Project Name")
}

ACDD_variable_attributes = {
    "ground_temperature": {
            "resolution": ("GTC Installation", "Sensor Resolution (˚C)"),
            "accuracy": ("GTC Installation", "Sensor Accuracy (˚C)")
          }

}

Permafrost_globals = {
    "ground_slope_angle": ("Site Conditions", "Slope Angle"),
    "ground_slope_direction": ("Site Conditions", "Slope Aspect"),
    "vegetation_type": ("Site Conditions", "Dominant Vegetation (mandatory)"),
    "organic_matter_thickness": ("Site Conditions", "Organic Layer"),
    "overburden_thickness": ("Site Conditions", "Overburden Thickness (m)"),
    "surface_cover": ("Site Conditions", "Surface Cover Material"),
    "surficial_geology": ("Site Conditions", "Surficial Geology (mandatory)"),
    "environment_description" : ("Site Conditions", "Site Conditions-Additional Comments")
}

IOOS_globals = {

}

v_names = {
    'temperature': 'ground_temperature',
    'elevation': 'elevation'
}

