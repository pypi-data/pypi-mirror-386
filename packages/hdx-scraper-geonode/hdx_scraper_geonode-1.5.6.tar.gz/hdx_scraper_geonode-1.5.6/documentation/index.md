# Summary

The HDX Scraper Geonode Library enables easy building of scrapers for extracting data from
[GeoNode](https://geonode.org/) servers. GeoNode is a web-based application and platform for developing
geospatial information systems (GIS) and for deploying spatial data infrastructures (SDI).

# Information

This library is part of the [Humanitarian Data Exchange](https://data.humdata.org/) (HDX) project. If you have
humanitarian related data, please upload your datasets to HDX.

The code for the library is [here](https://github.com/OCHA-DAP/hdx-scraper-geonode).
The library has detailed API documentation which can be found in the menu on the left and starts
[here](https://hdx-scraper-geonode.readthedocs.io/en/latest/api-documentation).

## Breaking Changes

1.4.0 supports only Python 3.6 and later

# GeoNodeToHDX Class

You should create an object of the GeoNodeToHDX class:

    geonodetohdx = GeoNodeToHDX("https://geonode.wfp.org", downloader)
    geonodetohdx = GeoNodeToHDX("https://geonode.themimu.info", downloader)

It has high level methods generate_datasets_and_showcases and
delete_other_datasets:

    # generate datasets and showcases reading country and layer information from the GeoNode
    datasets = generate_datasets_and_showcases("maintainerid", "orgid", "orgname", updatefreq="Adhoc",
                                               subnational=True)
    # generate datasets and showcases reading layer information ignoring region (country) in layers call
    countrydata = {"iso3": "MMR", "name": "Myanmar", "layers": None}
    datasets = generate_datasets_and_showcases("maintainerid", "orgid", "orgname", updatefreq="Adhoc",
                                               subnational=True, countrydata=countrydata)
    # delete any datasets and associated showcases from HDX that are not in the list datasets
    # (assuming matching organisation id, maintainer id and geonode url in the resource url)
    delete_other_datasets(datasets)

If you need more fine-grained control, it has low level methods
get_locationsdata, get_layersdata, generate_dataset_and_showcase:

    # get countries where count > 0
    countries = geonodetohdx.get_countries(use_count=True)
    # get layers for country with ISO 3 code SDN
    layers = geonodetohdx.get_layers(countryiso="SDN")
    # get layers for all countries
    layers = get_layers(countryiso=None)

There are default terms to be ignored and mapped. These can be overridden by
creating a YAML configuration with the new configuration in this format:

    ignore_data:
      - deprecated

    category_mapping:
      Elevation: "elevation - topography - altitude"
      "Inland Waters": river

    titleabstract_mapping:
      bridges:
        - bridges
        - transportation
        - "facilities and infrastructure"
      idp:
        camp:
          - "displaced persons locations - camps - shelters"
          - "internally displaced persons - idp"
        else:
          - "internally displaced persons - idp"

ignore_data are any terms in the abstract that mean that the dataset
should not be added to HDX.

category_mapping are mappings from the category field category__gn_description
to HDX metadata tags.

titleabstract_mapping are mappings from terms in the title or abstract to
HDX metadata tags.

For more fine-grained tuning of these, you retrieve the dictionaries and
manipulate them directly:

    geonodetohdx = GeoNodeToHDX("https://geonode.wfp.org", downloader)
    ignore_data = geonodetohdx.get_ignore_data()
    category_mapping = geonodetohdx.get_category_mapping()
    titleabstract_mapping = geonodetohdx.get_titleabstract_mapping()
