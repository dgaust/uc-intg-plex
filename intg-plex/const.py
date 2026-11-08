"""Constants used for Plex integration."""

from dataclasses import dataclass

from ucapi.media_player import Commands, Features, MediaContentType
from ucapi.ui import Buttons, DeviceButtonMapping, UiPage


@dataclass
class PlexConfig:
    """Plex device configuration."""

    identifier: str
    name: str
    address: str
    username: str
    password: str
    auth_token: str
    server_name: str
    port: str
    tv_selection: str
    movie_selection: str
    page_size: int = 20
    sort_order: str = "titleSort:asc"
    show_placeholders: bool = True


PLEX_MEDIA_TYPES = {
    "music": MediaContentType.MUSIC,
    "artist": MediaContentType.MUSIC,
    "album": MediaContentType.MUSIC,
    "song": MediaContentType.MUSIC,
    "video": MediaContentType.VIDEO,
    "set": MediaContentType.MUSIC,
    "musicvideo": MediaContentType.VIDEO,
    "movie": MediaContentType.MOVIE,
    "tvshow": MediaContentType.TV_SHOW,
    "season": MediaContentType.TV_SHOW,
    "episode": MediaContentType.TV_SHOW,
    "channel": MediaContentType.TV_SHOW,
    "audio": MediaContentType.MUSIC,
}

PLEX_FEATURES = [
    Features.VOLUME,
    Features.MUTE,
    Features.PLAY_PAUSE,
    Features.STOP,
    Features.NEXT,
    Features.PREVIOUS,
    Features.FAST_FORWARD,
    Features.REWIND,
    Features.MEDIA_TITLE,
    Features.MEDIA_IMAGE_URL,
    Features.MEDIA_TYPE,
    Features.MEDIA_DURATION,
    Features.MEDIA_POSITION,
    Features.MEDIA_ARTIST,
    Features.MEDIA_ALBUM,
    Features.DPAD,
    Features.HOME,
    Features.MENU,
    Features.CONTEXT_MENU,
    Features.GUIDE,
    Features.INFO,
    Features.SEEK,
    Features.REPEAT,
    Features.SHUFFLE,
    Features.PLAY_MEDIA,
    Features.BROWSE_MEDIA,
    Features.SEARCH_MEDIA,
    Features.PLAY_MEDIA_ACTION,
    Features.CLEAR_PLAYLIST,
    Features.SUBTITLE,
    Features.AUDIO_TRACK,
]


# Custom commands (shown on the remote as simple commands), acting on what's playing now.
CMD_SUBTITLES_OFF = "SUBTITLES_OFF"
CMD_MARK_WATCHED = "MARK_WATCHED"
CMD_MARK_UNWATCHED = "MARK_UNWATCHED"

PLEX_SIMPLE_COMMANDS = {
    CMD_SUBTITLES_OFF: "Subtitles off",
    CMD_MARK_WATCHED: "Mark watched",
    CMD_MARK_UNWATCHED: "Mark unwatched",
}

PLEX_ACTIONS_KEYMAP = {}

PLEX_REMOTE_BUTTONS_MAPPING: list[DeviceButtonMapping] = [  # type: ignore[assignment]
    {"button": Buttons.BACK, "short_press": {"cmd_id": Commands.BACK}},
    {"button": Buttons.HOME, "short_press": {"cmd_id": Commands.HOME}},
    {"button": Buttons.CHANNEL_DOWN, "short_press": {"cmd_id": Commands.CHANNEL_DOWN}},
    {"button": Buttons.CHANNEL_UP, "short_press": {"cmd_id": Commands.CHANNEL_UP}},
    {"button": Buttons.DPAD_UP, "short_press": {"cmd_id": Commands.CURSOR_UP}},
    {"button": Buttons.DPAD_DOWN, "short_press": {"cmd_id": Commands.CURSOR_DOWN}},
    {"button": Buttons.DPAD_LEFT, "short_press": {"cmd_id": Commands.REWIND}},
    {"button": Buttons.DPAD_RIGHT, "short_press": {"cmd_id": Commands.FAST_FORWARD}},
    {"button": Buttons.DPAD_MIDDLE, "short_press": {"cmd_id": Commands.CURSOR_ENTER}},
    {"button": Buttons.PLAY, "short_press": {"cmd_id": Commands.PLAY_PAUSE}},
    {"button": Buttons.PREV, "short_press": {"cmd_id": Commands.PREVIOUS}},
    {"button": Buttons.NEXT, "short_press": {"cmd_id": Commands.NEXT}},
    {"button": Buttons.MUTE, "short_press": {"cmd_id": Commands.MUTE}},
]  # ty:ignore[invalid-assignment]

PLEX_REMOTE_SIMPLE_COMMANDS = [
    Commands.MUTE,
    Commands.PLAY_PAUSE,
    Commands.STOP,
    Commands.HOME,
    Commands.BACK,
    Commands.PREVIOUS,
    Commands.NEXT,
    Commands.FAST_FORWARD,
    Commands.REWIND,
    Commands.SUBTITLE,
    Commands.AUDIO_TRACK,
    CMD_SUBTITLES_OFF,
    CMD_MARK_WATCHED,
    CMD_MARK_UNWATCHED,
]

PLEX_REMOTE_UI_PAGES: list[UiPage] = [  # type: ignore[assignment]
    {
        "page_id": "Plex commands",
        "name": "Plex commands",
        "grid": {"width": 4, "height": 6},
        "items": [
            {
                "command": {
                    "cmd_id": "remote.send",
                    "params": {"command": Commands.PLAY_PAUSE, "repeat": 1},
                },
                "icon": "uc:play",
                "location": {"x": 0, "y": 0},
                "size": {"height": 1, "width": 1},
                "type": "icon",
            },
            {
                "command": {
                    "cmd_id": "remote.send",
                    "params": {"command": Commands.AUDIO_TRACK, "repeat": 1},
                },
                "icon": "uc:language",
                "location": {"x": 1, "y": 0},
                "size": {"height": 1, "width": 1},
                "type": "icon",
            },
            {
                "command": {
                    "cmd_id": "remote.send",
                    "params": {"command": Commands.SUBTITLE, "repeat": 1},
                },
                "icon": "uc:cc",
                "location": {"x": 2, "y": 0},
                "size": {"height": 1, "width": 1},
                "type": "icon",
            },
            {
                "command": {"cmd_id": Commands.CONTEXT_MENU},
                "icon": "uc:menu",
                "location": {"x": 3, "y": 5},
                "size": {"height": 1, "width": 1},
                "type": "icon",
            },
        ],
    },
]  # ty:ignore[invalid-assignment]


def key_update_helper(input_attributes, key: str, value: str | None, attributes):
    """Return modified attributes only."""
    if value is None:
        return attributes

    if key in input_attributes:
        if input_attributes[key] != value:
            attributes[key] = value
    else:
        attributes[key] = value

    return attributes
