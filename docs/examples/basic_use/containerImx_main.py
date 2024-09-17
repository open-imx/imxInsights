from imxInsights import ImxContainer

imx = ImxContainer(r"path to xml zip container or folder")

# print imx version and hash
print(imx.files.signaling_design.imx_version)
print(imx.files.signaling_design.file_hash)

print(imx.files.observations.imx_version)
print(imx.files.observations.file_hash)

# print build exceptions
for puic, exceptions in imx.get_build_exceptions():
    print(puic, [exception.msg for exception in exceptions])

# get all
all_objects = imx.get_all()

# get from situation
imx_object = imx.find("puic_uuid4")

# get all types
object_types = imx.get_types()

# get by type
object_subset = imx.get_by_types([object_types[0], imx_object.tag])
