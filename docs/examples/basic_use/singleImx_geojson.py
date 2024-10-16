from imxInsights import ImxSingleFile

imx = ImxSingleFile(r"path to xml file")

# get a feature collection by giving it a path
feature_collection = imx.initial_situation.get_geojson(["Signal"])

# keep coordinates as RD + NAP and add extension object properties
feature_collection_rd = imx.initial_situation.get_geojson(
    object_path=["Signal"],
    to_wgs=False, extension_properties=True
)

# get a string representation of the geojson
geojson_str = feature_collection_rd.geojson_str()

# write to file
feature_collection.to_geojson_file(file_path="Signals.geojson")

# write all to file
imx.new_situation.create_geojson_files(directory_path="geojson")
