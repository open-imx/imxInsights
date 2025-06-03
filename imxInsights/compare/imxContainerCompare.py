import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd
from loguru import logger

from imxInsights.compare.changedImxObject import ChangedImxObject
from imxInsights.repo.imxMultiRepoProtocol import ImxMultiRepoProtocol
from imxInsights.utils.pandas_helpers import (
    df_columns_sort_start_end,
    styler_highlight_change_status,
    styler_highlight_changes,
)
from imxInsights.utils.report_helpers import (
    add_review_styles_to_excel,
    app_info_df,
    clean_diff_df,
    shorten_sheet_name,
    upper_keys_with_index,
    write_df_to_sheet,
)
from imxInsights.utils.shapely.shapely_geojson import (
    CrsEnum,
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

            df = df_columns_sort_start_end(
                df,
                [
                    "@puic",
                    "path",
                    "tag",
                    "parent",
                    "children",
                    "status",
                    "geometry_status",
                    "@name",
                ],
                [],
            )
            df = df.fillna("")

            status_order = ["added", "changed", "unchanged", "type_change", "removed"]
            df["status"] = pd.Categorical(
                df["status"], categories=status_order, ordered=True
            )
            df = df.sort_values(by=["path", "status"])

            if styled_df:
                excluded_columns = df.filter(regex=r"(\.display|\|analyse)$").columns
                styler = df.style.applymap(  # type: ignore[attr-defined]
                    styler_highlight_changes,
                    subset=df.columns.difference(excluded_columns),
                )
                styler = styler.applymap(  # type: ignore[attr-defined]
                    styler_highlight_change_status,
                    subset=["status"],
                )
                styler = styler.set_properties(
                    subset=df.columns.difference(excluded_columns),
                    **{
                        "border": "1px solid black",
                        "vertical-align": "middle",
                    },
                )
                df = styler

        return df

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
        styled_df: bool = True,
        add_review_styles: bool = True,
    ) -> None:
        """
        Exports the overview and detailed changes to an Excel file.

        Args:
            file_name: The name or path of the Excel file to create.
            add_analyse: Whether to add analysis to the Excel output.
            styled_df: Whether to apply styling to highlight changes.
            add_review_styles: Whether to add review styles to the workbook.
        """
        file_name = Path(file_name) if isinstance(file_name, str) else file_name

        paths = self._repo.get_all_paths()

        logger.info("create change excel file")

        diff_dict = {
            item: self.get_pandas([item], add_analyse=add_analyse, styled_df=styled_df)
            for item in paths
        }
        diff_dict = dict(sorted(diff_dict.items()))
        diff_dict = upper_keys_with_index(diff_dict)

        overview_df = pd.concat([styler.data for styler in diff_dict.values()], axis=0)
        columns_to_keep = [
            "@puic",
            "path",
            "tag",
            "parent",
            "@name",
            "status",
            "geometry_status",
            "Location.GeographicLocation.@accuracy",
            "Location.GeographicLocation.@dataAcquisitionMethod",
            "Metadata.@isInService",
            "Metadata.@lifeCycleStatus",
            "Metadata.@source",
        ]
        diff_dict = {"meta-overview": overview_df[columns_to_keep]} | diff_dict

        with pd.ExcelWriter(file_name, engine="xlsxwriter") as writer:
            process_data = {
                "Diff Report": "",
                "Run Date": datetime.now().isoformat(),
                "": "",
                **self._get_imx_details(self._imx_info, self.container_id_1, "T1"),
                **self._get_imx_details(self._imx_info, self.container_id_2, "T2"),
            }
            inf_df = app_info_df(process_data)
            write_df_to_sheet(writer, "info", inf_df, header=False, auto_filter=False)

            for key, df in diff_dict.items():
                if len(df.columns) == 0:
                    continue

                logger.debug(f"processing {key}")
                sheet_name = shorten_sheet_name(key)

                try:
                    work_sheet = write_df_to_sheet(writer, sheet_name, df)
                    status_column = (
                        df["status"]
                        if isinstance(df, pd.DataFrame)
                        else df.data["status"]
                    )

                    if status_column.eq("unchanged").all():
                        work_sheet.set_tab_color("gray")

                except Exception as e:
                    logger.error(f"Error writing sheet {sheet_name}: {e}")

        if add_review_styles:
            add_review_styles_to_excel(file_name)

        logger.success("creating change excel file finished")
