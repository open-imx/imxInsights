from collections import defaultdict
from typing import Callable
from shapely import MultiPoint, MultiLineString

from imxInsights.domain.imxObject import ImxObject


def add_specific_geometry(
    tree_dict: defaultdict[str, list[ImxObject]],
    find: Callable[[str], ImxObject | None],
):

    for key, imx_objects in tree_dict.items():
        for imx_object in imx_objects:
            if imx_object.tag == 'PpcTrack':
                if imx_object.imx_file.imx_version == "5.0.0":
                    imx_object.geometry = MultiPoint([
                        find(imx_object.properties['@demarcatorOneSideRef']).geometry,
                        find(imx_object.properties['@demarcatorOtherSideRef']).geometry
                    ])
                else:
                    raise NotImplemented

            elif imx_object.tag == 'TrackCircuit':
                if imx_object.imx_file.imx_version == "5.0.0":
                    imx_object.geometry = MultiPoint(
                        [find(item).geometry for item in imx_object.properties['InsulatedJointRefs'].split()]
                    )
                else:
                    raise NotImplemented

            elif imx_object.tag == 'AxleCounterSection':
                if imx_object.imx_file.imx_version == "5.0.0":
                    imx_object.geometry = MultiPoint(
                        [find(item).geometry for item in imx_object.properties['AxleCounterDetectionPointRefs'].split()]
                    )
                else:
                    raise NotImplemented

            elif imx_object.tag == 'StopConnection':
                if imx_object.imx_file.imx_version == "5.0.0":
                    imx_object.geometry = find(imx_object.properties['@signalRef']).geometry
                else:
                    raise NotImplemented

            elif imx_object.tag == 'SignalingRoute':
                pass
            elif imx_object.tag == 'Workzone':
                pass
            elif imx_object.tag == 'WorkzoneSystem':
                pass
            elif imx_object.tag == 'SignalAspect':
                pass
            elif imx_object.tag == 'Telegram':
                pass
            elif imx_object.tag == 'NationalValueSet':
                pass
            elif imx_object.tag == 'CombinationTrack':
                print()
                pass

            elif imx_object.tag == 'CbgDepartureTrack':
                if imx_object.imx_file.imx_version == "5.0.0":
                    imx_object.geometry = MultiLineString(
                        [item.geometry for item in imx_object.on_rail_geometry]
                    )
                else:
                    raise NotImplemented

            elif imx_object.tag == 'WorkzoneDepartureTrack':
                pass
            elif imx_object.tag == 'ErtmsArea':
                pass
            elif imx_object.tag == 'PositionReportParametersArea':
                pass
            elif imx_object.tag == 'RadioBlockCenterArea':
                pass

            # if imx_object.geographic_location is None:
            #     if imx_object.tag not in [
            #         "RailConnection", "PpcTrack", "TrackCircuit", "AxleCounterSection", "StopConnection",
            #         "SignalingRoute", "Workzone", "WorkzoneSystem", "SignalAspect", "Telegram", "NationalValueSet",
            #         "CombinationTrack", "CbgDepartureTrack", "WorkzoneDepartureTrack", "ErtmsArea",
            #         "PositionReportParametersArea", "RadioBlockCenterArea"
            #     ] :
            #         print()
            #     print()
