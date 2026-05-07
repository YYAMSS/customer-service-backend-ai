SET FOREIGN_KEY_CHECKS=0;
TRUNCATE series_category_rel;
TRUNCATE series;
SET FOREIGN_KEY_CHECKS=1;

SET @institution_id := (SELECT id FROM org_institution ORDER BY id LIMIT 1);
SET @created_by := (SELECT id FROM sys_user ORDER BY id LIMIT 1);

-- Insert series
INSERT INTO series (
  institution_id, delivery_mode, series_code, series_name, description, cover_url,
  target_learner_identity_codes, target_learning_goal_codes, target_grade_codes,
  sale_status, created_by, created_at, updated_at
)
SELECT
  @institution_id,
  COALESCE(JSON_UNQUOTE(JSON_EXTRACT(s.delivery_mode_codes, '$[0]')), 'online_live') AS delivery_mode,
  s.series_code,
  s.series_name,
  NULL,
  NULL,
  CAST(NULLIF(s.target_learner_identity_codes, '') AS JSON),
  CAST(NULLIF(s.target_learning_goal_codes, '') AS JSON),
  CAST(NULLIF(s.target_grade_codes, '') AS JSON),
  s.sale_status_code,
  @created_by,
  NOW(),
  NOW()
FROM stg_series s
WHERE s.series_code IS NOT NULL AND s.series_code <> '';

-- Insert series_category_rel using most specific category_code available
INSERT INTO series_category_rel (series_id, category_id, sort_no, created_at, updated_at)
SELECT
  sr.id,
  COALESCE(
    (SELECT id FROM dim_course_category WHERE category_code = (s.category_level3_code COLLATE utf8mb4_unicode_ci) LIMIT 1),
    (SELECT id FROM dim_course_category WHERE category_code = (s.category_level2_code COLLATE utf8mb4_unicode_ci) LIMIT 1),
    (SELECT id FROM dim_course_category WHERE category_code = (s.category_level1_code COLLATE utf8mb4_unicode_ci) LIMIT 1),
    (SELECT id FROM dim_course_category ORDER BY id LIMIT 1)
  ) AS category_id,
  0,
  NOW(),
  NOW()
FROM stg_series s
JOIN series sr
  ON sr.institution_id=@institution_id
 AND sr.series_code = (s.series_code COLLATE utf8mb4_unicode_ci);

SELECT COUNT(*) AS series_rows FROM series;
SELECT COUNT(*) AS series_category_rel_rows FROM series_category_rel;

