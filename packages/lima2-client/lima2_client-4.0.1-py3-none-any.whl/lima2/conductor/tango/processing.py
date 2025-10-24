# This file is part of the Lima2 project
#
# Copyright (c) 2020-2024 Beamline Control Unit, ESRF
# Distributed under the MIT licence. See LICENSE for more info.

"""Lima2 processing tango device.

Specializes the ProcessingDevice protocol for lima2 tango processing devices.

Allows us to add typechecking to all attributes and remote procedure calls.
"""

import logging
import traceback
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, cast
from uuid import UUID

import orjson
import tango as tg

from lima2.common.exceptions import Lima2DeviceError
from lima2.common.types import FrameInfo
from lima2.conductor.tango.utils import handle_tango_errors, unpack_exception

logger = logging.getLogger(__name__)


@dataclass
class ProcessingErrorEvent:
    """Structure passed to on_error when a device reports an error."""

    device_name: str
    what: str
    info: str


class TangoProcessing:
    """Wrapper around the raw processing DeviceProxy.

    Provides type-annotated methods and attributes.

    Does not implement the TangoDevice protocol since it doesn't have an acq_state
    attribute. This is not an issue for type checking, since processing devices are
    never grouped with control/receiver devices.
    """

    def __init__(self, url: str, class_name: str, timeout_s: float):
        self.device = tg.DeviceProxy(url, green_mode=tg.GreenMode.Asyncio)
        self.device.set_timeout_millis(timeout_s * 1000)
        self.class_name = class_name

        self.on_finished_event_id: int = -1
        self.on_error_event_id: int = -1

        self.commands: list[str] = self.device.get_command_list()

    @property
    def name(self) -> str:
        return cast(str, self.device.dev_name())

    @handle_tango_errors
    async def ping(self) -> int:
        return cast(int, await self.device.ping())

    @handle_tango_errors
    async def read_attribute(self, name: str) -> Any:
        """Get an attribute's value given its name."""
        return (await self.device.read_attribute(name)).value

    @handle_tango_errors
    async def progress_counters(self) -> dict[str, int]:
        value: str = await self.read_attribute("progress_counters")
        return cast(dict[str, int], orjson.loads(value))

    @handle_tango_errors
    async def last_frames(self) -> dict[str, int]:
        value = await self.read_attribute("last_frames")
        last_frames: dict[str, int] = orjson.loads(value)
        return last_frames

    @handle_tango_errors
    async def raw_frame_info(self) -> FrameInfo:
        # Raises DevFailed if db offline
        db = tg.Database()
        # value always has a "frame_info" key
        value = db.get_device_property(dev_name=self.name, value="frame_info")
        if len(value["frame_info"]) < 1:
            raise Lima2DeviceError(
                f"Device {self.name} has no 'frame_info' property",
                device_name=self.name,
            )
        else:
            frame_info = orjson.loads(value["frame_info"][0])
            return FrameInfo.from_dict(frame_info)

    @handle_tango_errors
    async def input_frame_info(self) -> FrameInfo:
        value: str = await self.read_attribute("input_frame_info")
        frame_info: dict[str, Any] = orjson.loads(value)
        return FrameInfo.from_dict(frame_info)

    @handle_tango_errors
    async def processed_frame_info(self) -> FrameInfo:
        value: str = await self.read_attribute("processed_frame_info")
        frame_info: dict[str, Any] = orjson.loads(value)
        return FrameInfo.from_dict(frame_info)

    @handle_tango_errors
    async def pop_reduced_data(self, getter_name: str) -> tuple[str, bytes]:
        if getter_name not in self.commands:
            raise ValueError(
                f"Cannot fetch reduced data from device {self.name}: "
                f"command {getter_name} not available"
            )
        return cast(tuple[str, bytes], await self.device.command_inout(getter_name))

    async def on_finished(self, callback: Callable[[str], Awaitable[None]]) -> None:
        """Register a callback to the is_finished data_ready_event."""
        if self.on_finished_event_id != -1:
            logger.debug(
                f"Unsubscribing previous on_finished callback id={self.on_finished_event_id}"
            )
            await self.device.unsubscribe_event(self.on_finished_event_id)

        async def wrapper(evt: tg.DataReadyEventData) -> None:
            if evt.err:
                # logger.debug(f"Processing device {evt.device.dev_name()} is offline")
                return

            try:
                await callback(evt.device.dev_name())
            except Exception:
                logger.error(
                    "Exception raised in processing device on_finished callback:\n"
                    f"{traceback.format_exc()}"
                )

        self.on_finished_event_id = await self.device.subscribe_event(
            "is_finished", tg.EventType.DATA_READY_EVENT, wrapper
        )

        logger.debug(f"Subscribed to is_finished event id={self.on_finished_event_id}")

    async def on_error(
        self, callback: Callable[[ProcessingErrorEvent], Awaitable[None]]
    ) -> None:
        """Register a callback to the last_error data_ready_event."""
        if self.on_error_event_id != -1:
            logger.debug(
                f"Unsubscribing previous on_error callback id={self.on_error_event_id}"
            )
            await self.device.unsubscribe_event(self.on_error_event_id)

        async def wrapper(evt: tg.DataReadyEventData) -> None:
            if evt.err:
                # logger.debug(f"Processing device {evt.device.dev_name()} is offline")
                return

            payload = (await evt.device.read_attribute("last_error")).value
            what, info = unpack_exception(payload)

            proc_err_evt = ProcessingErrorEvent(
                device_name=evt.device.dev_name(), what=what, info=info
            )

            try:
                await callback(proc_err_evt)
            except Exception:
                logger.error(
                    "Exception raised in processing device on_error callback:\n"
                    f"{traceback.format_exc()}"
                )

        self.on_error_event_id = await self.device.subscribe_event(
            "last_error", tg.EventType.DATA_READY_EVENT, wrapper
        )

        logger.debug(f"Subscribed to last_error event id={self.on_error_event_id}")


def from_uuid(uuid: UUID, timeout_s: float) -> list[TangoProcessing]:
    """Create a list of TangoProcessing instances from a single pipeline uuid."""
    db = tg.Database()
    urls = db.get_device_exported(f"*/limaprocessing/{str(uuid)}*")

    if not urls:
        raise ValueError(f"Processing devices not found in tango database: {uuid=}")

    class_names = [db.get_device_info(url).class_name for url in urls]
    if not all(class_name == class_names[0] for class_name in class_names):
        raise NotImplementedError("Heterogeneous processing is not supported")

    def rcv_idx(name: str) -> int:
        """
        Find the receiver index from a processing device name, by splitting
        on the '@' character.
        """
        return int(name.split("@")[-1])

    # Sort the processing devices by receiver index
    sorted_urls = sorted(urls, key=rcv_idx)

    return [
        TangoProcessing(url=url, class_name=class_name, timeout_s=timeout_s)
        for url, class_name in zip(sorted_urls, class_names, strict=True)
    ]
