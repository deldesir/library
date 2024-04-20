import argparse, os, sqlite3

from xklb import media_printer, usage
from xklb.utils import arggroups, consts, db_utils, objects
from xklb.utils.log_utils import log


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        "library playlists",
        usage.playlists,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    arggroups.sql_fs(parser)
    arggroups.sql_media(parser)
    arggroups.debug(parser)

    arggroups.database(parser)
    parser.add_argument("search", nargs="*")
    args = parser.parse_intermixed_args()

    args.include += args.search

    args.db = db_utils.connect(args)
    log.info(objects.dict_filter_bool(args.__dict__))

    args.action = consts.SC.playlists
    return args


def construct_query(args) -> tuple[str, dict]:
    pl_columns = db_utils.columns(args, "playlists")
    args.filter_sql = []
    args.filter_bindings = {}

    args.filter_sql.extend([" and " + w for w in args.where])

    args.table = "playlists"
    if args.db["playlists"].detect_fts():
        if args.include:
            args.table, search_bindings = db_utils.fts_search_sql(
                "playlists",
                fts_table=args.db["playlists"].detect_fts(),
                include=args.include,
                exclude=args.exclude,
                flexible=args.flexible_search,
            )
            args.filter_bindings = {**args.filter_bindings, **search_bindings}
        elif args.exclude:
            db_utils.construct_search_bindings(
                args,
                [f"{k}" for k in pl_columns if k in db_utils.config["media"]["search_columns"]],
            )
    else:
        db_utils.construct_search_bindings(
            args,
            [f"{k}" for k in pl_columns if k in db_utils.config["media"]["search_columns"]],
        )

    LIMIT = "LIMIT " + str(args.limit) if args.limit else ""
    query = f"""SELECT
        *
    FROM {args.table} m
    WHERE 1=1
        and COALESCE(time_deleted,0) = 0
        {" ".join(args.filter_sql)}
        {'AND extractor_key != "Local"' if args.online_media_only else ''}
        {'AND extractor_key = "Local"' if args.local_media_only else ''}
    ORDER BY 1=1
        {', ' + args.sort if args.sort else ''}
        , path
        , random()
    {LIMIT}
    """

    return query, args.filter_bindings


def delete_playlists(args, playlists) -> None:
    deleted_playlist_count = 0
    with args.db.conn:
        playlist_paths = playlists + [p.rstrip(os.sep) for p in playlists]
        cursor = args.db.conn.execute(
            "delete from playlists where path in (" + ",".join(["?"] * len(playlist_paths)) + ")",
            playlist_paths,
        )
        deleted_playlist_count = cursor.rowcount

    deleted_media_count = 0
    try:
        online_media = [p for p in playlists if p.startswith("http")]
        if online_media:
            with args.db.conn:
                cursor = args.db.conn.execute(
                    """DELETE from media where
                    playlists_id in (
                        SELECT id from playlists
                        WHERE path IN ("""
                    + ",".join(["?"] * len(online_media))
                    + "))",
                    (*online_media,),
                )
                deleted_media_count += cursor.rowcount
    except sqlite3.OperationalError:  # no such column: playlists_id
        pass

    local_media = [p.rstrip(os.sep) for p in playlists if not p.startswith("http")]
    for folder in local_media:
        with args.db.conn:
            cursor = args.db.conn.execute("delete from media where path like ?", (folder + "%",))
            deleted_media_count += cursor.rowcount

    print(f"Deleted {deleted_playlist_count} playlists ({deleted_media_count} media records)")


def playlists() -> None:
    args = parse_args()

    pl_columns = db_utils.columns(args, "playlists")
    m_columns = db_utils.columns(args, "media")
    query, bindings = construct_query(args)

    if "playlists_id" in m_columns:
        query = f"""
        select
            coalesce(p.path, "Playlist-less media") path
            , p.extractor_key
            {', p.title' if 'title' in pl_columns else ''}
            {', p.time_deleted' if 'time_deleted' in pl_columns else ''}
            {', count(*) FILTER(WHERE play_count>0) play_count' if 'play_count' in m_columns else ''}
            {', sum(m.duration) duration' if 'duration' in m_columns else ''}
            {', sum(m.size) size' if 'size' in m_columns else ''}
            , count(*) count
        from media m
        join ({query}) p on p.id = m.playlists_id
        group by m.playlists_id, coalesce(p.path, "Playlist-less media")
        order by count, p.path
        """

    if "a" in args.print:
        query = f"""
        select
            'Aggregate of playlists' path
            {', count(*) FILTER(WHERE time_deleted>0) deleted_count' if 'time_deleted' in query else ''}
            {', sum(play_count) play_count' if 'play_count' in query else ''}
            {', sum(duration) duration' if 'duration' in query else ''}
            {', avg(duration) avg_playlist_duration' if 'duration' in query else ''}
            {', sum(size) size' if 'size' in query else ''}
            , count(*) playlists_count
            {', sum(count) media_count' if 'count' in query else ''}
        from ({query})
        """

    playlists = list(args.db.query(query, bindings))
    media_printer.media_printer(args, playlists, units="playlists")

    if args.delete_rows:
        delete_playlists(args, [d["path"] for d in playlists])