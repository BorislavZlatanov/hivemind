"""Hive API: account, post, and comment object retrieval"""
import logging
from hive.server.hive_api.common import get_account_id
from hive.utils.account import safe_db_profile_metadata
log = logging.getLogger(__name__)

# Account objects
# ---------------

async def accounts_by_name(db, names, observer=None, lite=True):
    """Find and return accounts by `name`."""

    sql = """SELECT id, name, about, created_at,
                    rank, followers, following, posting_json_metadata, json_metadata
               FROM hive_accounts WHERE name IN :names"""
    rows = await db.query_all(names=tuple(names))

    accounts = {}
    for row in rows:
        profile = safe_db_profile_metadata(row['posting_json_metadata'], row['json_metadata'])
        account = {
            'id': row['id'],
            'name': row['name'],
            'created': str(row['created_at']).split(' ')[0],
            'rank': row['rank'],
            'followers': row['followers'],
            'following': row['following'],
            'display_name': profile['name'],
            'about': profile['about'],
        }
        if not lite:
            account['location'] = profile['location']
            account['website'] = profile['website']
            account['profile_image'] = profile['profile_image']
            account['cover_image'] = profile['cover_image']
        accounts[account['id']] = account

    if observer:
        await _follow_contexts(db, accounts,
                               observer_id=await get_account_id(db, observer),
                               include_mute=not lite)

    return accounts.values()

async def _follow_contexts(db, accounts, observer_id, include_mute=False):
    sql = """SELECT following, state FROM hive_follows
              WHERE follower = :account_id AND following IN :ids"""
    rows = await db.query_all(sql,
                              account_id=observer_id,
                              ids=tuple(accounts.keys()))
    for row in rows:
        following_id = row[0]
        state = row[1]
        context = {'followed': state == 1}
        if include_mute and state == 2:
            context['muted'] = True
        accounts[following_id]['context'] = context

    for account in accounts.values():
        if 'context' not in account:
            account['context'] = {'followed': False}


# Comment objects
# ---------------

async def comments_by_id(db, ids, observer=None):
    """Given an array of post ids, returns comment objects keyed by id."""
    assert ids, 'no ids passed to comments_by_id'

    sql = """
      SELECT
        hp.id,
        hp.author,
        hp.permlink,
        hp.body,
        hp.depth,
        hp.payout,
        hp.payout_at,
        hp.is_paidout,
        hp.created_at,
        hp.updated_at,
        hp.rshares,
        hp.is_hidden,
        hp.is_grayed,
        hp.votes
      FROM hive_posts_view hp
      WHERE hp.id IN :ids""" #votes
    result = await db.query_all(sql, ids=tuple(ids))

    authors = set()
    by_id = {}
    for row in result:
        top_votes, observer_vote = _top_votes(row, 5, observer)
        post = {
            'id': row['id'],
            'author': row['author'],
            'url': row['author'] + '/' + row['permlink'],
            'depth': row['depth'],
            'body': row['body'],
            'payout': str(row['payout']),
            'created_at': str(row['created_at']),
            'updated_at': str(row['updated_at']),
            'payout_at': str(row['payout_at']),
            'is_paidout': row['is_paidout'],
            'rshares': row['rshares'],
            'hide': row['is_hidden'] or row['is_grayed'],
            'top_votes': top_votes,
        }

        authors.add(row['author'])

        if observer:
            post['context'] = {'vote_rshares': observer_vote}
        by_id[post['id']] = post

    by_id = await _append_flags(db, by_id)
    return {'posts': by_id, #[by_id[_id] for _id in ids],
            'accounts': await accounts_by_name(db, authors, observer, lite=True)}

async def posts_by_id(db, ids, observer=None, lite=True):
    """Given a list of post ids, returns lite post objects in the same order."""

    # pylint: disable=too-many-locals
    sql = """
        SELECT 
          hp.id,
          hp.author,
          hp.permlink,
          hp.title, 
          hp.img_url,
          hp.payout,
          hp.promoted,
          hp.created_at,
          hp.payout_at,
          hp.is_nsfw,
          hp.rshares,
          hp.votes,
          hp.is_muted,
          hp.is_valid,
          %s
        FROM hive_posts_view hp 
        WHERE id IN :ids"""
    fields = ['hp.preview'] if lite else ['hp.body', 'hp.updated_at', 'hp.json']
    sql = sql % (', '.join(fields))

    reblogged_ids = await _reblogged_ids(db, observer, ids) if observer else []

    # TODO: filter out observer's mutes?

    # key by id.. returns sorted by input order
    authors = set()
    by_id = {}
    for row in await db.query_all(sql, ids=tuple(ids)):
        assert not row['is_muted']
        assert row['is_valid']
        pid = row['id']
        top_votes, observer_vote = _top_votes(row, 5, observer)

        obj = {
            'id': pid,
            'author': row['author'],
            'url': row['author'] + '/' + row['permlink'],
            'title': row['title'],
            'payout': float(row['payout']),
            'promoted': float(row['promoted']),
            'created_at': str(row['created_at']),
            'payout_at': str(row['payout_at']),
            'is_paidout': row['is_paidout'],
            'rshares' : row['rshares'],
            'top_votes' : top_votes,
            'thumb_url': row['img_url'],
            'is_nsfw' : row['is_nsfw'],
        }

        if lite:
            obj['preview'] = row['preview']
        else:
            obj['body'] = row['body']
            obj['updated_at'] = str(row['updated_at'])
            obj['json_metadata'] = row['json']

        if observer:
            obj['context'] = {
                'reblogged': obj['id'] in reblogged_ids,
                'vote_rshares': observer_vote
            }

        authors.add(obj['author'])
        by_id[row['id']] = obj

    # in rare cases of cache inconsistency, recover and warn
    missed = set(ids) - by_id.keys()
    if missed:
        log.warning("by_id do not exist in cache: %s", repr(missed))
        for _id in missed:
            ids.remove(_id)

    by_id = await _append_flags(db, by_id)
    return {'posts': [by_id[_id] for _id in ids],
            'accounts': await accounts_by_name(db, authors, observer, lite=True)}

async def _append_flags(db, posts):
    sql = """
        SELECT 
            id, parent_id, community_id,  hcd.category as category, is_muted, is_valid
        FROM hive_posts hp
        LEFT JOIN hive_category_data hcd ON hcd.id = hp.category_id
        WHERE id IN :ids"""
    for row in await db.query_all(sql, ids=tuple(posts.keys())):
        post = posts[row['id']]
        post['parent_id'] = row['parent_id']
        post['community_id'] = row['community_id']
        post['category'] = row['category']
        post['is_muted'] = row['is_muted']
        post['is_valid'] = row['is_valid']
    return posts

async def _reblogged_ids(db, observer, post_ids):
    sql = """
        SELECT
            hr.post_id
        FROM 
            hive_reblogs hr
        INNER JOIN hive_accounts ha ON ha.id = hr.blogger_id
        WHERE
            ha.name = :observer
            AND hr.post_id IN :ids
    """
    return  await db.query_col(sql, observer=observer, ids=tuple(post_ids))

def _top_votes(obj, limit, observer):
    observer_vote = None
    votes = []
    if obj['votes']:
        for csa in obj['votes'].split("\n"):
            print(">>>"+csa+"<<<<")
            voter, rshares = csa.split(",")[0:2]
            rshares = int(rshares)
            votes.append((voter, rshares))

            if observer == voter:
                observer_vote = rshares

    top = sorted(votes, key=lambda row: abs(int(row[1])), reverse=True)[:limit]

    return (top, observer_vote)
