import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd
import shapely
from deepdiff import DeepDiff
from loguru import logger
from pandas.io.formats.style import Styler

from imxInsights.compare.changedImxObject import ChangedImxObject
from imxInsights.compare.changes import Change, process_deep_diff
from imxInsights.compare.changeStatusEnum import ChangeStatusEnum
from imxInsights.repo.imxMultiRepoProtocol import ImxMultiRepoProtocol
from imxInsights.utils.flatten_unflatten import flatten_dict
from imxInsights.utils.headerAnnotator import HeaderSpec
from imxInsights.utils.pandas_helpers import (
    df_columns_sort_start_end,
    styler_highlight_change_status,
    styler_highlight_changes,
)
from imxInsights.utils.report_helpers import (
    add_overview_df_to_diff_dict,
    add_review_styles_to_excel,
    app_info_df,
    clean_diff_df,
    set_sheet_color_by_change_status,
    shorten_sheet_name,
    upper_keys_with_index,
    write_df_to_sheet,
)
from imxInsights.utils.shapely.shapely_geojson import (
    CrsEnum,
    ShapelyGeoJsonFeature,
    ShapelyGeoJsonFeatureCollection,
)


@dataclass
class CompareContainerInfo:
    file_name: str
    file_hash: str
    imx_version: str
    container_type: str


