DROP FUNCTION IF EXISTS bridge_get_account_posts_by_blog;

CREATE OR REPLACE FUNCTION bridge_get_account_posts_by_blog(
  in _account VARCHAR,
  in _author VARCHAR,
  in _permlink VARCHAR,
  in _limit INTEGER
)
RETURNS SETOF bridge_api_post
AS
$function$
DECLARE
  __post_id INTEGER := 0;
  __account_id INTEGER := find_account_id( _account, True );
  __created_at TIMESTAMP;
BEGIN

  IF _permlink <> '' THEN
    __post_id = find_comment_id( _author, _permlink, True );
    __created_at = 
    (
      SELECT created_at
      FROM hive_feed_cache
      WHERE account_id = __account_id
      AND post_id = __post_id
    );
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
      hp.curator_payout_value,
      hp.is_muted
    FROM hive_posts_view hp
    JOIN
    (
      SELECT hfc.post_id
      FROM hive_feed_cache hfc
      LEFT JOIN
      (
        SELECT
            hp.id
        FROM
            hive_posts_view hp
            LEFT JOIN hive_reblogs hr ON hp.id = hr.post_id
        WHERE
            hp.author_id = __account_id
            AND hp.depth = 0
            AND hp.community_id IS NOT NULL
      ) T ON hfc.post_id = T.id
      WHERE hfc.account_id = __account_id AND ( __post_id = 0 OR hfc.created_at <= __created_at )
      ORDER BY hfc.created_at DESC
    )T ON hp.id = T.post_id
    LIMIT _limit;

END
$function$
language plpgsql STABLE;
