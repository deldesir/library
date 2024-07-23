import os

from tests.utils import connect_db_args
from xklb.createdb.tube_add import tube_add
from xklb.lb import library as lb

URL = "https://www.youtube.com/watch?v=BaW_jenozKc"
STORAGE_PREFIX = "tests/data/"

dl_db = "tests/data/dl.db"


def test_yt():
    tube_add([dl_db, URL])
    lb(
        [
            "dl",
            dl_db,
            "--video",
            f"--prefix={STORAGE_PREFIX}",
            "--write-thumbnail",
            "--force",
            "--subs",
            "-s",
            URL,
        ]
    )

    args = connect_db_args(dl_db)

    captions = list(args.db.query("select * from captions"))
    assert {"media_id": 1, "time": 3, "text": "For more information contact phihag@phihag.de"} in captions

    video_id = "BaW_jenozKc"
    thumbnail_path = os.path.join(STORAGE_PREFIX, "Youtube", "Philipp Hagemeister", f"{video_id}.jpg")
    assert os.path.exists(thumbnail_path), "Thumbnail file does not exist"