class ImxContainerCompare:
    def __init__(
        self,
        repo: ImxMultiRepoProtocol,
        container_id_1: str,
        container_id_2: str,
        object_paths: list[str] | None = None,
    ):
        """
        Initialize an IMX container comparison instance.

        This class retrieves objects from the given repository, compares their attributes across two container IDs.

        Args:
            repo: The repository containing the IMX objects to be compared.
            container_id_1: The first container ID for comparison.
            container_id_2: The second container ID for comparison.
            object_paths: A list of object paths to filter the comparison.
                If None, all objects within the containers will be compared.

        Attributes:
            container_id_1: The first container ID.
            container_id_2: The second container ID.
            object_paths: The object paths used to filter comparisons.
            compared_objects: A list of compared IMX objects.

        """
        self._repo = repo
        self.container_id_1 = container_id_1
        self.container_id_2 = container_id_2
        self._imx_info: dict[str, CompareContainerInfo] = {}
        self.object_paths = object_paths
        self.compared_objects: list[ChangedImxObject] = self._get_compared_objects()

    def _set_container_info(self, container_id, t):
        if container_id not in self._imx_info and t:
            self._imx_info[container_id] = CompareContainerInfo(
                t.imx_file.path.name,
                t.imx_file.file_hash,
                t.imx_file.imx_version,
                t.imx_situation or "container",
            )

    def _get_compared_objects(self) -> list[ChangedImxObject]:
        compared_objects = []

        repo_objects = (
            self._repo.get_by_paths(self.object_paths)
            if self.object_paths
            else self._repo.get_all()
        )

        for multi_object in repo_objects:
            t1 = multi_object.get_by_container_id(self.container_id_1)
            t2 = multi_object.get_by_container_id(self.container_id_2)

            self._set_container_info(self.container_id_1, t1)
            self._set_container_info(self.container_id_2, t2)

            if t1 or t2:
                compare = ChangedImxObject(t1=t1, t2=t2)
                if compare:
                    compared_objects.append(compare)

        return compared_objects

    def _replace_guids_with_names(self, input_string):
        def get_attr(t1, t2, attr="tag"):
            if t1 is None and t2 is None:
                return ""

            if t1 is None:
                return getattr(t2, attr, "")
            if t2 is None:
                return getattr(t1, attr, "")

            return getattr(t1, attr, "") if t1 == t2 else getattr(t2, attr, "")

        def replacer(match):
            guid = match.group(1)
            obj = replacements.get(guid)
            return f"{obj}" if obj else f"{guid}-not-present"  # {guid}|

        # Regex to match GUIDs (with optional ++ or -- prefixes)
        guid_pattern = r"(?:\+\+|--)?([0-9a-fA-F-]{36})"
        guids = re.findall(guid_pattern, input_string)

        replacements = {}
        for guid in guids:
            try:
                multi_object = self._repo.find(guid)
                t1 = multi_object.get_by_container_id(self.container_id_1)
                t2 = multi_object.get_by_container_id(self.container_id_2)

                tag = get_attr(t1, t2, "tag")
                name = get_attr(t1, t2, "name")
                if name == "":
                    name = "NoName"

                replacements[guid] = (
                    f"{tag}|{name}|t1:{'✔' if t1 else 'X'}|t2:{'✔' if t2 else 'X'}"
                )
            except ValueError:
                replacements[guid] = "NotPresent|Unknown|t1:X|t2:X"

        return re.sub(guid_pattern, replacer, input_string)

    def _nice_display(self, property_dict: dict[str, str]) -> dict[str, str]:
        new_property_dict = {}
        for key, value in property_dict.items():
            if key[-3:] == "Ref" or key[-4:] == "Refs":
                new_property_dict[key] = "\n".join(value.split(" "))
                ref_display_value = self._replace_guids_with_names(value)
                new_property_dict[f"{key}|.display"] = "\n".join(
                    ref_display_value.split(" ")
                )
            if key[-15:] == "gml:coordinates" and "->" in value:
                before, after = value.split(" -> ", 1)
                new_property_dict[key] = f"{before}\n->\n{after}"
            else:
                new_property_dict[key] = value
        return new_property_dict

    def get_pandas(
        self,
        object_paths: list[str],
        add_analyse: bool = True,
        styled_df: bool = True,
        ref_display: bool = True,
    ) -> pd.DataFrame:
        """
        Generates a DataFrame detailing the changes for a specific object path.

        Args:
            object_paths (list[str]): A list containing the object path to filter the changes.
            add_analyse (bool): Whether to add analysis to the DataFrame.
            styled_df (bool): Whether to apply styling to highlight changes.
            ref_display (bool): Whether to add reference display properties to the output.

        Returns:
            pd.DataFrame: A DataFrame representing the changes for the specified object path.
        """
        items = [
            item
            for item in self.compared_objects
            if (item.t1 and item.t1.path in object_paths)
            or (item.t2 and item.t2.path in object_paths)
        ]

        out = [item.get_change_dict(add_analyse=add_analyse) for item in items]

        if ref_display:
            out = [self._nice_display(item) for item in out]

        df = pd.DataFrame(out)
        if not df.empty:
            df = clean_diff_df(df)

            # TODO: remove path_to_root
            df = df_columns_sort_start_end(
                df,
                [
                    "@puic",
                    "path",
                    "tag",
                    "status",
                    "geometry_status",
                    "ImxArea",
                    "parent",
                    "children",
                    "@name",
                ],
                ["path_to_root"],
            )
            status_order = ["added", "changed", "type_change", "removed", "unchanged"]
            df["status"] = pd.Categorical(
                df["status"], categories=status_order, ordered=True
            )
            df = df.sort_values(by=["path", "status"])
            df["status"] = df["status"].astype("object")

            if styled_df:
                # TODO: return styler or dataframe, probly give type errors all over the place...
                df = self._style_diff_pandas(df)  # type: ignore[assignment]

        return df

    @staticmethod
    def _style_diff_pandas(df: pd.DataFrame) -> Styler:
        excluded_columns = df.filter(regex=r"(\.display|\|analyse)$").columns
        styler = df.style.map(  # type: ignore[attr-defined]
            styler_highlight_changes,  # type: ignore[arg-type]
            subset=df.columns.difference(excluded_columns),
        )
        styler = styler.map(  # type: ignore[attr-defined]
            styler_highlight_change_status,  # type: ignore[arg-type]
            subset=["status"],
        )

        styler.set_properties(
            border="1px solid black",
            vertical_align="middle",
        )
        return styler

    def get_geojson(
        self,
        object_paths: list[str] | None = None,
        to_wgs: bool = True,
        ref_display: bool = True,
    ) -> ShapelyGeoJsonFeatureCollection:
        """
        Generates a GeoJSON feature collection representing the changed objects.

        Args:
            object_paths (list[str] | None): Optional list of object paths to filter the GeoJSON features. If None, all changed objects are included.
            to_wgs (bool): Whether to convert the coordinates to WGS84.
            ref_display (bool): Whether to add reference display properties to the output.

        Returns:
            ShapelyGeoJsonFeatureCollection: A GeoJSON collection representing the changed objects.
        """
        if object_paths:
            features = []
            for item in self.compared_objects:
                if item.t2 and item.t2.path in object_paths:
                    features.append(item.as_geojson_feature(as_wgs=to_wgs))
                elif item.t1 and item.t1.path in object_paths:
                    features.append(item.as_geojson_feature(as_wgs=to_wgs))

        else:
            features = [
                item.as_geojson_feature(as_wgs=to_wgs) for item in self.compared_objects
            ]

        if ref_display:
            for feature in features:
                feature.properties = self._nice_display(feature.properties)

        return ShapelyGeoJsonFeatureCollection(
            features, crs=CrsEnum.WGS84 if to_wgs else CrsEnum.RD_NEW_NAP
        )

    def get_project_metadata_geojson(
        self, to_wgs: bool = True
    ) -> ShapelyGeoJsonFeatureCollection:
        areas: dict = {
            "UserArea": {"t1": {}, "t2": {}},
            "WorkArea": {"t1": {}, "t2": {}},
        }
        id_map = {self.container_id_1: "t1", self.container_id_2: "t2"}

        for container in self._repo.containers:
            version = id_map.get(container.container_id)
            if not version or not container.project_metadata:
                continue

            for feature in container.project_metadata.get_geojson(to_wgs).features:
                area = feature.properties.get("area")
                if area in areas and feature.geometry_list:
                    areas[area][version] = {
                        "props": feature.properties,
                        "geo": feature.geometry_list[0].wkt,
                    }

        features: list[ShapelyGeoJsonFeature] = []

        for area_name, versions in areas.items():
            dd = DeepDiff(
                versions["t1"],
                versions["t2"],
                ignore_order=True,
                verbose_level=2,
                cutoff_distance_for_pairs=1,
                cutoff_intersection_for_pairs=1,
                report_repetition=True,
            )
            changes = process_deep_diff(dd)

            # Add unchanged keys from t1
            for k, v in flatten_dict(versions["t1"]).items():
                changes.setdefault(
                    k,
                    Change(
                        ChangeStatusEnum.UNCHANGED,
                        t1=v,
                        t2=v,
                        diff_string=str(v),
                        analyse=None,
                    ),
                )

            changed = any(
                ch.status != ChangeStatusEnum.UNCHANGED for ch in changes.values()
            )
            geometry_changes = {
                k: ch for k, ch in changes.items() if k.startswith("geo")
            }
            geometry_changed = any(
                ch.status != ChangeStatusEnum.UNCHANGED
                for ch in geometry_changes.values()
            )
            geometry_1 = next(
                (ch.t1 for ch in geometry_changes.values() if ch.t1),
                versions["t1"].get("geo"),
            )
            geometry_2 = next(
                (ch.t2 for ch in geometry_changes.values() if ch.t2),
                versions["t2"].get("geo"),
            )

            props = {
                k.removeprefix("props."): ch.diff_string
                for k, ch in changes.items()
                if k != "geo"
            }
            props.update({"changed": changed, "geometry_changed": geometry_changed})

            for wkt in [geometry_1, geometry_2] if geometry_changed else [geometry_1]:
                if wkt:
                    try:
                        features.append(
                            ShapelyGeoJsonFeature([shapely.from_wkt(wkt)], props)
                        )
                    except Exception as e:
                        logger.warning(e)

        return ShapelyGeoJsonFeatureCollection(features)

    def create_geojson_files(
        self, directory_path: str | Path, to_wgs: bool = True
    ) -> None:
        """
        Creates GeoJSON files for each unique object path in the compared objects.

        Args:
            directory_path (str | Path): The directory where the GeoJSON files will be created.
            to_wgs (bool): Whether to convert the coordinates to WGS84.
        """
        logger.info("create geojson files")

        if isinstance(directory_path, str):
            directory_path = Path(directory_path)
        directory_path.mkdir(parents=True, exist_ok=True)

        paths = self._repo.get_all_paths()

        geojson_dict = {}
        for path in paths:
            geojson_dict[path] = self.get_geojson([path], to_wgs)

        geojson_dict = dict(sorted(geojson_dict.items()))
        geojson_dict = upper_keys_with_index(geojson_dict)

        for path, geojson_collection in geojson_dict.items():
            if len(geojson_collection.features) != 0:
                logger.info(f"create geojson file {path}")
                file_name = f"{directory_path}\\{path}.geojson"
                geojson_collection.to_geojson_file(file_name)

        feature_collection = self.get_project_metadata_geojson(to_wgs=to_wgs)
        file_name = f"{directory_path}\\ProjectMetadataAreas.geojson"
        feature_collection.to_geojson_file(file_name)

        logger.success("creating change excel file finished")

    @staticmethod
    def _get_imx_details(info, container_id, prefix):
        return {
            f"{prefix}_file_path": info[container_id].file_name,
            f"{prefix}_file_hash": info[container_id].file_hash,
            f"{prefix}_file_version": info[container_id].imx_version,
            f"{prefix}_file_situation": info[container_id].container_type,
        }

    def to_excel(
        self,
        file_name: str | Path,
        add_analyse: bool = True,
        add_review_styles: bool = True,
        header_spec: HeaderSpec | None = None,
    ) -> None:
        """
        Exports the overview and detailed changes to an Excel file. Adds header formatting in case a specification file is provided.

        Args:
            file_name: Required. The name or path of the Excel file to create.
            add_analyse: Whether to add analysis columns to the Excel output. Defaults to True.
            add_review_styles: Whether to add review formatting styles to the Excel workbook. Defaults to True.
            header_spec: HeaderSpec object containing header metadata.
        """

        file_name = Path(file_name) if isinstance(file_name, str) else file_name
        header_loader = header_spec.get_annotator() if header_spec else None

        logger.info("create change excel file")

        paths = self._repo.get_all_paths()
        diff_dict = {
            item: self.get_pandas([item], add_analyse=add_analyse, styled_df=False)
            for item in paths
        }
        diff_dict = dict(sorted(diff_dict.items()))
        diff_dict = upper_keys_with_index(diff_dict)
        diff_dict = add_overview_df_to_diff_dict(diff_dict)

        with pd.ExcelWriter(
            file_name,
            engine="xlsxwriter",
            engine_kwargs={"options": {"strings_to_numbers": True}},
        ) as writer:
            process_info = {
                "Diff Report": "",
                "Run Date": datetime.now().isoformat(),
                "": "",
                **self._get_imx_details(self._imx_info, self.container_id_1, "T1"),
                **self._get_imx_details(self._imx_info, self.container_id_2, "T2"),
            }
            inf_df = app_info_df(process_info)
            write_df_to_sheet(writer, "info", inf_df, header=False, auto_filter=False)

            for key, df in diff_dict.items():
                if df.empty or df.shape[1] == 0:
                    continue
                try:
                    sheet_name = shorten_sheet_name(key)
                    logger.debug(f"processing {key}")

                    if key == "meta-overview":
                        df = df.reset_index(drop=True)
                    elif header_loader:
                        # TODO: this will fuk up column order
                        df = header_loader.apply_metadata_header(df)

                    df = df.fillna("")

                    if key == "meta-overview":
                        work_sheet = write_df_to_sheet(writer, sheet_name, df)
                    elif not header_loader:
                        del df["path_to_root"]
                        styled_df = self._style_diff_pandas(df)
                        work_sheet = write_df_to_sheet(
                            writer, sheet_name, styled_df, grouped_columns=["G:H"]
                        )
                    else:
                        work_sheet = header_loader.to_excel_with_metadata(
                            writer,
                            sheet_name,
                            df,
                            styler_fn=self._style_diff_pandas,
                        )

                    if key != "meta-overview":
                        set_sheet_color_by_change_status(df, work_sheet)

                except Exception as e:
                    logger.exception(f"Error writing sheet '{sheet_name}': {e}")

        if add_review_styles:
            add_review_styles_to_excel(file_name)

        logger.success("creating change excel file finished")
