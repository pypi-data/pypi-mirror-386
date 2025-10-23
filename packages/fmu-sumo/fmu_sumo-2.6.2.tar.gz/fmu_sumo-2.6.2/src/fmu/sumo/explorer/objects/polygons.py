"""Module containing class for polygons object"""

from typing import Dict

from sumo.wrapper import SumoClient

from ._child import Child


class Polygons(Child):
    """Class representig a polygons object in Sumo"""

    def __init__(self, sumo: SumoClient, metadata: Dict, blob=None) -> None:
        """
        Args:
            sumo (SumoClient): connection to Sumo
            metadata (dict): polygon metadata
        """
        super().__init__(sumo, metadata, blob)

    def to_pandas(self):
        """Get polygons object as a DataFrame

        Returns:
            DataFrame: A DataFrame object
        """

        import pandas as pd

        try:
            if self.format == "csv":
                return pd.read_csv(self.blob)
            if self.format == "parquet":
                return pd.read_parquet(self.blob)
            raise TypeError()
        except TypeError as type_err:
            raise TypeError(f"Unknown format: {self.format}") from type_err

    async def to_pandas_async(self):
        """Get polygons object as a DataFrame

        Returns:
            DataFrame: A DataFrame object
        """

        import pandas as pd

        try:
            if self.format == "csv":
                return pd.read_csv(await self.blob_async)
            if self.format == "parquet":
                return pd.read_parquet(await self.blob_async)
            raise TypeError()
        except TypeError as type_err:
            raise TypeError(f"Unknown format: {self.format}") from type_err
