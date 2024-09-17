from imxInsights import ImxSingleFile

imx = ImxSingleFile(r"path to xml file")

# print imx version and hash
print(imx.file.imx_version)
print(imx.file.file_hash)

# print build exceptions
for puic, exceptions in imx.situation.get_build_exceptions():
    print(puic, [exception.msg for exception in exceptions])

# get all
all_objects = imx.situation.get_all()

# get from situation
imx_object = imx.initial_situation.find("puic_uuid4")

# get all types
object_types = imx.new_situation.get_types()

# get by type
object_subset = imx.new_situation.get_by_types([object_types[0], imx_object.tag])
