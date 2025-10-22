from typing import Any
import pandas as pd
import logging

from .publisher import Publisher


log = logging.getLogger(__name__)


class CsvPublisher(Publisher):
    def __init__(self, filename: str, **kwargs: Any):
        """Initialize new CSV publisher.

        Args:
            filename: Name of file to log in.
        """
        Publisher.__init__(self, **kwargs)

        # store
        self._filename = filename

    async def __call__(self, **kwargs: Any) -> None:
        """Publish the given results.

        Args:
            **kwargs: Results to publish.
        """

        # load data
        csv = await self.data()

        # create new row from kwargs and append it
        row = pd.DataFrame(kwargs, index=[0])
        csv = pd.concat([csv, row], ignore_index=True)

        # write it
        await self.vfs.write_csv(self._filename, csv, index=False)

    async def data(self) -> pd.DataFrame:
        """Return data that has so far been published."""

        # load data
        try:
            # load it
            return await self.vfs.read_csv(self._filename, index_col=False)

        except FileNotFoundError:
            # file not found, so start new with row
            log.warning("No previous CSV file found, creating new one...")
            return pd.DataFrame()


__all__ = ["CsvPublisher"]
