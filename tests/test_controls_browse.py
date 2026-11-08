"""Coverage for subtitle/audio switching, watched state, and the extra browse folders."""

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from test_now_playing import device  # also puts intg-plex on the import path

import browser
from plexapi.library import Hub


def stream(stream_id, stream_type):
    return SimpleNamespace(id=stream_id, streamType=stream_type, displayTitle="English")


def session(subtitles=(), audio=(), sub_on=None, audio_on=None, live=False):
    """
    A playing item as Plex reports it: the session lists only the tracks in use, while
    the library item (what fetchItem returns) has every track.
    """
    library = [stream(i, 3) for i in subtitles] + [stream(i, 2) for i in audio]
    in_use = [s for s in library if s.id in (sub_on, audio_on)]
    item = SimpleNamespace(
        title="Film",
        media=[SimpleNamespace(parts=[SimpleNamespace(id=1, streams=library)])],
        markPlayed=Mock(),
        markUnplayed=Mock(),
    )
    playing = SimpleNamespace(
        ratingKey=7, live=live, media=[SimpleNamespace(parts=[SimpleNamespace(id=1, streams=in_use)])]
    )
    return playing, item


class StreamTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.server = device()
        self.server.event_loop = asyncio.get_running_loop()
        self.client = Mock()
        self.server._plex_client = self.client

    def playing(self, state):
        current, item = state if state else (None, None)
        self.server._track_cache = None  # each case stands in for a different item
        self.server.get_session_by_client_id = lambda *_args: current
        self.server._plex.fetchItem = Mock(return_value=item)
        return item

    async def test_subtitles_go_through_every_track_then_off(self):
        for on, expected in ((None, 1), (1, 2), (2, 0)):
            with self.subTest(on=on):
                self.playing(session([1, 2], sub_on=on))
                await self.server.async_cycle_subtitles()
                self.client.setSubtitleStream.assert_called_with(expected)

    async def test_subtitles_off(self):
        self.playing(session([1], sub_on=1))
        await self.server.async_cycle_subtitles(off=True)
        self.client.setSubtitleStream.assert_called_with(0)

    async def test_audio_wraps_round_and_needs_two_tracks(self):
        self.playing(session(audio=[5, 6], audio_on=6))
        await self.server.async_cycle_audio()
        self.client.setAudioStream.assert_called_with(5)
        self.client.reset_mock()
        self.playing(session(audio=[5], audio_on=5))
        await self.server.async_cycle_audio()
        self.client.setAudioStream.assert_not_called()

    async def test_live_tv_and_nothing_playing_are_left_alone(self):
        for state in (session([1], [5, 6], audio_on=5, live=True), None):
            self.playing(state)
            await self.server.async_cycle_subtitles()
            await self.server.async_cycle_audio()
            self.assertFalse(await self.server.async_mark_watched(True))
        self.client.setSubtitleStream.assert_not_called()
        self.client.setAudioStream.assert_not_called()

    async def test_track_labels_number_only_repeated_names(self):
        state = session([1, 2], [5], sub_on=2, audio_on=5)
        self.playing(state)
        labels = self.server._read_track_labels(state[0])
        self.assertEqual(labels, {3: "English (2 of 2)", 2: "English"})
        self.playing(session([1, 2], [5], audio_on=5))
        await self.server._refresh_track_labels()
        self.assertEqual((self.server.subtitle_track, self.server.audio_track), ("Off", "English"))
        self.server.push_update.assert_called()
        self.playing(None)
        await self.server._refresh_track_labels()
        self.assertEqual((self.server.subtitle_track, self.server.audio_track), ("", ""))

    async def test_sensors_show_the_tracks(self):
        from sensor import NOT_PLAYING, PlexAudioTrackSensor, PlexSubtitleSensor
        from ucapi import sensor as uc_sensor

        self.server._track_labels = {3: "English (SDH)"}
        for cls, expected in ((PlexSubtitleSensor, "English (SDH)"), (PlexAudioTrackSensor, NOT_PLAYING)):
            entity = cls.__new__(cls)
            entity._device = self.server
            entity.update = Mock()
            await entity.sync_state()
            sent = entity.update.call_args.args[0]
            self.assertEqual(sent[uc_sensor.Attributes.VALUE], expected)
            self.assertEqual(sent[uc_sensor.Attributes.STATE], uc_sensor.States.ON)

    async def test_mark_watched_and_unwatched(self):
        item = self.playing(session())
        self.assertTrue(await self.server.async_mark_watched(True))
        self.assertTrue(await self.server.async_mark_watched(False))
        self.server._plex.fetchItem.assert_called_with(7)
        item.markPlayed.assert_called_once()
        item.markUnplayed.assert_called_once()


def hub(identifier, title, items, hub_type="movie"):
    return SimpleNamespace(
        hubIdentifier=identifier, title=title, size=len(items), type=hub_type, items=lambda: items
    )


def movie(key, title="Film"):
    return SimpleNamespace(type="movie", ratingKey=key, title=title, thumb="/t", year=2000)


