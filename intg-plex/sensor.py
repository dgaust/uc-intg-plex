"""
Sensor entities: the subtitle and audio track playing on a Plex player.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging

from const import PlexConfig
from plex import PlexServer
from ucapi import sensor
from ucapi.entity import EntityTypes
from ucapi_framework import create_entity_id
from ucapi_framework.entities import SensorEntity

_LOG = logging.getLogger(__name__)

# Shown while nothing with switchable tracks is playing (nothing at all, or Live TV).
NOT_PLAYING = "Not playing"


class PlexTrackSensor(SensorEntity):
    """
    A text sensor naming one kind of track in use on the player.

    It follows the media player's updates (every push_update() from the device), and the
    device re-reads the tracks whenever Plex reports on the session, plus once more a
    moment after the subtitle or audio button switches tracks.
    """

    track_id = ""
    track_name = ""

    def __init__(self, config_device: PlexConfig, device: PlexServer):
        self._device = device
        super().__init__(
            create_entity_id(EntityTypes.SENSOR, config_device.identifier, self.track_id),
            f"{config_device.name} {self.track_name}",
            [],
            {
                sensor.Attributes.STATE: sensor.States.UNKNOWN,
                sensor.Attributes.VALUE: NOT_PLAYING,
            },
            device_class=sensor.DeviceClasses.CUSTOM,
        )
        self.subscribe_to_device(device)

    def current_track(self) -> str:
        raise NotImplementedError

    async def sync_state(self) -> None:
        self.update(
            {
                sensor.Attributes.STATE: sensor.States.ON,
                sensor.Attributes.VALUE: self.current_track() or NOT_PLAYING,
            }
        )


class PlexSubtitleSensor(PlexTrackSensor):
    """The subtitle track in use, or "Off"."""

    track_id = "subtitles"
    track_name = "Subtitles"

    def current_track(self) -> str:
        return self._device.subtitle_track


class PlexAudioTrackSensor(PlexTrackSensor):
    """The audio track in use."""

    track_id = "audio_track"
    track_name = "Audio track"

    def current_track(self) -> str:
        return self._device.audio_track
