# Specklia

Specklia is a cloud-hosted geospatial point cloud database designed for satellite altimetry data, produced by [Earthwave Ltd](https://earthwave.co.uk/). This package is the open-source Python Client for Specklia. It is intended for use by Academics within automated workflows and Jupyter Notebooks. Note that in order to use Specklia, you must first [generate an API key](https://specklia.earthwave.co.uk).

When using Earth Observation data, Academics are often presented with deeply nested folder structures containing headers that need to be manually parsed and files that contain large quantites of data not relevant to the current study. Specklia solves this problem by allowing users to request only the data within their desired study region, time period, and other filter criteria, and have it delivered right into their python workspace as a GeoDataFrame, without losing any of the headers and traceability information that standard product files provide.

Specklia was produced using funding from the [European Space Agency](https://www.esa.int/), and originally designed to host the [Cryo-TEMPO EOLIS Products](https://cryotempo-eolis.org/), which are derived from [CryoSat-2](https://www.esa.int/Applications/Observing_the_Earth/FutureEO/CryoSat) data. More information can be found at [Specklia's home page](https://specklia.earthwave.co.uk/).

If you're interested in influencing Specklia's development, using it in ways that are not
immediately enabled by the python client, or you have other support queries, please contact [support@earthwave.co.uk](mailto:support@earthwave.co.uk).
