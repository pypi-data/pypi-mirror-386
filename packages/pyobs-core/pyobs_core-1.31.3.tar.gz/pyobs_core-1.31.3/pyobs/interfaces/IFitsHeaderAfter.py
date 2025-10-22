from abc import ABCMeta, abstractmethod
from typing import List, Dict, Tuple, Any, Optional

from .interface import Interface


class IFitsHeaderAfter(Interface, metaclass=ABCMeta):
    """The module provides some additional header entries for FITS headers after some event (usually the end of the
    exposure)."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def get_fits_header_after(
        self, namespaces: Optional[List[str]] = None, **kwargs: Any
    ) -> Dict[str, Tuple[Any, str]]:
        """Returns FITS header for the current status of this module.

        Args:
            namespaces: If given, only return FITS headers for the given namespaces.

        Returns:
            Dictionary containing FITS headers.
        """
        ...


__all__ = ["IFitsHeaderAfter"]
