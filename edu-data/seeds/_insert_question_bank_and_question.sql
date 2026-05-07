SET FOREIGN_KEY_CHECKS=0;
TRUNCATE question;
TRUNCATE question_bank;
SET FOREIGN_KEY_CHECKS=1;

SET @institution_id := (SELECT id FROM org_institution ORDER BY id LIMIT 1);

-- Insert banks with category fallback: level3 -> level2 -> level1 -> first category
INSERT INTO question_bank (institution_id, category_id, bank_code, bank_name, yn, created_at, updated_at)
SELECT
  @institution_id,
  COALESCE(
    (SELECT id FROM dim_course_category WHERE category_code = (b.category_level3_code COLLATE utf8mb4_unicode_ci) LIMIT 1),
    (SELECT id FROM dim_course_category WHERE category_code = (b.category_level2_code COLLATE utf8mb4_unicode_ci) LIMIT 1),
    (SELECT id FROM dim_course_category WHERE category_code = (b.category_level1_code COLLATE utf8mb4_unicode_ci) LIMIT 1),
    (SELECT id FROM dim_course_category ORDER BY id LIMIT 1)
  ) AS category_id,
  b.question_bank_code,
  b.question_bank_name,
  1,
  NOW(),
  NOW()
FROM stg_question_bank b
WHERE b.question_bank_code IS NOT NULL AND b.question_bank_code <> '';

-- Insert questions (requires bank_id + question_type_id)
INSERT INTO question (
  bank_id, question_code, question_type_id, stem, options_json, answer_text, analysis_text, yn, created_at, updated_at
)
SELECT
  qb.id,
  q.question_code,
  qt.id,
  q.stem,
  CAST(NULLIF(q.options_json, '') AS JSON),
  q.answer_text,
  NULLIF(q.analysis_text, ''),
  1,
  NOW(),
  NOW()
FROM stg_question q
JOIN question_bank qb ON qb.bank_code = (q.question_bank_code COLLATE utf8mb4_unicode_ci)
JOIN dim_question_type qt ON qt.type_code = (q.question_type_code COLLATE utf8mb4_unicode_ci)
WHERE q.question_code IS NOT NULL AND q.question_code <> '';

SELECT COUNT(*) AS question_bank_rows FROM question_bank;
SELECT COUNT(*) AS question_rows FROM question;