class BrowseTests(unittest.TestCase):
    def setUp(self):
        self.server = device()

    def ids(self, result):
        return [(item.title, item.media_type, item.media_id) for item in result.media.items]

    def test_root_adds_discover_playlists_and_up_next_only_while_playing(self):
        plex = SimpleNamespace(library=SimpleNamespace(sections=lambda: []))
        titles = [item.title for item in browser._browse_root(self.server, plex).media.items]
        self.assertEqual(titles, ["On Deck", "Discover", "Playlists"])

        self.server._session = SimpleNamespace(ratingKey=42, live=False)
        items = browser._browse_root(self.server, plex).media.items
        self.assertEqual(items[2].title, "Up Next")
        self.assertEqual(items[2].media_id, "/hubs/metadata/42/postplay")

        self.server._session = SimpleNamespace(ratingKey=42, live=True)
        titles = [item.title for item in browser._browse_root(self.server, plex).media.items]
        self.assertNotIn("Up Next", titles)

    def test_hubs_list_rows_and_open_one_by_identifier(self):
        rows = [
            hub("home.recent", "Recently Added", [movie(1), movie(2)]),
            hub("empty", "Empty", []),
            hub("home.photos", "Photos", [movie(3)], "photo"),
            hub("extras", "Extras", [movie(4)], "clip"),
        ]
        plex = SimpleNamespace(fetchItems=Mock(return_value=rows))
        result = browser._browse_hubs(plex, "/hubs")
        self.assertEqual(result.media.title, "Discover")
        self.assertEqual(self.ids(result), [("Recently Added", "hub", "/hubs#home.recent")])
        plex.fetchItems.assert_called_with("/hubs", cls=Hub)

        result = browser._browse_hub(self.server, plex, "/hubs#home.recent", 2, 1)
        self.assertEqual(result.media.title, "Recently Added")
        self.assertEqual([(i.media_id, i.can_play) for i in result.media.items], [("2", True)])
        self.assertEqual(result.pagination.count, 2)

    def test_playlists_play_and_open_collections_open(self):
        playlist = SimpleNamespace(type="playlist", ratingKey=9, title="Mix", thumb="/p", leafCount=3)
        collection = SimpleNamespace(type="collection", ratingKey=8, title="Saga", thumb="/c", childCount=4)
        plex = SimpleNamespace(
            playlists=lambda: [playlist],
            library=SimpleNamespace(
                sectionByID=lambda _key: SimpleNamespace(collections=lambda: [collection])
            ),
            fetchItem=lambda _key: SimpleNamespace(
                title="Saga", type="collection", thumb=None, items=lambda: [movie(1)]
            ),
        )
        item = browser._browse_playlists(self.server, plex, 1, 20).media.items[0]
        self.assertEqual((item.media_type, item.can_play, item.can_browse, item.subtitle), ("playlist", True, True, "3 items"))
        item = browser._browse_collections(self.server, plex, "1", 1, 20).media.items[0]
        self.assertEqual((item.media_type, item.can_play, item.can_browse, item.subtitle), ("collection", False, True, "4 items"))
        result = browser._browse_container(self.server, plex, "8", 1, 20)
        self.assertEqual((result.media.title, result.media.items[0].media_type), ("Saga", "movie"))

    def test_libraries_offer_collections_and_shows_more_like_this(self):
        section = SimpleNamespace(title="Movies", thumb=None)
        plex = SimpleNamespace(library=SimpleNamespace(sectionByID=lambda _key: section))
        result = browser._browse_library(self.server, plex, "1", "movie_library")
        self.assertEqual(self.ids(result)[-1], ("Collections", "collections", "1"))

        show = SimpleNamespace(title="Show", thumb=None, seasons=lambda: [])
        plex = SimpleNamespace(fetchItem=lambda _key: show)
        result = browser._browse_seasons(self.server, plex, "5")
        self.assertEqual(self.ids(result), [("More Like This", "hubs", "/library/metadata/5/related")])

    def test_unknown_types_are_not_browsable(self):
        clip = SimpleNamespace(type="clip", ratingKey=3, title="Trailer", thumb=None)
        item = browser._media_item(self.server, clip)
        self.assertEqual((item.can_play, item.can_browse), (False, False))


class LiveArtworkTests(unittest.TestCase):
    def test_live_artwork_url_changes_with_the_programme(self):
        server = device()

        def airing(title):
            return SimpleNamespace(
                type="movie", live=True, title=title, guid=f"tv.plex.xmltv://movie/{title}",
                thumb="/library/metadata/72088/thumb/1", art=None,
            )

        first = server.get_artwork_url(airing("BASEketball"))
        second = server.get_artwork_url(airing("The Retirement Plan"))
        self.assertNotEqual(first, second)
        self.assertEqual(first, server.get_artwork_url(airing("BASEketball")))
        self.assertTrue(first.startswith(server.build_plex_url("/library/metadata/72088/thumb/1") + "&programme="))

        library = SimpleNamespace(type="movie", title="Film", thumb="/t", art=None)
        self.assertNotIn("programme=", server.get_artwork_url(library))


if __name__ == "__main__":
    unittest.main()
