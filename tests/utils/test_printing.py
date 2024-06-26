import unittest

from tests import utils
from xklb.utils import printing


def test_col_naturaldate():
    assert printing.col_naturaldate([{"t": 0, "t1": 1}], "t") == [{"t": None, "t1": 1}]
    assert printing.col_naturaldate([{"t": 0, "t1": int(utils.ignore_tz(172799))}], "t1") == [
        {"t": 0, "t1": "Jan 02 1970"}
    ]


def test_col_naturalsize():
    assert printing.col_naturalsize([{"t": 0, "t1": 1}], "t") == [{"t": None, "t1": 1}]
    assert printing.col_naturalsize([{"t": 946684800, "t1": 1}], "t") == [{"t": "902.8 MiB", "t1": 1}]


def test_human_time():
    assert printing.human_duration(0) == ""
    assert printing.human_duration(946684800) == "30 years and 7 days"


def test_col_duration():
    assert printing.col_duration([{"t": 0, "t1": 1}], "t") == [{"t": "", "t1": 1}]
    assert printing.col_duration([{"t": 946684800, "t1": 1}], "t") == [{"t": "30 years and 7 days", "t1": 1}]


class SecondsToHHMMSSTestCase(unittest.TestCase):
    def test_positive_seconds(self):
        assert printing.seconds_to_hhmmss(1) == "    0:01"
        assert printing.seconds_to_hhmmss(59) == "    0:59"
        assert printing.seconds_to_hhmmss(600) == "   10:00"
        assert printing.seconds_to_hhmmss(3600) == " 1:00:00"
        assert printing.seconds_to_hhmmss(3665) == " 1:01:05"
        assert printing.seconds_to_hhmmss(86399) == "23:59:59"
        assert printing.seconds_to_hhmmss(86400) == "24:00:00"
        assert printing.seconds_to_hhmmss(90061) == "25:01:01"

    def test_zero_seconds(self):
        assert printing.seconds_to_hhmmss(0) == "    0:00"
