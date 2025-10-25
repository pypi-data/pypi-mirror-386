from abc import ABCMeta, abstractmethod
from typing import Any

from .interface import Interface
from pyobs.utils.enums import ExposureStatus


class IExposure(Interface, metaclass=ABCMeta):
    """The module controls a camera."""

    __module__ = "pyobs.interfaces"

    @abstractmethod
    async def get_exposure_status(self, **kwargs: Any) -> ExposureStatus:
        """Returns the current status of the camera, which is one of 'idle', 'exposing', or 'readout'.

        Returns:
            Current status of camera.
        """
        ...

    @abstractmethod
    async def get_exposure_progress(self, **kwargs: Any) -> float:
        """Returns the progress of the current exposure in percent.

        Returns:
            Progress of the current exposure in percent.
        """
        ...


__all__ = ["IExposure"]
