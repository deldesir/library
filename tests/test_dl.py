import unittest
from argparse import Namespace
from pathlib import Path
from unittest import mock

from xklb import paths
from xklb.db import connect
from xklb.dl_extract import dl_add, dl_block, dl_download, dl_update, yt
from xklb.tube_extract import tube_add

PLAYLIST_URL = "https://youtube.com/playlist?list=PLVoczRgDnXDLWV1UJ_tO70VT_ON0tuEdm"
PLAYLIST_VIDEO_URL = "https://www.youtube.com/watch?v=QoXubRvB6tQ"
STORAGE_PREFIX = "tests/data/"

dl_db = "--db", "tests/data/dl.db"

tube_db = "--db", "tests/data/tube_dl.db"
tube_add([*tube_db, PLAYLIST_URL])


class TestTube(unittest.TestCase):
    def init_db(self):
        for p in Path("tests/data/").glob("dl.db*"):
            p.unlink()
        dl_add([*dl_db, "-c=Self", PLAYLIST_URL])

    def test_yt(self):
        dl_db = "--db", "tests/data/dl.db"
        dl_add([*dl_db, "-c=Self", PLAYLIST_URL])

        args = Namespace(
            database=dl_db[1],
            dl_config={},
            prefix=STORAGE_PREFIX,
            ext=None,
            ignore_errors=False,
            small=False,
            verbose=0,
        )
        args.db = connect(args)
        yt(args, dict(path=PLAYLIST_VIDEO_URL, dl_config="{}", category="Self", profile="video"))

    @mock.patch("xklb.dl_extract.yt")
    @mock.patch("xklb.tube_backend.process_playlist")
    def test_tube_dl_conversion(self, process_playlist, yt):
        dl_add([*tube_db, "-c=Self", PLAYLIST_URL])
        out = process_playlist.call_args[0][1]
        assert out == PLAYLIST_URL

        dl_download([*tube_db, STORAGE_PREFIX])
        out = yt.call_args[0]
        assert out[1]["path"] == PLAYLIST_VIDEO_URL

    @mock.patch("xklb.dl_extract.yt")
    def test_download(self, yt):
        self.init_db()

        dl_download([*dl_db, STORAGE_PREFIX])
        out = yt.call_args[0]
        assert out[1]["path"] == PLAYLIST_VIDEO_URL

    @mock.patch("xklb.tube_backend.update_playlists")
    def test_dlupdate(self, update_playlists):
        self.init_db()

        dl_update([*dl_db])
        out = update_playlists.call_args[0]
        assert out[1][0]["path"] == PLAYLIST_URL

    @mock.patch("xklb.tube_backend.update_playlists")
    def test_dlupdate_subset_category(self, update_playlists):
        self.init_db()

        dl_update([*dl_db, "-c=Self"])
        out = update_playlists.call_args[0]
        assert out[1][0]["path"] == PLAYLIST_URL

    def test_block_existing(self):
        self.init_db()

        dl_block([*dl_db, PLAYLIST_URL])
        db = connect(Namespace(database=dl_db[1], verbose=2))
        playlists = list(db["playlists"].rows)
        assert playlists[0]["is_deleted"] == 1
        assert playlists[0]["category"] == paths.BLOCK_THE_CHANNEL
