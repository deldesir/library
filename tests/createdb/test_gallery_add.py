from pathlib import Path
from unittest import skip

from xklb.createdb import gallery_backend
from xklb.utils.db_utils import connect
from xklb.utils.objects import NoneSpace


def create_args(test_name):
    db_path = f"tests/data/gdl_{test_name}.db"
    Path(db_path).unlink(missing_ok=True)
    Path(db_path).touch()

    args = NoneSpace(database=db_path, verbose=2)
    args.db = connect(args)
    return args


@skip("inconsistent between gallery-dl versions")
def test_safe_mode():
    args = NoneSpace()
    assert gallery_backend.is_supported(args, "https://i.redd.it/gdlcqo5xvpwa1.png")
    assert gallery_backend.is_supported(args, "https://www.reddit.com/gallery/145863a")
    assert gallery_backend.is_supported(args, "https://old.reddit.com/r/lego/comments/145863a/spaceship_moc/")
    assert gallery_backend.is_supported(args, "www.com") is False
    assert gallery_backend.is_supported(args, "https://youtu.be/HoY5RbzRcmo") is False


@skip("imgur is 429")
def test_get_playlist_metadata_imgur_single():
    args = create_args("playlist_metadata_imgur_single")
    out = gallery_backend.get_playlist_metadata(args, "https://imgur.com/0gybAXR")
    assert out == 1
    data = list(args.db.query("select * from media"))
    assert len(data) == 1
    assert data[0]["path"] == "https://i.imgur.com/0gybAXR.mp4"
    assert data[0]["webpath"] == "https://imgur.com/0gybAXR"


@skip("imgur is 429")
def test_get_playlist_metadata_imgur_album():
    args = create_args("playlist_metadata_imgur_album")
    out = gallery_backend.get_playlist_metadata(args, "https://imgur.com/t/album/jc19AA5")
    assert out == 2
    media = list(args.db.query("select * from media"))
    assert len(media) == 2
    playlists = list(args.db.query("select * from playlists"))
    assert len(playlists) == 1


def test_get_playlist_metadata_blogspot_album():
    args = create_args("get_playlist_metadata_blogspot_album")
    out = gallery_backend.get_playlist_metadata(
        args,
        "http://dyanasmen.blogspot.com/2008/10/frumoasele-jucatoare-de-la-wimbledon.html",
    )
    assert out == 4
    media = list(args.db.query("select * from media"))
    assert len(media) == 4
    playlists = list(args.db.query("select * from playlists"))
    assert len(playlists) == 1


@skip("tumblr is obake")
def test_get_playlist_metadata_tumblr_single():
    args = create_args("playlist_metadata_tumblr_single")
    out = gallery_backend.get_playlist_metadata(
        args,
        "https://66.media.tumblr.com/7f87be573a76ccb4899ed24b24dc1328/tumblr_ny1nxrqkni1tse85no1_1280.jpg",
    )
    assert out == 1
    media = list(args.db.query("select * from media"))
    assert len(media) == 1


@skip("tumblr is obake")
def test_get_playlist_metadata_tumblr_album():
    args = create_args("playlist_metadata_tumblr_album")
    out = gallery_backend.get_playlist_metadata(args, "https://www.tumblr.com/toricoriot/719481863148830720/fairy")
    assert out == 6
    media = list(args.db.query("select * from media"))
    assert len(media) == 6
