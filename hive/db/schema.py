"""Db schema definitions and setup routines."""

import sqlalchemy as sa
from sqlalchemy.sql import text as sql_text
from sqlalchemy.types import SMALLINT
from sqlalchemy.types import CHAR
from sqlalchemy.types import VARCHAR
from sqlalchemy.types import TEXT
from sqlalchemy.types import BOOLEAN

import logging
log = logging.getLogger(__name__)

#pylint: disable=line-too-long, too-many-lines, bad-whitespace

# [DK] we changed and removed some tables so i upgraded DB_VERSION to 18
DB_VERSION = 18

def build_metadata():
    """Build schema def with SqlAlchemy"""
    metadata = sa.MetaData()

    sa.Table(
        'hive_blocks', metadata,
        sa.Column('num', sa.Integer, primary_key=True, autoincrement=False),
        sa.Column('hash', CHAR(40), nullable=False),
        sa.Column('prev', CHAR(40)),
        sa.Column('txs', SMALLINT, server_default='0', nullable=False),
        sa.Column('ops', SMALLINT, server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),

        sa.UniqueConstraint('hash', name='hive_blocks_ux1'),
        sa.ForeignKeyConstraint(['prev'], ['hive_blocks.hash'], name='hive_blocks_fk1'),
    )

    sa.Table(
        'hive_accounts', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', VARCHAR(16, collation='C'), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        #sa.Column('block_num', sa.Integer, nullable=False),
        sa.Column('reputation', sa.Float(precision=6), nullable=False, server_default='25'),

        sa.Column('followers', sa.Integer, nullable=False, server_default='0'),
        sa.Column('following', sa.Integer, nullable=False, server_default='0'),

        sa.Column('rank', sa.Integer, nullable=False, server_default='0'),

        sa.Column('lastread_at', sa.DateTime, nullable=False, server_default='1970-01-01 00:00:00'),
        sa.Column('posting_json_metadata', sa.Text),
        sa.Column('json_metadata', sa.Text),

        sa.UniqueConstraint('name', name='hive_accounts_ux1'),
        sa.Index('hive_accounts_ix6', 'reputation')
    )

    sa.Table(
        'hive_account_reputation_status', metadata,
        sa.Column('account_id', sa.Integer, primary_key=True),
        sa.Column('reputation', sa.BigInteger, nullable=False),
        sa.Column('is_implicit', sa.Boolean, nullable=False)
    )

    sa.Table(
        'hive_reputation_data', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('author_id', sa.Integer, nullable=False),
        sa.Column('voter_id', sa.Integer, nullable=False),
        sa.Column('permlink', sa.String(255, collation='C'), nullable=False),
        sa.Column('rshares', sa.BigInteger, nullable=False),
        sa.Column('block_num', sa.Integer,  nullable=False),

        sa.Index('hive_reputation_data_author_permlink_voter_idx', 'author_id', 'permlink', 'voter_id')
    )

    sa.Table(
        'hive_posts', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('root_id', sa.Integer, nullable=False), # records having initially set 0 will be updated to their id
        sa.Column('parent_id', sa.Integer, nullable=False),
        sa.Column('author_id', sa.Integer, nullable=False),
        sa.Column('permlink_id', sa.Integer, nullable=False),
        sa.Column('category_id', sa.Integer, nullable=False),
        sa.Column('community_id', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('depth', SMALLINT, nullable=False),
        sa.Column('counter_deleted', sa.Integer, nullable=False, server_default='0'),
        sa.Column('is_pinned', BOOLEAN, nullable=False, server_default='0'),
        sa.Column('is_muted', BOOLEAN, nullable=False, server_default='0'),
        sa.Column('is_valid', BOOLEAN, nullable=False, server_default='1'),
        sa.Column('promoted', sa.types.DECIMAL(10, 3), nullable=False, server_default='0'),

        sa.Column('children', sa.Integer, nullable=False, server_default='0'),


        # core stats/indexes
        sa.Column('payout', sa.types.DECIMAL(10, 3), nullable=False, server_default='0'),
        sa.Column('pending_payout', sa.types.DECIMAL(10, 3), nullable=False, server_default='0'),
        sa.Column('payout_at', sa.DateTime, nullable=False, server_default='1970-01-01'),
        sa.Column('last_payout_at', sa.DateTime, nullable=False, server_default='1970-01-01'),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default='1970-01-01'),
        sa.Column('is_paidout', BOOLEAN, nullable=False, server_default='0'),

        # ui flags/filters
        sa.Column('is_nsfw', BOOLEAN, nullable=False, server_default='0'),
        sa.Column('is_declined', BOOLEAN, nullable=False, server_default='0'),
        sa.Column('is_full_power', BOOLEAN, nullable=False, server_default='0'),
        sa.Column('is_hidden', BOOLEAN, nullable=False, server_default='0'),
        sa.Column('is_grayed', BOOLEAN, nullable=False, server_default='0'),

        # important indexes
        sa.Column('sc_trend', sa.Float(precision=6), nullable=False, server_default='0'),
        sa.Column('sc_hot', sa.Float(precision=6), nullable=False, server_default='0'),

        sa.Column('total_payout_value', sa.String(30), nullable=False, server_default='0.000 HBD'),
        sa.Column('author_rewards', sa.BigInteger, nullable=False, server_default='0'),

        sa.Column('author_rewards_hive', sa.BigInteger, nullable=False, server_default='0'),
        sa.Column('author_rewards_hbd', sa.BigInteger, nullable=False, server_default='0'),
        sa.Column('author_rewards_vests', sa.BigInteger, nullable=False, server_default='0'),

        sa.Column('abs_rshares', sa.BigInteger, nullable=False, server_default='0'),
        sa.Column('vote_rshares', sa.BigInteger, nullable=False, server_default='0'),
        sa.Column('total_vote_weight', sa.Numeric, nullable=False, server_default='0'),
        sa.Column('active', sa.DateTime, nullable=False, server_default='1970-01-01 00:00:00'),
        sa.Column('cashout_time', sa.DateTime, nullable=False, server_default='1970-01-01 00:00:00'),
        sa.Column('percent_hbd', sa.Integer, nullable=False, server_default='10000'),

        sa.Column('curator_payout_value', sa.String(30), nullable=False, server_default='0.000 HBD'),
        sa.Column('max_accepted_payout',  sa.String(30), nullable=False, server_default='1000000.000 HBD'),
        sa.Column('allow_votes', BOOLEAN, nullable=False, server_default='1'),
        sa.Column('allow_curation_rewards', BOOLEAN, nullable=False, server_default='1'),
        sa.Column('beneficiaries', sa.JSON, nullable=False, server_default='[]'),
        sa.Column('block_num', sa.Integer,  nullable=False ),

        sa.ForeignKeyConstraint(['author_id'], ['hive_accounts.id'], name='hive_posts_fk1'),
        sa.ForeignKeyConstraint(['root_id'], ['hive_posts.id'], name='hive_posts_fk2'),
        sa.ForeignKeyConstraint(['parent_id'], ['hive_posts.id'], name='hive_posts_fk3'),
        sa.UniqueConstraint('author_id', 'permlink_id', 'counter_deleted', name='hive_posts_ux1'),

        sa.Index('hive_posts_depth_idx', 'depth'),

        sa.Index('hive_posts_root_id_id_idx', 'root_id','id'),

        sa.Index('hive_posts_parent_id_idx', 'parent_id'),
        sa.Index('hive_posts_community_id_idx', 'community_id'),

        sa.Index('hive_posts_category_id_idx', 'category_id'),
        sa.Index('hive_posts_payout_at_idx', 'payout_at'),
        sa.Index('hive_posts_payout_idx', 'payout'),
        sa.Index('hive_posts_promoted_idx', 'promoted'),
        sa.Index('hive_posts_sc_trend_idx', 'sc_trend'),
        sa.Index('hive_posts_sc_hot_idx', 'sc_hot'),
        sa.Index('hive_posts_created_at_idx', 'created_at'),
        sa.Index('hive_posts_block_num_idx', 'block_num')
    )

    sa.Table(
        'hive_post_data', metadata,
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=False),
        sa.Column('title', VARCHAR(512), nullable=False, server_default=''),
        sa.Column('preview', VARCHAR(1024), nullable=False, server_default=''), # first 1k of 'body'
        sa.Column('img_url', VARCHAR(1024), nullable=False, server_default=''), # first 'image' from 'json'
        sa.Column('body', TEXT, nullable=False, server_default=''),
        sa.Column('json', TEXT, nullable=False, server_default='')
    )

    sa.Table(
        'hive_permlink_data', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('permlink', sa.String(255, collation='C'), nullable=False),
        sa.UniqueConstraint('permlink', name='hive_permlink_data_permlink')
    )

    sa.Table(
        'hive_category_data', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('category', sa.String(255, collation='C'), nullable=False),
        sa.UniqueConstraint('category', name='hive_category_data_category')
    )

    sa.Table(
        'hive_votes', metadata,
        sa.Column('id', sa.BigInteger, primary_key=True),
        sa.Column('post_id', sa.Integer, nullable=False),
        sa.Column('voter_id', sa.Integer, nullable=False),
        sa.Column('author_id', sa.Integer, nullable=False),
        sa.Column('permlink_id', sa.Integer, nullable=False),
        sa.Column('weight', sa.Numeric, nullable=False, server_default='0'),
        sa.Column('rshares', sa.BigInteger, nullable=False, server_default='0'),
        sa.Column('vote_percent', sa.Integer, server_default='0'),
        sa.Column('last_update', sa.DateTime, nullable=False, server_default='1970-01-01 00:00:00'),
        sa.Column('num_changes', sa.Integer, server_default='0'),
        sa.Column('block_num', sa.Integer,  nullable=False ),
        sa.Column('is_effective', BOOLEAN, nullable=False, server_default='0'),

        sa.UniqueConstraint('voter_id', 'author_id', 'permlink_id', name='hive_votes_ux1'),

        sa.ForeignKeyConstraint(['post_id'], ['hive_posts.id'], name='hive_votes_fk1'),
        sa.ForeignKeyConstraint(['voter_id'], ['hive_accounts.id'], name='hive_votes_fk2'),
        sa.ForeignKeyConstraint(['author_id'], ['hive_accounts.id'], name='hive_votes_fk3'),
        sa.ForeignKeyConstraint(['permlink_id'], ['hive_permlink_data.id'], name='hive_votes_fk4'),
        sa.ForeignKeyConstraint(['block_num'], ['hive_blocks.num'], name='hive_votes_fk5'),

        sa.Index('hive_votes_post_id_idx', 'post_id'),
        sa.Index('hive_votes_voter_id_idx', 'voter_id'),
        sa.Index('hive_votes_voter_id_post_id_idx', 'voter_id', 'post_id'),
        sa.Index('hive_votes_post_id_voter_id_idx', 'post_id', 'voter_id'),
        sa.Index('hive_votes_block_num_idx', 'block_num'),
        sa.Index('hive_votes_last_update_idx', 'last_update')
    )

    sa.Table(
        'hive_tag_data', metadata,
        sa.Column('id', sa.Integer, nullable=False, primary_key=True),
        sa.Column('tag', VARCHAR(64, collation='C'), nullable=False, server_default=''),
        sa.UniqueConstraint('tag', name='hive_tag_data_ux1')
    )

    sa.Table(
        'hive_post_tags', metadata,
        sa.Column('post_id', sa.Integer, nullable=False),
        sa.Column('tag_id', sa.Integer, nullable=False),
        sa.PrimaryKeyConstraint('post_id', 'tag_id', name='hive_post_tags_pk1'),

        sa.ForeignKeyConstraint(['post_id'], ['hive_posts.id'], name='hive_post_tags_fk1'),
        sa.ForeignKeyConstraint(['tag_id'], ['hive_tag_data.id'], name='hive_post_tags_fk2'),

        sa.Index('hive_post_tags_tag_id_idx', 'tag_id')
    )

    sa.Table(
        'hive_follows', metadata,
        sa.Column('id', sa.Integer, primary_key=True ),
        sa.Column('follower', sa.Integer, nullable=False),
        sa.Column('following', sa.Integer, nullable=False),
        sa.Column('state', SMALLINT, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('blacklisted', sa.Boolean, nullable=False, server_default='0'),
        sa.Column('follow_blacklists', sa.Boolean, nullable=False, server_default='0'),
        sa.Column('block_num', sa.Integer,  nullable=False ),

        sa.UniqueConstraint('following', 'follower', name='hive_follows_ux1'), # core
        sa.ForeignKeyConstraint(['block_num'], ['hive_blocks.num'], name='hive_follows_fk1'),
        sa.Index('hive_follows_ix5a', 'following', 'state', 'created_at', 'follower'),
        sa.Index('hive_follows_ix5b', 'follower', 'state', 'created_at', 'following'),
        sa.Index('hive_follows_block_num_idx', 'block_num'),
        sa.Index('hive_follows_created_at_idx', 'created_at'),
    )

    sa.Table(
        'hive_reblogs', metadata,
        sa.Column('id', sa.Integer, primary_key=True ),
        sa.Column('blogger_id', sa.Integer, nullable=False),
        sa.Column('post_id', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('block_num', sa.Integer,  nullable=False ),

        sa.ForeignKeyConstraint(['blogger_id'], ['hive_accounts.id'], name='hive_reblogs_fk1'),
        sa.ForeignKeyConstraint(['post_id'], ['hive_posts.id'], name='hive_reblogs_fk2'),
        sa.ForeignKeyConstraint(['block_num'], ['hive_blocks.num'], name='hive_reblogs_fk3'),
        sa.UniqueConstraint('blogger_id', 'post_id', name='hive_reblogs_ux1'), # core
        sa.Index('hive_reblogs_blogger_id', 'blogger_id'),
        sa.Index('hive_reblogs_post_id', 'post_id'),
        sa.Index('hive_reblogs_block_num_idx', 'block_num'),
        sa.Index('hive_reblogs_created_at_idx', 'created_at')
    )

    sa.Table(
        'hive_payments', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('block_num', sa.Integer, nullable=False),
        sa.Column('tx_idx', SMALLINT, nullable=False),
        sa.Column('post_id', sa.Integer, nullable=False),
        sa.Column('from_account', sa.Integer, nullable=False),
        sa.Column('to_account', sa.Integer, nullable=False),
        sa.Column('amount', sa.types.DECIMAL(10, 3), nullable=False),
        sa.Column('token', VARCHAR(5), nullable=False),

        sa.ForeignKeyConstraint(['from_account'], ['hive_accounts.id'], name='hive_payments_fk1'),
        sa.ForeignKeyConstraint(['to_account'], ['hive_accounts.id'], name='hive_payments_fk2'),
        sa.ForeignKeyConstraint(['post_id'], ['hive_posts.id'], name='hive_payments_fk3'),
        sa.Index('hive_payments_from', 'from_account'),
        sa.Index('hive_payments_to', 'to_account'),
        sa.Index('hive_payments_post_id', 'post_id'),
    )

    sa.Table(
        'hive_feed_cache', metadata,
        sa.Column('post_id', sa.Integer, nullable=False),
        sa.Column('account_id', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('block_num',    sa.Integer,  nullable=True),
        sa.PrimaryKeyConstraint('account_id', 'post_id', name='hive_feed_cache_pk'),
        sa.ForeignKeyConstraint(['block_num'], ['hive_blocks.num'], name='hive_feed_cache_fk1'),
    )

    sa.Table(
        'hive_state', metadata,
        sa.Column('block_num', sa.Integer, primary_key=True, autoincrement=False),
        sa.Column('db_version', sa.Integer, nullable=False),
        sa.Column('steem_per_mvest', sa.types.DECIMAL(14, 6), nullable=False),
        sa.Column('usd_per_steem', sa.types.DECIMAL(14, 6), nullable=False),
        sa.Column('sbd_per_steem', sa.types.DECIMAL(14, 6), nullable=False),
        sa.Column('dgpo', sa.Text, nullable=False),
    )

    sa.Table(
        'hive_posts_api_helper', metadata,
        sa.Column('id', sa.Integer, primary_key=True, autoincrement = False),
        sa.Column('author', VARCHAR(16, collation='C'), nullable=False),
        sa.Column('parent_author', VARCHAR(16, collation='C'), nullable=False),
        sa.Column('parent_permlink_or_category', sa.String(255, collation='C'), nullable=False),
        sa.Index('hive_posts_api_helper_parent_permlink_or_category', 'parent_author', 'parent_permlink_or_category', 'id')
    )

    sa.Table(
        'hive_mentions', metadata,
        sa.Column('post_id', sa.Integer, nullable=False),
        sa.Column('account_id', sa.Integer, nullable=False),

        sa.PrimaryKeyConstraint('account_id', 'post_id', name='hive_mentions_pk'),
        sa.ForeignKeyConstraint(['post_id'], ['hive_posts.id'], name='hive_mentions_fk1'),
        sa.ForeignKeyConstraint(['account_id'], ['hive_accounts.id'], name='hive_mentions_fk2'),

        sa.Index('hive_mentions_post_id_idx', 'post_id'),
        sa.Index('hive_mentions_account_id_idx', 'account_id')
    )

    metadata = build_metadata_community(metadata)

    return metadata

def build_metadata_community(metadata=None):
    """Build community schema defs"""
    if not metadata:
        metadata = sa.MetaData()

    sa.Table(
        'hive_communities', metadata,
        sa.Column('id',          sa.Integer,      primary_key=True, autoincrement=False),
        sa.Column('type_id',     SMALLINT,        nullable=False),
        sa.Column('lang',        CHAR(2),         nullable=False, server_default='en'),
        sa.Column('name',        VARCHAR(16, collation='C'), nullable=False),
        sa.Column('title',       sa.String(32),   nullable=False, server_default=''),
        sa.Column('created_at',  sa.DateTime,     nullable=False),
        sa.Column('sum_pending', sa.Integer,      nullable=False, server_default='0'),
        sa.Column('num_pending', sa.Integer,      nullable=False, server_default='0'),
        sa.Column('num_authors', sa.Integer,      nullable=False, server_default='0'),
        sa.Column('rank',        sa.Integer,      nullable=False, server_default='0'),
        sa.Column('subscribers', sa.Integer,      nullable=False, server_default='0'),
        sa.Column('is_nsfw',     BOOLEAN,         nullable=False, server_default='0'),
        sa.Column('about',       sa.String(120),  nullable=False, server_default=''),
        sa.Column('primary_tag', sa.String(32),   nullable=False, server_default=''),
        sa.Column('category',    sa.String(32),   nullable=False, server_default=''),
        sa.Column('avatar_url',  sa.String(1024), nullable=False, server_default=''),
        sa.Column('description', sa.String(5000), nullable=False, server_default=''),
        sa.Column('flag_text',   sa.String(5000), nullable=False, server_default=''),
        sa.Column('settings',    TEXT,            nullable=False, server_default='{}'),
        sa.Column('block_num', sa.Integer,  nullable=False ),

        sa.UniqueConstraint('name', name='hive_communities_ux1'),
        sa.Index('hive_communities_ix1', 'rank', 'id'),
        sa.Index('hive_communities_block_num_idx', 'block_num')
    )

    sa.Table(
        'hive_roles', metadata,
        sa.Column('account_id',   sa.Integer,     nullable=False),
        sa.Column('community_id', sa.Integer,     nullable=False),
        sa.Column('created_at',   sa.DateTime,    nullable=False),
        sa.Column('role_id',      SMALLINT,       nullable=False, server_default='0'),
        sa.Column('title',        sa.String(140), nullable=False, server_default=''),

        sa.PrimaryKeyConstraint('account_id', 'community_id', name='hive_roles_pk'),
        sa.Index('hive_roles_ix1', 'community_id', 'account_id', 'role_id'),
    )

    sa.Table(
        'hive_subscriptions', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('account_id',   sa.Integer,  nullable=False),
        sa.Column('community_id', sa.Integer,  nullable=False),
        sa.Column('created_at',   sa.DateTime, nullable=False),
        sa.Column('block_num', sa.Integer,  nullable=False ),

        sa.UniqueConstraint('account_id', 'community_id', name='hive_subscriptions_ux1'),
        sa.Index('hive_subscriptions_ix1', 'community_id', 'account_id', 'created_at'),
        sa.Index('hive_subscriptions_block_num_idx', 'block_num')
    )

    sa.Table(
        'hive_notifs', metadata,
        sa.Column('id',           sa.Integer,  primary_key=True),
        sa.Column('block_num',    sa.Integer,  nullable=False),
        sa.Column('type_id',      SMALLINT,    nullable=False),
        sa.Column('score',        SMALLINT,    nullable=False),
        sa.Column('created_at',   sa.DateTime, nullable=False),
        sa.Column('src_id',       sa.Integer,  nullable=True),
        sa.Column('dst_id',       sa.Integer,  nullable=True),
        sa.Column('post_id',      sa.Integer,  nullable=True),
        sa.Column('community_id', sa.Integer,  nullable=True),
        sa.Column('block_num',    sa.Integer,  nullable=True),
        sa.Column('payload',      sa.Text,     nullable=True),

        sa.Index('hive_notifs_ix1', 'dst_id',                  'id', postgresql_where=sql_text("dst_id IS NOT NULL")),
        sa.Index('hive_notifs_ix2', 'community_id',            'id', postgresql_where=sql_text("community_id IS NOT NULL")),
        sa.Index('hive_notifs_ix3', 'community_id', 'type_id', 'id', postgresql_where=sql_text("community_id IS NOT NULL")),
        sa.Index('hive_notifs_ix4', 'community_id', 'post_id', 'type_id', 'id', postgresql_where=sql_text("community_id IS NOT NULL AND post_id IS NOT NULL")),
        sa.Index('hive_notifs_ix5', 'post_id', 'type_id', 'dst_id', 'src_id', postgresql_where=sql_text("post_id IS NOT NULL AND type_id IN (16,17)")), # filter: dedupe
        sa.Index('hive_notifs_ix6', 'dst_id', 'created_at', 'score', 'id', postgresql_where=sql_text("dst_id IS NOT NULL")), # unread
    )

    return metadata


def teardown(db):
    """Drop all tables"""
    build_metadata().drop_all(db.engine())

def drop_fk(db):
    db.query_no_return("START TRANSACTION")
    for table in build_metadata().sorted_tables:
        for fk in table.foreign_keys:
            sql = """ALTER TABLE {} DROP CONSTRAINT IF EXISTS {}""".format(table.name, fk.name)
            db.query_no_return(sql)
    db.query_no_return("COMMIT")

def create_fk(db):
    from sqlalchemy.schema import AddConstraint
    from sqlalchemy import text
    connection = db.engine().connect()
    connection.execute(text("START TRANSACTION"))
    for table in build_metadata().sorted_tables:
        for fk in table.foreign_keys:
            connection.execute(AddConstraint(fk.constraint))
    connection.execute(text("COMMIT"))

def setup(db):
    """Creates all tables and seed data"""
    # initialize schema
    build_metadata().create_all(db.engine())

    # tune auto vacuum/analyze
    reset_autovac(db)

    # sets FILLFACTOR:
    set_fillfactor(db)

    # default rows
    sqls = [
        "INSERT INTO hive_state (block_num, db_version, steem_per_mvest, usd_per_steem, sbd_per_steem, dgpo) VALUES (0, %d, 0, 0, 0, '')" % DB_VERSION,
        "INSERT INTO hive_blocks (num, hash, created_at) VALUES (0, '0000000000000000000000000000000000000000', '2016-03-24 16:04:57')",

        "INSERT INTO hive_permlink_data (id, permlink) VALUES (0, '')",
        "INSERT INTO hive_category_data (id, category) VALUES (0, '')",
        "INSERT INTO hive_accounts (id, name, created_at) VALUES (0, '', '1970-01-01T00:00:00')",

        "INSERT INTO hive_accounts (name, created_at) VALUES ('miners',    '2016-03-24 16:05:00')",
        "INSERT INTO hive_accounts (name, created_at) VALUES ('null',      '2016-03-24 16:05:00')",
        "INSERT INTO hive_accounts (name, created_at) VALUES ('temp',      '2016-03-24 16:05:00')",
        "INSERT INTO hive_accounts (name, created_at) VALUES ('initminer', '2016-03-24 16:05:00')",

        """
        INSERT INTO
            public.hive_posts(id, root_id, parent_id, author_id, permlink_id, category_id,
                community_id, created_at, depth, block_num
            )
        VALUES
            (0, 0, 0, 0, 0, 0, 0, now(), 0, 0);
        """]
    for sql in sqls:
        db.query(sql)

    sql = "CREATE INDEX hive_communities_ft1 ON hive_communities USING GIN (to_tsvector('english', title || ' ' || about))"
    db.query(sql)

    sql = """
      DROP FUNCTION IF EXISTS find_comment_id(character varying, character varying, boolean)
      ;
      CREATE OR REPLACE FUNCTION find_comment_id(
        in _author hive_accounts.name%TYPE,
        in _permlink hive_permlink_data.permlink%TYPE,
        in _check boolean)
      RETURNS INT
      LANGUAGE 'plpgsql'
      AS
      $function$
      DECLARE
        post_id INT;
      BEGIN
        SELECT INTO post_id COALESCE( (SELECT hp.id
        FROM hive_posts hp
        JOIN hive_accounts ha ON ha.id = hp.author_id
        JOIN hive_permlink_data hpd ON hpd.id = hp.permlink_id
        WHERE ha.name = _author AND hpd.permlink = _permlink AND hp.counter_deleted = 0
        ), 0 );
        IF _check AND (_author <> '' OR _permlink <> '') AND post_id = 0 THEN
          RAISE EXCEPTION 'Post %/% does not exist', _author, _permlink;
        END IF;
        RETURN post_id;
      END
      $function$
      ;
    """

    db.query_no_return(sql)

    sql = """
        DROP FUNCTION IF EXISTS find_account_id(character varying, boolean)
        ;
        CREATE OR REPLACE FUNCTION find_account_id(
          in _account hive_accounts.name%TYPE,
          in _check boolean)
        RETURNS INT
        LANGUAGE 'plpgsql'
        AS
        $function$
        DECLARE
          account_id INT;
        BEGIN
          SELECT INTO account_id COALESCE( ( SELECT id FROM hive_accounts WHERE name=_account ), 0 );
          IF _check AND account_id = 0 THEN
            RAISE EXCEPTION 'Account % does not exist', _account;
          END IF;
          RETURN account_id;
        END
        $function$
        ;
    """

    db.query_no_return(sql)

    sql = """
          DROP FUNCTION if exists process_hive_post_operation(character varying,character varying,character varying,character varying,timestamp without time zone,timestamp without time zone)
          ;
          CREATE OR REPLACE FUNCTION process_hive_post_operation(
            in _author hive_accounts.name%TYPE,
            in _permlink hive_permlink_data.permlink%TYPE,
            in _parent_author hive_accounts.name%TYPE,
            in _parent_permlink hive_permlink_data.permlink%TYPE,
            in _date hive_posts.created_at%TYPE,
            in _community_support_start_date hive_posts.created_at%TYPE,
            in _block_num hive_posts.block_num%TYPE)
          RETURNS TABLE (is_new_post boolean, id hive_posts.id%TYPE, author_id hive_posts.author_id%TYPE, permlink_id hive_posts.permlink_id%TYPE,
                         post_category hive_category_data.category%TYPE, parent_id hive_posts.parent_id%TYPE, community_id hive_posts.community_id%TYPE,
                         is_valid hive_posts.is_valid%TYPE, is_muted hive_posts.is_muted%TYPE, depth hive_posts.depth%TYPE)
          LANGUAGE plpgsql
          AS
          $function$
          BEGIN

          INSERT INTO hive_permlink_data
          (permlink)
          values
          (
          _permlink
          )
          ON CONFLICT DO NOTHING
          ;
          if _parent_author != '' THEN
            RETURN QUERY INSERT INTO hive_posts as hp
            (parent_id, depth, community_id, category_id,
             root_id, is_muted, is_valid,
             author_id, permlink_id, created_at, updated_at, sc_hot, sc_trend, active, payout_at, cashout_time, counter_deleted, block_num)
            SELECT php.id AS parent_id, php.depth + 1 AS depth,
                (CASE
                   WHEN _date > _community_support_start_date THEN
                     COALESCE(php.community_id, (select hc.id from hive_communities hc where hc.name = _parent_permlink))
                   ELSE NULL
                END) AS community_id,
                COALESCE(php.category_id, (select hcg.id from hive_category_data hcg where hcg.category = _parent_permlink)) AS category_id,
                (CASE(php.root_id)
                   WHEN 0 THEN php.id
                   ELSE php.root_id
                 END) AS root_id,
                php.is_muted AS is_muted, php.is_valid AS is_valid,
                ha.id AS author_id, hpd.id AS permlink_id, _date AS created_at,
                _date AS updated_at,
                calculate_time_part_of_hot(_date) AS sc_hot,
                calculate_time_part_of_trending(_date) AS sc_trend,
                _date AS active, (_date + INTERVAL '7 days') AS payout_at, (_date + INTERVAL '7 days') AS cashout_time, 0, _block_num as block_num
            FROM hive_accounts ha,
                 hive_permlink_data hpd,
                 hive_posts php
            INNER JOIN hive_accounts pha ON pha.id = php.author_id
            INNER JOIN hive_permlink_data phpd ON phpd.id = php.permlink_id
            WHERE pha.name = _parent_author AND phpd.permlink = _parent_permlink AND
                   ha.name = _author AND hpd.permlink = _permlink AND php.counter_deleted = 0

            ON CONFLICT ON CONSTRAINT hive_posts_ux1 DO UPDATE SET
              --- During post update it is disallowed to change: parent-post, category, community-id
              --- then also depth, is_valid and is_muted is impossible to change
             --- post edit part
             updated_at = _date,
             active = _date
            RETURNING (xmax = 0) as is_new_post, hp.id, hp.author_id, hp.permlink_id, (SELECT hcd.category FROM hive_category_data hcd WHERE hcd.id = hp.category_id) as post_category, hp.parent_id, hp.community_id, hp.is_valid, hp.is_muted, hp.depth
          ;
          ELSE
            INSERT INTO hive_category_data
            (category)
            VALUES (_parent_permlink)
            ON CONFLICT (category) DO NOTHING
            ;

            RETURN QUERY INSERT INTO hive_posts as hp
            (parent_id, depth, community_id, category_id,
             root_id, is_muted, is_valid,
             author_id, permlink_id, created_at, updated_at, sc_hot, sc_trend, active, payout_at, cashout_time, counter_deleted, block_num)
            SELECT 0 AS parent_id, 0 AS depth,
                (CASE
                  WHEN _date > _community_support_start_date THEN
                    (select hc.id FROM hive_communities hc WHERE hc.name = _parent_permlink)
                  ELSE NULL
                END) AS community_id,
                (SELECT hcg.id FROM hive_category_data hcg WHERE hcg.category = _parent_permlink) AS category_id,
                0 as root_id, -- will use id as root one if no parent
                false AS is_muted, true AS is_valid,
                ha.id AS author_id, hpd.id AS permlink_id, _date AS created_at,
                _date AS updated_at,
                calculate_time_part_of_hot(_date) AS sc_hot,
                calculate_time_part_of_trending(_date) AS sc_trend,
                _date AS active, (_date + INTERVAL '7 days') AS payout_at, (_date + INTERVAL '7 days') AS cashout_time, 0, _block_num as block_num
            FROM hive_accounts ha,
                 hive_permlink_data hpd
            WHERE ha.name = _author and hpd.permlink = _permlink

            ON CONFLICT ON CONSTRAINT hive_posts_ux1 DO UPDATE SET
              --- During post update it is disallowed to change: parent-post, category, community-id
              --- then also depth, is_valid and is_muted is impossible to change
              --- post edit part
              updated_at = _date,
              active = _date,
              block_num = _block_num

            RETURNING (xmax = 0) as is_new_post, hp.id, hp.author_id, hp.permlink_id, _parent_permlink as post_category, hp.parent_id, hp.community_id, hp.is_valid, hp.is_muted, hp.depth
            ;
          END IF;
          END
          $function$
    """
    db.query_no_return(sql)

    sql = """
          DROP FUNCTION if exists delete_hive_post(character varying,character varying,character varying)
          ;
          CREATE OR REPLACE FUNCTION delete_hive_post(
            in _author hive_accounts.name%TYPE,
            in _permlink hive_permlink_data.permlink%TYPE)
          RETURNS TABLE (id hive_posts.id%TYPE, depth hive_posts.depth%TYPE)
          LANGUAGE plpgsql
          AS
          $function$
          BEGIN
            RETURN QUERY UPDATE hive_posts AS hp
              SET counter_deleted =
              (
                SELECT max( hps.counter_deleted ) + 1
                FROM hive_posts hps
                INNER JOIN hive_accounts ha ON hps.author_id = ha.id
                INNER JOIN hive_permlink_data hpd ON hps.permlink_id = hpd.id
                WHERE ha.name = _author AND hpd.permlink = _permlink
              )
            FROM hive_posts hp1
            INNER JOIN hive_accounts ha ON hp1.author_id = ha.id
            INNER JOIN hive_permlink_data hpd ON hp1.permlink_id = hpd.id
            WHERE hp.id = hp1.id AND ha.name = _author AND hpd.permlink = _permlink AND hp1.counter_deleted = 0
            RETURNING hp.id, hp.depth;
          END
          $function$
          """
    db.query_no_return(sql)

    # In original hivemind, a value of 'active_at' was calculated from
    # max
    #   {
    #     created             ( account_create_operation ),
    #     last_account_update ( account_update_operation/account_update2_operation ),
    #     last_post           ( comment_operation - only creation )
    #     last_root_post      ( comment_operation - only creation + only ROOT ),
    #     last_vote_time      ( vote_operation )
    #   }
    # In order to simplify calculations, `last_account_update` is not taken into consideration, because this updating accounts is very rare
    # and posting/voting after an account updating, fixes `active_at` value immediately.

    sql = """
        DROP VIEW IF EXISTS public.hive_accounts_info_view;

        CREATE OR REPLACE VIEW public.hive_accounts_info_view
        AS
        SELECT
          id,
          name,
          (
            select count(*) post_count
            FROM hive_posts hp
            WHERE ha.id=hp.author_id
          ) post_count,
          created_at,
          (
            SELECT GREATEST
            (
              created_at,
              COALESCE(
                (
                  select max(hp.created_at)
                  FROM hive_posts hp
                  WHERE ha.id=hp.author_id
                ),
                '1970-01-01 00:00:00.0'
              ),
              COALESCE(
                (
                  select max(hv.last_update)
                  from hive_votes hv
                  WHERE ha.id=hv.voter_id
                ),
                '1970-01-01 00:00:00.0'
              )
            )
          ) active_at,
          reputation,
          rank,
          following,
          followers,
          lastread_at,
          posting_json_metadata,
          json_metadata
        FROM
          hive_accounts ha
          """
    db.query_no_return(sql)

    sql = """
        DROP VIEW IF EXISTS public.hive_posts_view;

        CREATE OR REPLACE VIEW public.hive_posts_view
        AS
        SELECT hp.id,
          hp.community_id,
          hp.root_id,
          hp.parent_id,
          ha_a.name AS author,
          hp.active,
          hp.author_rewards,
          hp.author_id,
          hpd_p.permlink,
          hpd.title,
          hpd.body,
          hpd.img_url,
          hpd.preview,
          hcd.category,
          hp.depth,
          hp.promoted,
          hp.payout,
          hp.pending_payout,
          hp.payout_at,
          hp.last_payout_at,
          hp.cashout_time,
          hp.is_paidout,
          hp.children,
          0 AS votes,
          0 AS active_votes,
          hp.created_at,
          hp.updated_at,
            COALESCE(
              (
                SELECT SUM( v.rshares )
                FROM hive_votes v
                WHERE v.post_id = hp.id
                GROUP BY v.post_id
              ), 0
            ) AS rshares,
            COALESCE(
              (
                SELECT SUM( CASE v.rshares >= 0 WHEN True THEN v.rshares ELSE -v.rshares END )
                FROM hive_votes v
                WHERE v.post_id = hp.id AND NOT v.rshares = 0
                GROUP BY v.post_id
              ), 0
            ) AS abs_rshares,
            COALESCE(
              (
                SELECT COUNT( 1 )
                FROM hive_votes v
                WHERE v.post_id = hp.id AND v.is_effective
                GROUP BY v.post_id
              ), 0
            ) AS total_votes,
            COALESCE(
              (
                SELECT SUM( CASE v.rshares > 0 WHEN True THEN 1 ELSE -1 END )
                FROM hive_votes v
                WHERE v.post_id = hp.id AND NOT v.rshares = 0
                GROUP BY v.post_id
              ), 0
            ) AS net_votes,
          hpd.json,
          ha_a.reputation AS author_rep,
          hp.is_hidden,
          hp.is_grayed,
          hp.total_vote_weight,
          ha_pp.name AS parent_author,
          ha_pp.id AS parent_author_id,
            ( CASE hp.depth > 0
              WHEN True THEN hpd_pp.permlink
              ELSE hcd.category
            END ) AS parent_permlink_or_category,
          hp.curator_payout_value,
          ha_rp.name AS root_author,
          hpd_rp.permlink AS root_permlink,
          rcd.category as root_category,
          hp.max_accepted_payout,
          hp.percent_hbd,
            True AS allow_replies,
          hp.allow_votes,
          hp.allow_curation_rewards,
          hp.beneficiaries,
            CONCAT('/', rcd.category, '/@', ha_rp.name, '/', hpd_rp.permlink,
              CASE (rp.id)
                WHEN hp.id THEN ''
                ELSE CONCAT('#@', ha_a.name, '/', hpd_p.permlink)
              END
            ) AS url,
          rpd.title AS root_title,
          hp.sc_trend,
          hp.sc_hot,
          hp.is_pinned,
          hp.is_muted,
          hp.is_nsfw,
          hp.is_valid,
          hr.title AS role_title,
          hr.role_id AS role_id,
          hc.title AS community_title,
          hc.name AS community_name,
          hp.block_num
          FROM hive_posts hp
            JOIN hive_posts pp ON pp.id = hp.parent_id
            JOIN hive_posts rp ON rp.id = hp.root_id
            JOIN hive_accounts ha_a ON ha_a.id = hp.author_id
            JOIN hive_permlink_data hpd_p ON hpd_p.id = hp.permlink_id
            JOIN hive_post_data hpd ON hpd.id = hp.id
            JOIN hive_accounts ha_pp ON ha_pp.id = pp.author_id
            JOIN hive_permlink_data hpd_pp ON hpd_pp.id = pp.permlink_id
            JOIN hive_accounts ha_rp ON ha_rp.id = rp.author_id
            JOIN hive_permlink_data hpd_rp ON hpd_rp.id = rp.permlink_id
            JOIN hive_post_data rpd ON rpd.id = rp.id
            JOIN hive_category_data hcd ON hcd.id = hp.category_id
            JOIN hive_category_data rcd ON rcd.id = rp.category_id
            LEFT JOIN hive_communities hc ON hp.community_id = hc.id
            LEFT JOIN hive_roles hr ON hp.author_id = hr.account_id AND hp.community_id = hr.community_id
          WHERE hp.counter_deleted = 0;
          """
    db.query_no_return(sql)

    sql = """
          DROP FUNCTION IF EXISTS public.update_hive_posts_root_id(INTEGER, INTEGER);

          CREATE OR REPLACE FUNCTION public.update_hive_posts_root_id(in _first_block_num INTEGER, _last_block_num INTEGER)
              RETURNS void
              LANGUAGE 'plpgsql'
              VOLATILE
          AS $BODY$
          BEGIN

          --- _first_block_num can be null together with _last_block_num
          UPDATE hive_posts uhp
          SET root_id = id
          WHERE uhp.root_id = 0 AND (_first_block_num IS NULL OR (uhp.block_num >= _first_block_num AND uhp.block_num <= _last_block_num))
          ;
          END
          $BODY$;
          """
    db.query_no_return(sql)

    sql = """
          DROP FUNCTION IF EXISTS public.update_hive_posts_children_count(INTEGER, INTEGER);

          CREATE OR REPLACE FUNCTION public.update_hive_posts_children_count(in _first_block INTEGER, in _last_block INTEGER)
              RETURNS void
              LANGUAGE SQL
              VOLATILE
          AS $BODY$
          UPDATE hive_posts uhp
          SET children = data_source.children_count
          FROM
          (
            WITH recursive tblChild AS
            (
              SELECT s.queried_parent, s.id
              FROM
              (SELECT h1.Parent_Id AS queried_parent, h1.id
               FROM hive_posts h1
               WHERE h1.depth > 0 AND h1.counter_deleted = 0
                     AND h1.block_num BETWEEN _first_block AND _last_block
               ORDER BY h1.depth DESC
              ) s
              UNION ALL
              SELECT tblChild.queried_parent, p.id FROM hive_posts p
              JOIN tblChild  ON p.Parent_Id = tblChild.Id
              WHERE p.counter_deleted = 0
            )
            SELECT queried_parent, cast(count(1) AS int) AS children_count
            FROM tblChild
            GROUP BY queried_parent
          ) data_source
          WHERE uhp.id = data_source.queried_parent
          ;
          $BODY$;
          """
    db.query_no_return(sql)

    sql = """
        DROP VIEW IF EXISTS hive_votes_view
        ;
        CREATE OR REPLACE VIEW hive_votes_view
        AS
        SELECT
            hv.id,
            hv.voter_id as voter_id,
            ha_a.name as author,
            hpd.permlink as permlink,
            vote_percent as percent,
            ha_a.reputation as reputation,
            rshares,
            last_update,
            ha_v.name as voter,
            weight,
            num_changes,
            hv.permlink_id as permlink_id,
            post_id,
            is_effective
        FROM
            hive_votes hv
        INNER JOIN hive_accounts ha_v ON ha_v.id = hv.voter_id
        INNER JOIN hive_accounts ha_a ON ha_a.id = hv.author_id
        INNER JOIN hive_permlink_data hpd ON hpd.id = hv.permlink_id
        ;
    """
    db.query_no_return(sql)

    sql = """
        DROP TYPE IF EXISTS database_api_vote CASCADE;

        CREATE TYPE database_api_vote AS (
          id BIGINT,
          voter VARCHAR(16),
          author VARCHAR(16),
          permlink VARCHAR(255),
          weight NUMERIC,
          rshares BIGINT,
          percent INT,
          last_update TIMESTAMP,
          num_changes INT,
          reputation FLOAT4
        );

        DROP FUNCTION IF EXISTS find_votes( character varying, character varying )
        ;
        CREATE OR REPLACE FUNCTION public.find_votes
        (
          in _AUTHOR hive_accounts.name%TYPE,
          in _PERMLINK hive_permlink_data.permlink%TYPE
        )
        RETURNS SETOF database_api_vote
        LANGUAGE 'plpgsql'
        AS
        $function$
        DECLARE _POST_ID INT;
        BEGIN
        _POST_ID = find_comment_id( _AUTHOR, _PERMLINK, True);

        RETURN QUERY
        (
            SELECT
                v.id,
                v.voter,
                v.author,
                v.permlink,
                v.weight,
                v.rshares,
                v.percent,
                v.last_update,
                v.num_changes,
                v.reputation
            FROM
                hive_votes_view v
            WHERE
                v.post_id = _POST_ID
            ORDER BY
                voter_id
        );

        END
        $function$;

        DROP FUNCTION IF EXISTS list_votes_by_voter_comment( character varying, character varying, character varying, int )
        ;
        CREATE OR REPLACE FUNCTION public.list_votes_by_voter_comment
        (
          in _VOTER hive_accounts.name%TYPE,
          in _AUTHOR hive_accounts.name%TYPE,
          in _PERMLINK hive_permlink_data.permlink%TYPE,
          in _LIMIT INT
        )
        RETURNS SETOF database_api_vote
        LANGUAGE 'plpgsql'
        AS
        $function$
        DECLARE __voter_id INT;
        DECLARE __post_id INT;
        BEGIN

        __voter_id = find_account_id( _VOTER, True );
        __post_id = find_comment_id( _AUTHOR, _PERMLINK, True );

        RETURN QUERY
        (
            SELECT
                v.id,
                v.voter,
                v.author,
                v.permlink,
                v.weight,
                v.rshares,
                v.percent,
                v.last_update,
                v.num_changes,
                v.reputation
            FROM
                hive_votes_view v
            WHERE
                v.voter_id = __voter_id
                AND v.post_id >= __post_id
            ORDER BY
                v.post_id
            LIMIT _LIMIT
        );

        END
        $function$;

        DROP FUNCTION IF EXISTS list_votes_by_comment_voter( character varying, character varying, character varying, int )
        ;
        CREATE OR REPLACE FUNCTION public.list_votes_by_comment_voter
        (
          in _VOTER hive_accounts.name%TYPE,
          in _AUTHOR hive_accounts.name%TYPE,
          in _PERMLINK hive_permlink_data.permlink%TYPE,
          in _LIMIT INT
        )
        RETURNS SETOF database_api_vote
        LANGUAGE 'plpgsql'
        AS
        $function$
        DECLARE __voter_id INT;
        DECLARE __post_id INT;
        BEGIN

        __voter_id = find_account_id( _VOTER, _VOTER != '' ); -- voter is optional
        __post_id = find_comment_id( _AUTHOR, _PERMLINK, True );

        RETURN QUERY
        (
            SELECT
                v.id,
                v.voter,
                v.author,
                v.permlink,
                v.weight,
                v.rshares,
                v.percent,
                v.last_update,
                v.num_changes,
                v.reputation
            FROM
                hive_votes_view v
            WHERE
                v.post_id = __post_id
                AND v.voter_id >= __voter_id
            ORDER BY
                v.voter_id
            LIMIT _LIMIT
        );

        END
        $function$;
    """
    db.query_no_return(sql)

    sql = """
      DROP TYPE IF EXISTS database_api_post CASCADE;
      CREATE TYPE database_api_post AS (
        id INT,
        community_id INT,
        author VARCHAR(16),
        permlink VARCHAR(255),
        title VARCHAR(512),
        body TEXT,
        category VARCHAR(255),
        depth SMALLINT,
        promoted DECIMAL(10,3),
        payout DECIMAL(10,3),
        last_payout_at TIMESTAMP,
        cashout_time TIMESTAMP,
        is_paidout BOOLEAN,
        children INT,
        votes INT,
        created_at TIMESTAMP,
        updated_at TIMESTAMP,
        rshares NUMERIC,
        json TEXT,
        is_hidden BOOLEAN,
        is_grayed BOOLEAN,
        total_votes BIGINT,
        net_votes BIGINT,
        total_vote_weight NUMERIC,
        parent_author VARCHAR(16),
        parent_permlink_or_category VARCHAR(255),
        curator_payout_value VARCHAR(30),
        root_author VARCHAR(16),
        root_permlink VARCHAR(255),
        max_accepted_payout VARCHAR(30),
        percent_hbd INT,
        allow_replies BOOLEAN,
        allow_votes BOOLEAN,
        allow_curation_rewards BOOLEAN,
        beneficiaries JSON,
        url TEXT,
        root_title VARCHAR(512),
        abs_rshares NUMERIC,
        active TIMESTAMP,
        author_rewards BIGINT
      )
      ;

      DROP FUNCTION IF EXISTS list_comments_by_cashout_time(timestamp, character varying, character varying, int)
      ;
      CREATE OR REPLACE FUNCTION list_comments_by_cashout_time(
        in _cashout_time timestamp,
        in _author hive_accounts.name%TYPE,
        in _permlink hive_permlink_data.permlink%TYPE,
        in _limit INT)
        RETURNS SETOF database_api_post
        AS
        $function$
        DECLARE
          __post_id INT;
        BEGIN
          __post_id = find_comment_id(_author,_permlink, True);
          RETURN QUERY
          SELECT
              hp.id, hp.community_id, hp.author, hp.permlink, hp.title, hp.body,
              hp.category, hp.depth, hp.promoted, hp.payout, hp.last_payout_at, hp.cashout_time, hp.is_paidout,
              hp.children, hp.votes, hp.created_at, hp.updated_at, hp.rshares, hp.json,
              hp.is_hidden, hp.is_grayed, hp.total_votes, hp.net_votes, hp.total_vote_weight,
              hp.parent_author, hp.parent_permlink_or_category, hp.curator_payout_value, hp.root_author, hp.root_permlink,
              hp.max_accepted_payout, hp.percent_hbd, hp.allow_replies, hp.allow_votes,
              hp.allow_curation_rewards, hp.beneficiaries, hp.url, hp.root_title, hp.abs_rshares,
              hp.active, hp.author_rewards
          FROM
              hive_posts_view hp
          INNER JOIN
          (
              SELECT 
                  hp1.id
              FROM 
                  hive_posts hp1
              WHERE
                  hp1.counter_deleted = 0
                  AND NOT hp1.is_muted
                  AND hp1.cashout_time > _cashout_time
                  OR hp1.cashout_time = _cashout_time
                  AND hp1.id >= __post_id AND hp1.id != 0
              ORDER BY
                  hp1.cashout_time ASC,
                  hp1.id ASC
              LIMIT
                  _limit
          ) ds ON ds.id = hp.id
          ORDER BY
              hp.cashout_time ASC,
              hp.id ASC
          ;
        END
        $function$
        LANGUAGE plpgsql
      ;

      DROP FUNCTION IF EXISTS list_comments_by_permlink(character varying, character varying, int)
      ;
      CREATE OR REPLACE FUNCTION list_comments_by_permlink(
        in _author hive_accounts.name%TYPE,
        in _permlink hive_permlink_data.permlink%TYPE,
        in _limit INT)
        RETURNS SETOF database_api_post
        LANGUAGE sql
        STABLE
        AS
        $function$
          SELECT
              hp.id, hp.community_id, hp.author, hp.permlink, hp.title, hp.body,
              hp.category, hp.depth, hp.promoted, hp.payout, hp.last_payout_at, hp.cashout_time, hp.is_paidout,
              hp.children, hp.votes, hp.created_at, hp.updated_at, hp.rshares, hp.json,
              hp.is_hidden, hp.is_grayed, hp.total_votes, hp.net_votes, hp.total_vote_weight,
              hp.parent_author, hp.parent_permlink_or_category, hp.curator_payout_value, hp.root_author, hp.root_permlink,
              hp.max_accepted_payout, hp.percent_hbd, hp.allow_replies, hp.allow_votes,
              hp.allow_curation_rewards, hp.beneficiaries, hp.url, hp.root_title, hp.abs_rshares,
              hp.active, hp.author_rewards
          FROM
              hive_posts_view hp
          INNER JOIN
          (
              SELECT hp1.id
              FROM
                  hive_posts hp1
              INNER JOIN hive_accounts ha ON ha.id = hp1.author_id
              INNER JOIN hive_permlink_data hpd ON hpd.id = hp1.permlink_id
              WHERE
                  hp1.counter_deleted = 0
                  AND NOT hp1.is_muted
                  AND ha.name > _author
                  OR ha.name = _author
                  AND hpd.permlink >= _permlink
                  AND hp1.id != 0
              ORDER BY
                  ha.name ASC,
                  hpd.permlink ASC
              LIMIT
                  _limit
          ) ds ON ds.id = hp.id
          ORDER BY
              hp.author ASC,
              hp.permlink ASC
        $function$
      ;


      DROP FUNCTION IF EXISTS list_comments_by_root(character varying, character varying, character varying, character varying, int)
      ;
      CREATE OR REPLACE FUNCTION list_comments_by_root(
        in _root_author hive_accounts.name%TYPE,
        in _root_permlink hive_permlink_data.permlink%TYPE,
        in _start_post_author hive_accounts.name%TYPE,
        in _start_post_permlink hive_permlink_data.permlink%TYPE,
        in _limit INT)
        RETURNS SETOF database_api_post
        AS
        $function$
        DECLARE
          __root_id INT;
          __post_id INT;
        BEGIN
          __root_id = find_comment_id(_root_author, _root_permlink, True);
          __post_id = find_comment_id(_start_post_author, _start_post_permlink, True);
          RETURN QUERY
          SELECT
            hp.id, hp.community_id, hp.author, hp.permlink, hp.title, hp.body,
            hp.category, hp.depth, hp.promoted, hp.payout, hp.last_payout_at, hp.cashout_time, hp.is_paidout,
            hp.children, hp.votes, hp.created_at, hp.updated_at, hp.rshares, hp.json,
            hp.is_hidden, hp.is_grayed, hp.total_votes, hp.net_votes, hp.total_vote_weight,
            hp.parent_author, hp.parent_permlink_or_category, hp.curator_payout_value, hp.root_author, hp.root_permlink,
            hp.max_accepted_payout, hp.percent_hbd, hp.allow_replies, hp.allow_votes,
            hp.allow_curation_rewards, hp.beneficiaries, hp.url, hp.root_title, hp.abs_rshares,
            hp.active, hp.author_rewards
          FROM 
            hive_posts_view hp
          INNER JOIN
          (
            SELECT 
              hp2.id
            FROM 
              hive_posts hp2
            WHERE
              hp2.counter_deleted = 0
              AND NOT hp2.is_muted
              AND hp2.root_id = __root_id
              AND hp2.id >= __post_id
            ORDER BY
              hp2.id ASC
            LIMIT _limit
          ) ds on hp.id = ds.id
          ORDER BY
            hp.id
          ;
        END
        $function$
        LANGUAGE plpgsql
      ;

      DROP FUNCTION IF EXISTS list_comments_by_parent(character varying, character varying, character varying, character varying, int)
      ;
      CREATE OR REPLACE FUNCTION list_comments_by_parent(
        in _parent_author hive_accounts.name%TYPE,
        in _parent_permlink hive_permlink_data.permlink%TYPE,
        in _start_post_author hive_accounts.name%TYPE,
        in _start_post_permlink hive_permlink_data.permlink%TYPE,
        in _limit INT)
        RETURNS SETOF database_api_post
      AS $function$
      DECLARE
        __post_id INT;
        __parent_id INT;
      BEGIN
        __parent_id = find_comment_id(_parent_author, _parent_permlink, True);
        __post_id = find_comment_id(_start_post_author, _start_post_permlink, True);
        RETURN QUERY
        SELECT
          hp.id, hp.community_id, hp.author, hp.permlink, hp.title, hp.body,
          hp.category, hp.depth, hp.promoted, hp.payout, hp.last_payout_at, hp.cashout_time, hp.is_paidout,
          hp.children, hp.votes, hp.created_at, hp.updated_at, hp.rshares, hp.json,
          hp.is_hidden, hp.is_grayed, hp.total_votes, hp.net_votes, hp.total_vote_weight,
          hp.parent_author, hp.parent_permlink_or_category, hp.curator_payout_value, hp.root_author, hp.root_permlink,
          hp.max_accepted_payout, hp.percent_hbd, hp.allow_replies, hp.allow_votes,
          hp.allow_curation_rewards, hp.beneficiaries, hp.url, hp.root_title, hp.abs_rshares,
          hp.active, hp.author_rewards
        FROM
          hive_posts_view hp
        INNER JOIN
        (
          SELECT hp1.id FROM
            hive_posts hp1
          WHERE
            hp1.counter_deleted = 0
            AND NOT hp1.is_muted
            AND hp1.parent_id = __parent_id
            AND hp1.id >= __post_id
          ORDER BY
            hp1.id ASC
          LIMIT
            _limit
        ) ds ON ds.id = hp.id
        ORDER BY
          hp.id
        ;
      END
      $function$
      LANGUAGE plpgsql
      ;

      DROP FUNCTION IF EXISTS list_comments_by_last_update(character varying, timestamp, character varying, character varying, int)
      ;
      CREATE OR REPLACE FUNCTION list_comments_by_last_update(
        in _parent_author hive_accounts.name%TYPE,
        in _updated_at hive_posts.updated_at%TYPE,
        in _start_post_author hive_accounts.name%TYPE,
        in _start_post_permlink hive_permlink_data.permlink%TYPE,
        in _limit INT)
        RETURNS SETOF database_api_post
        AS
        $function$
        DECLARE
          __post_id INT;
          __parent_author_id INT;
        BEGIN
          __parent_author_id = find_account_id(_parent_author, True);
          __post_id = find_comment_id(_start_post_author, _start_post_permlink, True);
          RETURN QUERY
          SELECT
              hp.id, hp.community_id, hp.author, hp.permlink, hp.title, hp.body,
              hp.category, hp.depth, hp.promoted, hp.payout, hp.last_payout_at, hp.cashout_time, hp.is_paidout,
              hp.children, hp.votes, hp.created_at, hp.updated_at, hp.rshares, hp.json,
              hp.is_hidden, hp.is_grayed, hp.total_votes, hp.net_votes, hp.total_vote_weight,
              hp.parent_author, hp.parent_permlink_or_category, hp.curator_payout_value, hp.root_author, hp.root_permlink,
              hp.max_accepted_payout, hp.percent_hbd, hp.allow_replies, hp.allow_votes,
              hp.allow_curation_rewards, hp.beneficiaries, hp.url, hp.root_title, hp.abs_rshares,
              hp.active, hp.author_rewards
          FROM
              hive_posts_view hp
          INNER JOIN
          (
              SELECT
                hp1.id
              FROM
                hive_posts hp1
              JOIN
                hive_posts hp2 ON hp1.parent_id = hp2.id
              WHERE
                hp1.counter_deleted = 0
                AND NOT hp1.is_muted
                AND hp2.author_id = __parent_author_id
                AND (
                  hp1.updated_at < _updated_at
                  OR hp1.updated_at = _updated_at
                  AND hp1.id >= __post_id
                )
              ORDER BY
                hp1.updated_at DESC,
                hp1.id ASC
              LIMIT
                _limit
          ) ds ON ds.id = hp.id
          ORDER BY
            hp.updated_at DESC,
            hp.id ASC
          ;
        END
        $function$
        LANGUAGE plpgsql
      ;

      DROP FUNCTION IF EXISTS list_comments_by_author_last_update(character varying, timestamp, character varying, character varying, int)
      ;
      CREATE OR REPLACE FUNCTION list_comments_by_author_last_update(
        in _author hive_accounts.name%TYPE,
        in _updated_at hive_posts.updated_at%TYPE,
        in _start_post_author hive_accounts.name%TYPE,
        in _start_post_permlink hive_permlink_data.permlink%TYPE,
        in _limit INT)
        RETURNS SETOF database_api_post
        AS
        $function$
        DECLARE
          __author_id INT;
          __post_id INT;
        BEGIN
          __author_id = find_account_id(_author, True);
          __post_id = find_comment_id(_start_post_author, _start_post_permlink, True);
          RETURN QUERY
          SELECT
              hp.id, hp.community_id, hp.author, hp.permlink, hp.title, hp.body,
              hp.category, hp.depth, hp.promoted, hp.payout, hp.last_payout_at, hp.cashout_time, hp.is_paidout,
              hp.children, hp.votes, hp.created_at, hp.updated_at, hp.rshares, hp.json,
              hp.is_hidden, hp.is_grayed, hp.total_votes, hp.net_votes, hp.total_vote_weight,
              hp.parent_author, hp.parent_permlink_or_category, hp.curator_payout_value, hp.root_author, hp.root_permlink,
              hp.max_accepted_payout, hp.percent_hbd, hp.allow_replies, hp.allow_votes,
              hp.allow_curation_rewards, hp.beneficiaries, hp.url, hp.root_title, hp.abs_rshares,
              hp.active, hp.author_rewards
          FROM
              hive_posts_view hp
          INNER JOIN
          (
            SELECT 
              hp1.id
            FROM
              hive_posts hp1
            WHERE
              hp1.counter_deleted = 0
              AND NOT hp1.is_muted
              AND hp1.author_id = __author_id
              AND (
                hp1.updated_at < _updated_at
                OR hp1.updated_at = _updated_at
                AND hp1.id >= __post_id
              )
            ORDER BY
              hp1.updated_at DESC,
              hp1.id ASC
            LIMIT
              _limit
          ) ds ON ds.id = hp.id
          ORDER BY
              hp.updated_at DESC,
              hp.id ASC
          ;
        END
        $function$
        LANGUAGE plpgsql
      ;
    """

    db.query_no_return(sql)

    sql = """
        DROP VIEW IF EXISTS hive_accounts_rank_view CASCADE
        ;
        CREATE VIEW hive_accounts_rank_view
        AS
        SELECT
            ha.id as id
          , CASE
                 WHEN rank.position < 200 THEN 70
                 WHEN rank.position < 1000 THEN 60
                 WHEN rank.position < 6500 THEN 50
                 WHEN rank.position < 25000 THEN 40
                 WHEN rank.position < 100000 THEN 30
                 ELSE 20
             END as score
        FROM hive_accounts ha
        JOIN (
        SELECT ha2.id, RANK () OVER ( ORDER BY ha2.reputation DESC ) as position FROM hive_accounts ha2
        ) as rank ON ha.id = rank.id
    """
    db.query_no_return(sql)

    # hot and tranding functions

    sql = """
       DROP FUNCTION IF EXISTS date_diff() CASCADE
       ;
       CREATE OR REPLACE FUNCTION date_diff (units VARCHAR(30), start_t TIMESTAMP, end_t TIMESTAMP)
         RETURNS INT AS $$
       DECLARE
         diff_interval INTERVAL;
         diff INT = 0;
         years_diff INT = 0;
       BEGIN
         IF units IN ('yy', 'yyyy', 'year', 'mm', 'm', 'month') THEN
           years_diff = DATE_PART('year', end_t) - DATE_PART('year', start_t);
           IF units IN ('yy', 'yyyy', 'year') THEN
             -- SQL Server does not count full years passed (only difference between year parts)
             RETURN years_diff;
           ELSE
             -- If end month is less than start month it will subtracted
             RETURN years_diff * 12 + (DATE_PART('month', end_t) - DATE_PART('month', start_t));
           END IF;
         END IF;
         -- Minus operator returns interval 'DDD days HH:MI:SS'
         diff_interval = end_t - start_t;
         diff = diff + DATE_PART('day', diff_interval);
         IF units IN ('wk', 'ww', 'week') THEN
           diff = diff/7;
           RETURN diff;
         END IF;
         IF units IN ('dd', 'd', 'day') THEN
           RETURN diff;
         END IF;
         diff = diff * 24 + DATE_PART('hour', diff_interval);
         IF units IN ('hh', 'hour') THEN
            RETURN diff;
         END IF;
         diff = diff * 60 + DATE_PART('minute', diff_interval);
         IF units IN ('mi', 'n', 'minute') THEN
            RETURN diff;
         END IF;
         diff = diff * 60 + DATE_PART('second', diff_interval);
         RETURN diff;
       END;
       $$ LANGUAGE plpgsql IMMUTABLE
    """
    db.query_no_return(sql)

    sql = """
          DROP FUNCTION IF EXISTS public.calculate_time_part_of_trending(_post_created_at hive_posts.created_at%TYPE ) CASCADE
          ;
          CREATE OR REPLACE FUNCTION public.calculate_time_part_of_trending(
            _post_created_at hive_posts.created_at%TYPE)
              RETURNS double precision
              LANGUAGE 'plpgsql'
              IMMUTABLE
          AS $BODY$
          DECLARE
            result double precision;
            sec_from_epoch INT = 0;
          BEGIN
            sec_from_epoch  = date_diff( 'second', CAST('19700101' AS TIMESTAMP), _post_created_at );
            result = sec_from_epoch/240000.0;
            return result;
          END;
          $BODY$;
    """
    db.query_no_return(sql)

    sql = """
            DROP FUNCTION IF EXISTS public.calculate_time_part_of_hot(_post_created_at hive_posts.created_at%TYPE ) CASCADE
            ;
            CREATE OR REPLACE FUNCTION public.calculate_time_part_of_hot(
              _post_created_at hive_posts.created_at%TYPE)
                RETURNS double precision
                LANGUAGE 'plpgsql'
                IMMUTABLE
            AS $BODY$
            DECLARE
              result double precision;
              sec_from_epoch INT = 0;
            BEGIN
              sec_from_epoch  = date_diff( 'second', CAST('19700101' AS TIMESTAMP), _post_created_at );
              result = sec_from_epoch/10000.0;
              return result;
            END;
            $BODY$;
    """
    db.query_no_return(sql)

    sql = """
    DROP FUNCTION IF EXISTS public.calculate_rhsares_part_of_hot_and_trend(_rshares hive_votes.rshares%TYPE) CASCADE
    ;
    CREATE OR REPLACE FUNCTION public.calculate_rhsares_part_of_hot_and_trend(_rshares hive_votes.rshares%TYPE)
    RETURNS double precision
    LANGUAGE 'plpgsql'
    IMMUTABLE
    AS $BODY$
    DECLARE
        mod_score double precision;
    BEGIN
        mod_score := _rshares / 10000000.0;
        IF ( mod_score > 0 )
        THEN
            return log( greatest( abs(mod_score), 1 ) );
        END IF;
        return  -1.0 * log( greatest( abs(mod_score), 1 ) );
    END;
    $BODY$;
    """
    db.query_no_return(sql)

    sql = """
    DROP FUNCTION IF EXISTS public.calculate_hot(hive_votes.rshares%TYPE, hive_posts.created_at%TYPE)
    ;
    CREATE OR REPLACE FUNCTION public.calculate_hot(
        _rshares hive_votes.rshares%TYPE,
        _post_created_at hive_posts.created_at%TYPE)
    RETURNS hive_posts.sc_hot%TYPE
    LANGUAGE 'plpgsql'
    IMMUTABLE
    AS $BODY$
    BEGIN
        return calculate_rhsares_part_of_hot_and_trend(_rshares) + calculate_time_part_of_hot( _post_created_at );
    END;
    $BODY$;
    """
    db.query_no_return(sql)

    sql = """
          DO $$
          BEGIN
            EXECUTE 'ALTER DATABASE '||current_database()||' SET join_collapse_limit TO 16';
            EXECUTE 'ALTER DATABASE '||current_database()||' SET from_collapse_limit TO 16';
          END
          $$;
          """
    db.query_no_return(sql)

    sql = """
    DROP FUNCTION IF EXISTS public.calculate_tranding(hive_votes.rshares%TYPE, hive_posts.created_at%TYPE)
    ;
    CREATE OR REPLACE FUNCTION public.calculate_tranding(
        _rshares hive_votes.rshares%TYPE,
        _post_created_at hive_posts.created_at%TYPE)
    RETURNS hive_posts.sc_trend%TYPE
    LANGUAGE 'plpgsql'
    IMMUTABLE
    AS $BODY$
    BEGIN
        return calculate_rhsares_part_of_hot_and_trend(_rshares) + calculate_time_part_of_trending( _post_created_at );
    END;
    $BODY$;
    """
    db.query_no_return(sql)

    sql = """
        DROP FUNCTION IF EXISTS public.max_time_stamp() CASCADE;
        CREATE OR REPLACE FUNCTION public.max_time_stamp( _first TIMESTAMP, _second TIMESTAMP )
        RETURNS TIMESTAMP
        LANGUAGE 'plpgsql'
        IMMUTABLE
        AS $BODY$
        BEGIN
          IF _first > _second THEN
               RETURN _first;
            ELSE
               RETURN _second;
            END IF;
        END
        $BODY$;
        """
    db.query_no_return(sql)

    sql = """
          DROP FUNCTION IF EXISTS public.update_hive_posts_api_helper(INTEGER, INTEGER);

          CREATE OR REPLACE FUNCTION public.update_hive_posts_api_helper(in _first_block_num INTEGER, _last_block_num INTEGER)
            RETURNS void
            LANGUAGE 'plpgsql'
            VOLATILE
          AS $BODY$
          BEGIN
          IF _first_block_num IS NULL OR _last_block_num IS NULL THEN
            -- initial creation of table.

            INSERT INTO hive_posts_api_helper
            (id, author, parent_author, parent_permlink_or_category)
            SELECT hp.id, hp.author, hp.parent_author, hp.parent_permlink_or_category
            FROM hive_posts_view hp
            ;
          ELSE
            -- Regular incremental update.
            INSERT INTO hive_posts_api_helper
            (id, author, parent_author, parent_permlink_or_category)
            SELECT hp.id, hp.author, hp.parent_author, hp.parent_permlink_or_category
            FROM hive_posts_view hp
            WHERE hp.block_num BETWEEN _first_block_num AND _last_block_num AND
                   NOT EXISTS (SELECT NULL FROM hive_posts_api_helper h WHERE h.id = hp.id)
            ;
          END IF;

          END
          $BODY$
          """
    db.query_no_return(sql)

    sql = """
        DROP FUNCTION IF EXISTS public.calculate_notify_vote_score(_payout hive_posts.payout%TYPE, _abs_rshares hive_posts_view.abs_rshares%TYPE, _rshares hive_votes.rshares%TYPE) CASCADE
        ;
        CREATE OR REPLACE FUNCTION public.calculate_notify_vote_score(_payout hive_posts.payout%TYPE, _abs_rshares hive_posts_view.abs_rshares%TYPE, _rshares hive_votes.rshares%TYPE)
        RETURNS INT
        LANGUAGE 'sql'
        IMMUTABLE
        AS $BODY$
            SELECT CASE
                WHEN ((( _payout )/_abs_rshares) * 1000 * _rshares < 20 ) THEN -1
                    ELSE LEAST(100, (LENGTH(CAST( CAST( ( (( _payout )/_abs_rshares) * 1000 * _rshares ) as BIGINT) as text)) - 1) * 25)
            END;
        $BODY$;
    """

    db.query_no_return(sql)

    sql = """
        DROP FUNCTION IF EXISTS notification_id(in _block_number INTEGER, in _notifyType INTEGER, in _id INTEGER)
        ;
        CREATE OR REPLACE FUNCTION notification_id(in _block_number INTEGER, in _notifyType INTEGER, in _id INTEGER)
        RETURNS BIGINT
        AS
        $function$
        BEGIN
        RETURN CAST( _block_number as BIGINT ) << 32
               | ( _notifyType << 16 )
               | ( _id & CAST( x'00FF' as INTEGER) );
        END
        $function$
        LANGUAGE plpgsql IMMUTABLE
        ;
    """
    db.query_no_return(sql)

    sql = """
        DROP VIEW IF EXISTS hive_notifications_view
        ;
        CREATE VIEW hive_notifications_view
        AS
        SELECT
        *
        FROM
        (
            SELECT --replies
                  posts_and_scores.block_num as block_num
                , posts_and_scores.id as id
                , posts_and_scores.post_id as post_id
                , posts_and_scores.type_id as type_id
                , posts_and_scores.created_at as created_at
                , posts_and_scores.author as src
                , posts_and_scores.parent_author as dst
                , posts_and_scores.parent_author as author
                , posts_and_scores.parent_permlink as permlink
                , ''::VARCHAR as community
                , ''::VARCHAR as community_title
                , ''::VARCHAR as payload
                , posts_and_scores.score as score
            FROM
            (
                SELECT
                      hpv.block_num as block_num
                    , notification_id(
                          hpv.block_num
                        , CASE ( hpv.depth )
                            WHEN 1 THEN 12 --replies
                            ELSE 13 --comment replies
                          END
                        , hpv.id ) as id
                    , CASE ( hpv.depth )
                        WHEN 1 THEN 12 --replies
                        ELSE 13 --comment replies
                      END as type_id
                    , hpv.created_at
                    , hpv.author
                    , hpv.parent_id as post_id
                    , hpv.parent_author as parent_author
                    , hpv.parent_permlink_or_category as parent_permlink
                    , hpv.depth
                    , hpv.parent_author_id
                    , hpv.author_id
                    , harv.score as score
                FROM
                    hive_posts_view hpv
                JOIN hive_accounts_rank_view harv ON harv.id = hpv.author_id
                WHERE hpv.depth > 0
            ) as posts_and_scores
            WHERE NOT EXISTS(
                SELECT 1
                FROM
                hive_follows hf
                WHERE hf.follower = posts_and_scores.parent_author_id AND hf.following = posts_and_scores.author_id AND hf.state = 2
            )

            UNION ALL

            SELECT --follows
                  hf.block_num as block_num
                , notifs_id.notif_id as id
                , 0 as post_id
                , 15 as type_id
                , hf.created_at as created_at
                , followers_scores.follower_name as src
                , ha2.name as dst
                , ''::VARCHAR as author
                , ''::VARCHAR as permlink
                , ''::VARCHAR as community
                , ''::VARCHAR as community_title
                , ''::VARCHAR as payload
                , followers_scores.score as score
            FROM
                hive_follows hf
            JOIN hive_accounts ha2 ON hf.following = ha2.id
            JOIN (
                SELECT
                      ha.id as follower_id
                    , ha.name as follower_name
                    , harv.score as score
                FROM hive_accounts ha
                JOIN hive_accounts_rank_view harv ON harv.id = ha.id
            ) as followers_scores ON followers_scores.follower_id = hf.follower
            JOIN (
                SELECT
                      hf2.id as id
                    , notification_id(hf2.block_num, 15, hf2.id) as notif_id
                FROM hive_follows hf2
            ) as notifs_id ON notifs_id.id = hf.id

            UNION ALL

            SELECT --reblogs
                  hr.block_num as block_num
                , hr_scores.notif_id as id
                , hp.id as post_id
                , 14 as type_id
                , hr.created_at as created_at
                , ha_hr.name as src
                , ha.name as dst
                , ha.name as author
                , hpd.permlink as permlink
                , ''::VARCHAR as community
                , ''::VARCHAR as community_title
                , ''::VARCHAR as payload
                , hr_scores.score as score
            FROM
                hive_reblogs hr
            JOIN hive_posts hp ON hr.post_id = hp.id
            JOIN hive_permlink_data hpd ON hp.permlink_id = hpd.id
            JOIN hive_accounts ha_hr ON hr.blogger_id = ha_hr.id
            JOIN (
                SELECT
                      hr2.id as id
                    , notification_id(hr2.block_num, 14, hr2.id) as notif_id
                    , harv.score as score
                FROM hive_reblogs hr2
                JOIN hive_accounts_rank_view harv ON harv.id = hr2.blogger_id
            ) as hr_scores ON hr_scores.id = hr.id
            JOIN hive_accounts ha ON hp.author_id = ha.id

            UNION ALL

            SELECT --subscriptions
                  hs.block_num as block_num
                , hs_scores.notif_id as id
                , 0 as post_id
                , 11 as type_id
                , hs.created_at as created_at
                , hs_scores.src as src
                , ha_com.name as dst
                , ''::VARCHAR as author
                , ''::VARCHAR as permlink
                , hc.name as community
                , hc.title as community_title
                , ''::VARCHAR as payload
                , hs_scores.score
            FROM
                hive_subscriptions hs
            JOIN hive_communities hc ON hs.community_id = hc.id
            JOIN (
                SELECT
                      hs2.id as id
                    , notification_id(hs2.block_num, 11, hs2.id) as notif_id
                    , harv.score as score
                    , ha.name as src
                FROM hive_subscriptions hs2
                JOIN hive_accounts ha ON hs2.account_id = ha.id
                JOIN hive_accounts_rank_view harv ON harv.id = ha.id
            ) as hs_scores ON hs_scores.id = hs.id
            JOIN hive_accounts ha_com ON hs.community_id = ha_com.id

            UNION ALL

            SELECT -- new community
                  hc.block_num as block_num
                , hc_id.notif_id as id
                , 0 as post_id
                , 1 as type_id
                , hc.created_at as created_at
                , ''::VARCHAR as src
                , ha.name as dst
                , ''::VARCHAR as author
                , ''::VARCHAR as permlink
                , hc.name as community
                , ''::VARCHAR as community_title
                , ''::VARCHAR as payload
                , 35 as score
            FROM
                hive_communities hc
            JOIN hive_accounts ha ON ha.id = hc.id
            JOIN (
                SELECT
                      hc2.id as id
                    , notification_id(hc2.block_num, 11, hc2.id) as notif_id
                FROM hive_communities hc2
            ) as hc_id ON hc_id.id = hc.id

            UNION ALL

            SELECT --votes
                  hv.block_num as block_num
                , scores.notif_id as id
                , scores.post_id as post_id
                , 17 as type_id
                , hv.last_update as created_at
                , scores.src as src
                , scores.dst as dst
                , scores.dst as author
                , scores.permlink as permlink
                , ''::VARCHAR as community
                , ''::VARCHAR as community_title
                , ''::VARCHAR as payload
                , scores.score as score
            FROM hive_votes hv
            JOIN (
                SELECT
                      hv1.id as id
                    , hpv.id as post_id
                    , notification_id(hv1.block_num, 17, CAST( hv1.id as INT) ) as notif_id
                    , calculate_notify_vote_score( (hpv.payout + hpv.pending_payout), hpv.abs_rshares, hv1.rshares ) as score
                    , hpv.author as dst
                    , ha.name as src
                    , hpv.permlink as permlink
                FROM hive_votes hv1
                JOIN hive_posts_view hpv ON hv1.post_id = hpv.id
                JOIN hive_accounts ha ON ha.id = hv1.voter_id
                WHERE hv1.rshares >= 10e9 AND hpv.abs_rshares != 0
            ) as scores ON scores.id = hv.id
            WHERE scores.score > 0
      UNION ALL
            SELECT --persistent notifs
            	 hn.block_num
               , notification_id(hn.block_num, hn.type_id, CAST( hn.id as INT) ) as id
               , hp.id as post_id
               , hn.type_id as type_id
               , hn.created_at as created_at
               , ha_src.name as src
               , ha_dst.name as dst
               , ha_pst.name as author
               , hpd.permlink as permlink
               , hc.name as community
               , hc.title as community_title
               , hn.payload as payload
               , hn.score as score
            FROM hive_notifs hn
            JOIN hive_accounts ha_dst ON hn.dst_id = ha_dst.id
            LEFT JOIN hive_accounts ha_src ON hn.src_id = ha_src.id
            LEFT JOIN hive_communities hc ON hn.community_id = hc.id
            LEFT JOIN hive_posts hp ON hn.post_id = hp.id
            LEFT JOIN hive_accounts ha_pst ON ha_pst.id = hp.author_id
            LEFT JOIN hive_permlink_data hpd ON hpd.id = hp.permlink_id
        ) as notifs
    """
    db.query_no_return(sql)

    sql = """
        DROP TYPE IF EXISTS bridge_api_post CASCADE;
        CREATE TYPE bridge_api_post AS (
            id INTEGER,
            author VARCHAR,
            parent_author VARCHAR,
            author_rep FLOAT4,
            root_title VARCHAR,
            beneficiaries JSON,
            max_accepted_payout VARCHAR,
            percent_hbd INTEGER,
            url TEXT,
            permlink VARCHAR,
            parent_permlink_or_category VARCHAR,
            title VARCHAR,
            body TEXT,
            category VARCHAR,
            depth SMALLINT,
            promoted DECIMAL(10,3),
            payout DECIMAL(10,3),
            pending_payout DECIMAL(10,3),
            payout_at TIMESTAMP,
            is_paidout BOOLEAN,
            children INTEGER,
            votes INTEGER,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            rshares NUMERIC,
            abs_rshares NUMERIC,
            json TEXT,
            is_hidden BOOLEAN,
            is_grayed BOOLEAN,
            total_votes BIGINT,
            sc_trend FLOAT4,
            role_title VARCHAR,
            community_title VARCHAR,
            role_id SMALLINT,
            is_pinned BOOLEAN,
            curator_payout_value VARCHAR
        );
    """
    db.query_no_return(sql)

    sql = """
        DROP FUNCTION IF EXISTS bridge_get_ranked_post_by_trends;
        CREATE FUNCTION bridge_get_ranked_post_by_trends( in _author VARCHAR, in _permlink VARCHAR, in _limit SMALLINT )
        RETURNS SETOF bridge_api_post
        AS
        $function$
        DECLARE
        	__post_id INTEGER = -1;
        	__trending_limit FLOAT = -1.0;
        BEGIN
            IF _author <> '' THEN
                __post_id = find_comment_id( _author, _permlink, True );
                SELECT hp.sc_trend INTO __trending_limit FROM hive_posts hp WHERE hp.id = __post_id;
            END IF;
            RETURN QUERY SELECT
            hp.id,
            hp.author,
            hp.parent_author,
            hp.author_rep,
            hp.root_title,
            hp.beneficiaries,
            hp.max_accepted_payout,
            hp.percent_hbd,
            hp.url,
            hp.permlink,
            hp.parent_permlink_or_category,
            hp.title,
            hp.body,
            hp.category,
            hp.depth,
            hp.promoted,
            hp.payout,
            hp.pending_payout,
            hp.payout_at,
            hp.is_paidout,
            hp.children,
            hp.votes,
            hp.created_at,
            hp.updated_at,
            hp.rshares,
            hp.abs_rshares,
            hp.json,
            hp.is_hidden,
            hp.is_grayed,
            hp.total_votes,
            hp.sc_trend,
            hp.role_title,
            hp.community_title,
            hp.role_id,
            hp.is_pinned,
            hp.curator_payout_value
        FROM
        (
        SELECT
            hp1.id
          , hp1.sc_trend as trend
        FROM
            hive_posts hp1
        WHERE NOT hp1.is_paidout AND hp1.depth = 0
            AND ( __post_id = -1 OR hp1.sc_trend < __trending_limit OR ( hp1.sc_trend = __trending_limit AND hp1.id < __post_id  ) )
        ORDER BY hp1.sc_trend DESC
        LIMIT _limit
        ) as trends
        JOIN hive_posts_view hp ON hp.id = trends.id
        ORDER BY trends.trend DESC, trends.id LIMIT _limit;
        END
        $function$
        language plpgsql STABLE
    """
    db.query_no_return(sql)

    sql = """
        DROP FUNCTION IF EXISTS bridge_get_ranked_post_by_created;
        CREATE FUNCTION bridge_get_ranked_post_by_created( in _author VARCHAR, in _permlink VARCHAR, in _limit SMALLINT )
        RETURNS SETOF bridge_api_post
        AS
        $function$
        DECLARE
          __post_id INTEGER = -1;
        BEGIN
          IF _author <> '' THEN
              __post_id = find_comment_id( _author, _permlink, True );
          END IF;
          RETURN QUERY SELECT
              hp.id,
              hp.author,
              hp.parent_author,
              hp.author_rep,
              hp.root_title,
              hp.beneficiaries,
              hp.max_accepted_payout,
              hp.percent_hbd,
              hp.url,
              hp.permlink,
              hp.parent_permlink_or_category,
              hp.title,
              hp.body,
              hp.category,
              hp.depth,
              hp.promoted,
              hp.payout,
              hp.pending_payout,
              hp.payout_at,
              hp.is_paidout,
              hp.children,
              hp.votes,
              hp.created_at,
              hp.updated_at,
              hp.rshares,
              hp.abs_rshares,
              hp.json,
              hp.is_hidden,
              hp.is_grayed,
              hp.total_votes,
              hp.sc_trend,
              hp.role_title,
              hp.community_title,
              hp.role_id,
              hp.is_pinned,
              hp.curator_payout_value
        	FROM
          (
              SELECT
                hp1.id
              , hp1.created_at as created_at
              FROM hive_posts hp1 WHERE hp1.depth = 0 AND NOT hp1.is_grayed AND ( __post_id = -1 OR hp1.id < __post_id  )
              ORDER BY hp1.id DESC
              LIMIT _limit
          ) as created
          JOIN hive_posts_view hp ON hp.id = created.id
          ORDER BY created.created_at DESC, created.id LIMIT _limit;
          END
          $function$
          language plpgsql STABLE
    """
    db.query_no_return(sql)

    sql = """
        DROP TYPE IF EXISTS notification
        ;
        CREATE TYPE notification AS
        (
          id BIGINT
        , type_id SMALLINT
        , created_at TIMESTAMP
        , src VARCHAR
        , dst VARCHAR
        , author VARCHAR
        , permlink VARCHAR
        , community VARCHAR
        , community_title VARCHAR
        , payload VARCHAR
        , score SMALLINT
        );
    """
    db.query_no_return(sql)

    sql = """
            DROP FUNCTION IF EXISTS account_notifications
                    ;
            CREATE OR REPLACE FUNCTION account_notifications(in _account VARCHAR, in _min_score SMALLINT, in _last_id BIGINT, in _limit SMALLINT)
            RETURNS SETOF notification
            AS
            $function$
            SELECT
                  hnv.id
                , CAST( hnv.type_id as SMALLINT) as type_id
                , hnv.created_at
                , hnv.src
                , hnv.dst
                , hnv.author
                , hnv.permlink
                , hnv.community
                , hnv.community_title
                , hnv.payload
                , CAST( hnv.score as SMALLINT) as score
            FROM
                hive_notifications_view hnv
            WHERE hnv.block_num > ( SELECT num as head_block FROM hive_blocks ORDER BY num DESC LIMIT 1 ) - (90 * 24 * 3600 / 3) -- 90 days in blocks
                AND hnv.dst = _account AND hnv.score >= _min_score AND ( _last_id = -1 OR hnv.id < _last_id )
            ORDER BY hnv.id DESC LIMIT _limit
            ;
            $function$
            LANGUAGE sql STABLE
            ;
    """
    db.query_no_return(sql)

    sql = """
        DROP FUNCTION IF EXISTS post_notifications
        ;
        CREATE OR REPLACE FUNCTION post_notifications(in _author VARCHAR, in _permlink VARCHAR, in _min_score SMALLINT, in _last_id BIGINT, in _limit SMALLINT)
        RETURNS SETOF notification
        AS
        $function$
        DECLARE
            __post_id INT;
            __start_block INT;
        BEGIN
            __post_id = find_comment_id(_author, _permlink, True);
            __start_block = ( SELECT num AS head_block FROM hive_blocks ORDER BY num DESC LIMIT 1 ) - (90 * 24 * 3600 / 3); -- 90 days in blocks
            RETURN QUERY
            (
                SELECT
                      hnv.id
                    , CAST( hnv.type_id as SMALLINT) as type_id
                    , hnv.created_at
                    , hnv.src
                    , hnv.dst
                    , hnv.author
                    , hnv.permlink
                    , hnv.community
                    , hnv.community_title
                    , hnv.payload
                    , CAST( hnv.score as SMALLINT) as score
                FROM
                    hive_notifications_view hnv
                WHERE
                    hnv.block_num > __start_block
                    AND hnv.post_id = __post_id
                    AND hnv.score >= _min_score
                    AND ( _last_id = -1 OR hnv.id < _last_id )
                ORDER BY hnv.id DESC
                LIMIT _limit
            );
        END
        $function$
        LANGUAGE plpgsql STABLE
    """
    db.query_no_return(sql)

    sql = """
        DROP FUNCTION IF EXISTS get_discussion
        ;
        CREATE OR REPLACE FUNCTION get_discussion(
            in _author hive_accounts.name%TYPE,
            in _permlink hive_permlink_data.permlink%TYPE
        )
        RETURNS TABLE
        (
            id hive_posts.id%TYPE, parent_id hive_posts.parent_id%TYPE, author hive_accounts.name%TYPE, permlink hive_permlink_data.permlink%TYPE,
            title hive_post_data.title%TYPE, body hive_post_data.body%TYPE, category hive_category_data.category%TYPE, depth hive_posts.depth%TYPE,
            promoted hive_posts.promoted%TYPE, payout hive_posts.payout%TYPE, pending_payout hive_posts.pending_payout%TYPE, payout_at hive_posts.payout_at%TYPE,
            is_paidout hive_posts.is_paidout%TYPE, children hive_posts.children%TYPE, created_at hive_posts.created_at%TYPE, updated_at hive_posts.updated_at%TYPE,
            rshares hive_posts_view.rshares%TYPE, abs_rshares hive_posts_view.abs_rshares%TYPE, json hive_post_data.json%TYPE, author_rep hive_accounts.reputation%TYPE,
            is_hidden hive_posts.is_hidden%TYPE, is_grayed hive_posts.is_grayed%TYPE, total_votes BIGINT, sc_trend hive_posts.sc_trend%TYPE,
            acct_author_id hive_posts.author_id%TYPE, root_author hive_accounts.name%TYPE, root_permlink hive_permlink_data.permlink%TYPE,
            parent_author hive_accounts.name%TYPE, parent_permlink_or_category hive_permlink_data.permlink%TYPE, allow_replies BOOLEAN,
            allow_votes hive_posts.allow_votes%TYPE, allow_curation_rewards hive_posts.allow_curation_rewards%TYPE, url TEXT, root_title hive_post_data.title%TYPE,
            beneficiaries hive_posts.beneficiaries%TYPE, max_accepted_payout hive_posts.max_accepted_payout%TYPE, percent_hbd hive_posts.percent_hbd%TYPE,
            curator_payout_value hive_posts.curator_payout_value%TYPE
        )
        LANGUAGE plpgsql
        AS
        $function$
        DECLARE
            __post_id INT;
        BEGIN
            __post_id = find_comment_id( _author, _permlink, True );
            RETURN QUERY
            SELECT
                hpv.id,
                hpv.parent_id,
                hpv.author,
                hpv.permlink,
                hpv.title,
                hpv.body,
                hpv.category,
                hpv.depth,
                hpv.promoted,
                hpv.payout,
                hpv.pending_payout,
                hpv.payout_at,
                hpv.is_paidout,
                hpv.children,
                hpv.created_at,
                hpv.updated_at,
                hpv.rshares,
                hpv.abs_rshares,
                hpv.json,
                hpv.author_rep,
                hpv.is_hidden,
                hpv.is_grayed,
                hpv.total_votes,
                hpv.sc_trend,
                hpv.author_id AS acct_author_id,
                hpv.root_author,
                hpv.root_permlink,
                hpv.parent_author,
                hpv.parent_permlink_or_category,
                hpv.allow_replies,
                hpv.allow_votes,
                hpv.allow_curation_rewards,
                hpv.url,
                hpv.root_title,
                hpv.beneficiaries,
                hpv.max_accepted_payout,
                hpv.percent_hbd,
                hpv.curator_payout_value
            FROM
            (
                WITH RECURSIVE child_posts (id, parent_id) AS
                (
                    SELECT hp.id, hp.parent_id
                    FROM hive_posts hp
                    WHERE hp.id = __post_id
                    AND NOT hp.is_muted
                    UNION ALL
                    SELECT children.id, children.parent_id
                    FROM hive_posts children
                    JOIN child_posts ON children.parent_id = child_posts.id
                    WHERE children.counter_deleted = 0 AND NOT children.is_muted
                )
                SELECT hp2.id
                FROM hive_posts hp2
                JOIN child_posts cp ON cp.id = hp2.id
                ORDER BY hp2.id
            ) ds
            JOIN hive_posts_view hpv ON ds.id = hpv.id
            ORDER BY ds.id
            LIMIT 2000
            ;
        END
        $function$
        ;
    """

    db.query_no_return(sql)

    sql_scripts = [
      "update_feed_cache.sql",
      "get_account_post_replies.sql",
      "payout_stats_view.sql",
      "update_hive_posts_mentions.sql"
    ]
    from os.path import dirname, realpath
    dir_path = dirname(realpath(__file__))
    for script in sql_scripts:
        execute_sql_script(db.query_no_return, "{}/sql_scripts/{}".format(dir_path, script))



def reset_autovac(db):
    """Initializes/resets per-table autovacuum/autoanalyze params.

    We use a scale factor of 0 and specify exact threshold tuple counts,
    per-table, in the format (autovacuum_threshold, autoanalyze_threshold)."""

    autovac_config = { #    vacuum  analyze
        'hive_accounts':    (50000, 100000),
        'hive_posts':       (2500, 10000),
        'hive_post_tags':   (5000, 10000),
        'hive_follows':     (5000, 5000),
        'hive_feed_cache':  (5000, 5000),
        'hive_blocks':      (5000, 25000),
        'hive_reblogs':     (5000, 5000),
        'hive_payments':    (5000, 5000),
    }

    for table, (n_vacuum, n_analyze) in autovac_config.items():
        sql = """ALTER TABLE %s SET (autovacuum_vacuum_scale_factor = 0,
                                     autovacuum_vacuum_threshold = %s,
                                     autovacuum_analyze_scale_factor = 0,
                                     autovacuum_analyze_threshold = %s)"""
        db.query(sql % (table, n_vacuum, n_analyze))


def set_fillfactor(db):
    """Initializes/resets FILLFACTOR for tables which are intesively updated"""

    fillfactor_config = {
        'hive_posts': 70,
        'hive_post_data': 70,
        'hive_votes': 70,
        'hive_reputation_data': 50
    }

    for table, fillfactor in fillfactor_config.items():
        sql = """ALTER TABLE {} SET (FILLFACTOR = {})"""
        db.query(sql.format(table, fillfactor))

def set_logged_table_attribute(db, logged):
    """Initializes/resets LOGGED/UNLOGGED attribute for tables which are intesively updated"""

    logged_config = [
        'hive_accounts',
        'hive_permlink_data',
        'hive_post_tags',
        'hive_posts',
        'hive_post_data',
        'hive_votes',
        'hive_reputation_data'
    ]

    for table in logged_config:
        log.info("Setting {} attribute on a table: {}".format('LOGGED' if logged else 'UNLOGGED', table))
        sql = """ALTER TABLE {} SET {}"""
        db.query_no_return(sql.format(table, 'LOGGED' if logged else 'UNLOGGED'))

def execute_sql_script(query_executor, path_to_script):
    """ Load and execute sql script from file
        Params:
          query_executor - callable to execute query with
          path_to_script - path to script
        Returns:
          depending on query_executor

        Example:
          print(execute_sql_script(db.query_row, "./test.sql"))
          where test_sql: SELECT * FROM hive_state WHERE block_num = 0;
          will return something like: (0, 18, Decimal('0.000000'), Decimal('0.000000'), Decimal('0.000000'), '')
    """
    try:
        sql_script = None
        with open(path_to_script, 'r') as sql_script_file:
            sql_script = sql_script_file.read()
        if sql_script is not None:
            return query_executor(sql_script)
    except Exception as ex:
        log.exception("Error running sql script: {}".format(ex))
        raise ex
    return None
