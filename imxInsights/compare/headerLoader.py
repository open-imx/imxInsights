import pandas as pd
from loguru import logger
import math

class HeaderLoader:
    """
    Class to handle the lookup of data for the header rows of a sheet
    """
    
    
    def __init__(self, headerfile, pathfield, ignore=tuple()):
        self.spec = pd.read_csv(
            headerfile,
            on_bad_lines="skip",
            encoding="utf-8",
        )
        for col in self.spec.columns:    
            if col + "_link" in self.spec.columns:
                self.spec[col] = '=HYPERLINK("'+self.spec[col + "_link"]+'", "'+self.spec[col]+'")'
                self.spec = self.spec.drop([col + "_link"], axis="columns")
        self.pathfield = pathfield
        self.ignore = ignore

    def _info_block_for_path(self, path):
        """
        Retrieves the specification information block for a given object path.

        Args:
            path (str): The object path for which to retrieve the specification information.

        Returns:
            pandas.DataFrame | None: A transposed DataFrame containing the specification
            values for the given path if exactly one match is found. Returns None if
            no match or multiple matches are found.
        """
        # Remove the Diff information
        if "->" in path:
            # This happens for paths that changed, for example InitialSituation->newsituation
            # We use the new situation
            path = path.partition("->")[2].strip()

        if path.startswith("++") or path.startswith("--"):
            path = path[2:].strip()

        if path.lower().startswith("imspoor"):
            path = ".".join(path.split(".")[1:])

        if path.startswith(".extension"):
            path = path[1:].partition(".")[-1]
            matching_rows = self.spec[
                self.spec[self.pathfield].str.endswith("." + path, na=False)
            ]
        else:
            matching_rows = self.spec[self.spec[self.pathfield] == path]

        # drop the path selecter, and remove any exact duplicates
        # The order is important here, as some paths might case double matches (specificly extentions) but if the information is exactly the same this does not matter
        matching_rows = matching_rows.drop(
            [self.pathfield] + list(self.ignore), axis="columns", errors="ignore"
        ).drop_duplicates()

        if matching_rows.empty:
            logger.error(f"No specification found for field with path {path}")
            return None
        elif len(matching_rows) > 1:
            logger.error(f"Specification not unique for field with path {path}")
            return None

        info = matching_rows.transpose()

        return info

    def add_header_to_sheet(self, df):
        """
        Adds a specification header block to the top of the given DataFrame for Excel export.

        The final DataFrame includes:
        - A header block containing specification information.
        - The original DataFrame rows.
        - Columns are reordered based on predefined logic.

        Args:
            df (pandas.DataFrame): The DataFrame to which the header information should be added.

        Returns:
            pandas.DataFrame: The modified DataFrame with specification header rows prepended.
        """
        klasse = df["path_to_root"].values[0]
        column_names = df.columns
        # Add missing collumns
        paths_from_spec = self.spec[self.spec[self.pathfield].str.startswith(klasse)]
        fields_from_spec = [path[len(klasse) + 1 :] for path in paths_from_spec]
        for field in fields_from_spec:
            if field not in column_names:
                df[field] = None

        # We keep track of the information for all collumns to concat later
        infoblocks = []
        # voeg de instructies en uitwisselscope toe obv het path
        for column in column_names:
            if (
                column
                in {
                    "path",
                    "tag",
                    "parent",
                    "children",
                    "status",
                    "geometry_status",
                    "path_to_root",
                }
                or "|" in column
            ):
                # These are added by the library and hence heve no info fields
                continue

            # columns might have numerical fields in them in case of list, e.g., Announcement.0.@announcementType.
            # For lookup purposes we want to ignore those
            ending = ".".join(
                part for part in column.split(".") if not part.isnumeric()
            )

            if column.startswith("extension."):
                # We do not have the full path for extentions, matching ending will have to do
                path = "." + ending
            else:
                # We should have the exact full path now
                path = f"{klasse}.{ending}"

            info = self._info_block_for_path(path)

            if info is not None:
                # Rename the collumn so it matches the actual column name
                numbername = info.columns[0]
                info[column] = info[numbername]
                info = info.drop([numbername], axis="columns")

                infoblocks.append(info)

        # Make dataframe for the top rows of the excel
        if infoblocks:
            fullinfo = pd.concat(infoblocks, axis="columns").dropna(how="all")
        else:
            # None of the fields had any info, can happen, particulary in diff between different IMX versions
            fullinfo = pd.DataFrame()

        # Reformat hyperlinks as an excel formula when present
        for i in range(1, 3):
            if f"ref_{i}" in fullinfo.index:
                refnames = fullinfo.loc[f"ref_{i}", :]
                refurls = fullinfo.loc[f"ref_{i}_link", :]
                fullinfo.loc[f"ref_{i}", :] = (
                    '=HYPERLINK("' + refurls + '", "' + refnames + '")'
                )
                fullinfo.drop([f"ref_{i}_link"], inplace=True)

        if "uitwisselscope_DO" in fullinfo.index:
            fullinfo.loc["uitwisselscope_DO"] = fullinfo.loc[
                "uitwisselscope_DO"
            ].replace({True: "In scope", False: "Buiten scope"})
        if "uitwisselscope_RVTO" in fullinfo.index:
            fullinfo.loc["uitwisselscope_RVTO"] = fullinfo.loc[
                "uitwisselscope_RVTO"
            ].replace({True: "In scope", False: "Buiten scope"})

        # Add the index as an actual collumn at the start
        labels = pd.DataFrame({"OTL": fullinfo.index})
        labels = labels.set_index(labels.OTL)
        fullinfo = pd.concat([labels, fullinfo], axis="columns")

        all_columns = set(fullinfo.columns.to_list()) | set(df.columns.to_list())

        # Ordering:
        # 1. OTL
        # 2. Added by imxInsights != |display
        # 3. all fields in order
        # 4. all extentions
        def col_key(colname):
            base_fields = [
                "@puic",
                "parent",
                "children",
                "@name",
                "path",
                "tag",
                "status",
                "geometry_status",
            ]
            if colname == "OTL":
                return (0, colname)
            if not colname.strip():
                return (5, 0)
            if colname in base_fields:
                return (1, base_fields.index(colname))
            if colname == "path_to_root":
                return (99, colname)
            is_extention_code = 3 if colname.startswith(".extension") else 2
            if "|" in colname:
                return (is_extention_code, colname.partition("|")[0], 1)
            else:
                return (is_extention_code, colname, 0)

        in_order = sorted(list(all_columns), key=col_key)

        # Hack together the order
        ordering_df = pd.DataFrame(columns=in_order)
        return pd.concat([ordering_df, fullinfo, df])
