import re
from pathlib import Path

import pandas as pd
from loguru import logger

from imxInsights.compare.changedImxObject import ChangedImxObject
from imxInsights.repo.imxMultiRepoProtocol import ImxMultiRepoProtocol
from imxInsights.utils.pandas_helpers import (
    df_columns_sort_start_end,
    styler_highlight_changes,
)
from imxInsights.utils.report_helpers import (
    clean_diff_df,
    shorten_sheet_name,
    upper_keys_with_index,
    write_df_to_sheet,
)
from imxInsights.utils.shapely.shapely_geojson import (
    CrsEnum,
    ShapelyGeoJsonFeatureCollection,
)


class ChangedImxObjects:
    def __init__(
        self,
        repo: ImxMultiRepoProtocol,
        container_id_1: str,
        container_id_2: str,
        object_paths: list[str] | None = None,
    ):
        self._repo = repo
        self.container_id_1 = container_id_1
        self.container_id_2 = container_id_2
        self.object_paths = object_paths
        self.compared_objects: list[ChangedImxObject] = self._get_compared_objects()

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

    def _nice_ref(self, property_dict: dict[str, str]) -> dict[str, str]:
        new_property_dict = {}
        for key, value in property_dict.items():
            if key[-3:] == "Ref" or key[-4:] == "Refs":
                new_property_dict[key] = "\n".join(value.split(" "))
                ref_display_value = self._replace_guids_with_names(value)
                new_property_dict[f"{key}|.display"] = "\n".join(
                    ref_display_value.split(" ")
                )
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
            object_paths: A list containing the object path to filter the changes.
            add_analyse: Add analyse to dataframe
            styled_df: Style changes in dataframe
            ref_display: Add refs display property to output

        Returns:
            A pandas DataFrame representing the changes for the specified object path.
        """
        items = [
            item
            for item in self.compared_objects
            if (item.t1 and item.t1.path in object_paths)
            or (item.t2 and item.t2.path in object_paths)
        ]

        out = [item.get_change_dict(add_analyse=add_analyse) for item in items]

        if ref_display:
            out = [self._nice_ref(item) for item in out]

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
                excluded_columns = df.filter(regex=r'(\.display|\|analyse)$').columns
                styler = df.style.map(styler_highlight_changes, subset=df.columns.difference(excluded_columns))
                styler.set_properties(**{
                    'border': '1px solid black',
                    'vertical-align': 'middle',
                })
                df = styler
                # todo: make every cell has a border en center it vertical
                # df = df.style.map(styler_highlight_changes)  # type: ignore[attr-defined]

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
            object_paths:: An optional list of object paths to filter the GeoJSON features. If None, all changed objects are included.
            to_wgs: A boolean indicating whether to convert the coordinates to WGS84.
            ref_display: Add refs display property to output

        Returns:
            A ShapelyGeoJsonFeatureCollection representing the changed objects.
        """
        if object_paths:
            features = []
            for item in self.compared_objects:
                if item.t1 and item.t1.path in object_paths:
                    features.append(item.as_geojson_feature(as_wgs=to_wgs))
                if item.t2 and item.t2.path in object_paths:
                    features.append(item.as_geojson_feature(as_wgs=to_wgs))

        else:
            features = [
                item.as_geojson_feature(as_wgs=to_wgs) for item in self.compared_objects
            ]

        if ref_display:
            for feature in features:
                feature.properties = self._nice_ref(feature.properties)

        return ShapelyGeoJsonFeatureCollection(
            features, crs=CrsEnum.WGS84 if to_wgs else CrsEnum.RD_NEW_NAP
        )

    def create_geojson_files(
        self, directory_path: str | Path, to_wgs: bool = True
    ) -> None:
        """
        Creates GeoJSON files for each unique object path in the compared objects.

        Args:
            directory_path: The path to the directory where the GeoJSON files will be created.
            to_wgs: A boolean indicating whether to convert the coordinates to WGS84.
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

    def to_excel(
        self, file_name: str | Path, add_analyse: bool = True, styled_df: bool = True
    ) -> None:
        """
        Exports the overview and detailed changes to an Excel file.

        Args:
            file_name: The name or path of the Excel file to create.
            add_analyse: Add analyse to excel
            styled_df: Style changes in excel
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

        with pd.ExcelWriter(file_name, engine="xlsxwriter") as writer:
            for key, df in diff_dict.items():
                if len(df.columns) == 0:
                    continue

                logger.debug(f"processing {key}")
                sheet_name = shorten_sheet_name(key)
                try:
                    write_df_to_sheet(writer, sheet_name, df)

                except Exception as e:
                    logger.error(f"Error writing sheet {sheet_name}: {e}")

        logger.success("creating change excel file finished")
