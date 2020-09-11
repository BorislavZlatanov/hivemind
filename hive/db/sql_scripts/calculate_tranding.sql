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