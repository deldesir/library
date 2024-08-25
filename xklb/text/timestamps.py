import datetime

from dateutil.parser import parse

from xklb import usage
from xklb.utils import arggroups, argparse_utils, nums


def print_timestamp(n):
    nonzero_denominator = n % 1
    print(n if nonzero_denominator else int(n))


def timestamps(defaults_override=None):
    parser = argparse_utils.ArgumentParser(usage=usage.dates)
    parser.add_argument("--from-unix", "--unix", "-u", action="store_true", help="Parse from UNIX time")

    parser.add_argument(
        "--month-day-year",
        "-m-d-y",
        action="store_true",
        help="""Parse ambiguous 3-integer date as MDY (default)
Example: 01/10/05
MDY  2005-01-10
DMY  2005-10-01
YMD  2001-10-05
YDM  2001-05-10

Example: July 8th, 2009
MDY  07/08/09
DMY  08/07/09
YMD  09/07/08
YDM  09/08/07
""",
    )
    parser.add_argument("--day-month-year", "-d-m-y", action="store_true", help="Parse ambiguous 3-integer date as DMY")
    parser.add_argument("--year-month-day", "-y-m-d", action="store_true", help="Parse ambiguous 3-integer date as YMD")
    parser.add_argument("--year-day-month", "-y-d-m", action="store_true", help="Parse ambiguous 3-integer date as YDM")

    parser.add_argument(
        "--to-date-only", "--date-only", "--date", "-d", action="store_true", help="Format the output as only dates"
    )
    parser.add_argument(
        "--to-time-only", "--time-only", "--time", "-t", action="store_true", help="Format the output as only times"
    )
    parser.add_argument("--to-unix", "-U", action="store_true", help="Format as UNIX time")

    arggroups.debug(parser)

    parser.add_argument(
        "dates", nargs="*", default=argparse_utils.STDIN_DASH, action=argparse_utils.ArgparseArgsOrStdin
    )

    parser.set_defaults(**(defaults_override or {}))
    args = parser.parse_args()
    arggroups.args_post(args, parser)

    day_first = None
    year_first = None
    if args.month_day_year:
        day_first = False
        year_first = False
    elif args.day_month_year:
        day_first = True
        year_first = False
    elif args.year_month_day:
        day_first = False
        year_first = True
    elif args.year_day_month:
        day_first = True
        year_first = True

    for date_str in args.dates:
        if args.from_unix:
            date = datetime.datetime.fromtimestamp(nums.safe_float(date_str), tz=datetime.timezone.utc)  # type: ignore
        else:
            date = parse(
                date_str,
                default=datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0),
                fuzzy=True,
                dayfirst=day_first,
                yearfirst=year_first,
            )

        tzinfo = date.tzinfo
        if args.to_time_only:
            date = date.time()
        elif args.to_date_only:
            date = date.date()

        if args.to_unix:
            if isinstance(date, datetime.datetime):
                print_timestamp(date.timestamp())
            elif isinstance(date, datetime.date):
                print_timestamp(
                    datetime.datetime(
                        year=date.year, month=date.month, day=date.day, hour=0, minute=0, microsecond=0, tzinfo=tzinfo
                    ).timestamp()
                )
            elif isinstance(date, datetime.time):
                print_timestamp(date.hour * 3600 + date.minute * 60 + date.second + date.microsecond / 1e6)
            else:
                raise NotImplementedError
        else:
            if isinstance(date, datetime.datetime):
                if date.tzinfo == datetime.timezone.utc:
                    date = date.replace(tzinfo=None)
                print(date.isoformat())
            elif isinstance(date, datetime.date):
                print(date.isoformat())
            elif isinstance(date, datetime.time):
                print(date.isoformat())
            else:
                raise NotImplementedError


def times():
    timestamps({"to_time_only": True})


def dates():
    timestamps({"to_date_only": True})
