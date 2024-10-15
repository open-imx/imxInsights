from imxInsights import ImxContainer

imx = ImxContainer(r"path to xml zip container or folder")

# get a feature collection by giving it a path
feature_collection = imx.get_geojson(["Signal"])

# do not convert coordinates to WGS84 but keep them as RD + NAP and add extension object properties
feature_collection_rd = imx.get_geojson(["SingleSwitch"], to_wgs=False, extension_properties=True)

# get a string representation of the geojson
geojson_str = feature_collection_rd.geojson_str()

# write to file
feature_collection.to_geojson_file("Signals.geojson")
