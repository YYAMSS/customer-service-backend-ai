SET FOREIGN_KEY_CHECKS=0;
TRUNCATE series_cohort_course;
TRUNCATE series_cohort;
SET FOREIGN_KEY_CHECKS=1;

SET @institution_id := (SELECT id FROM org_institution ORDER BY id LIMIT 1);
SET @teacher_id := (SELECT id FROM staff_profile WHERE institution_id=@institution_id ORDER BY id LIMIT 1);

-- Create one cohort per series (default)
INSERT INTO series_cohort (
  institution_id, series_id, campus_id, head_teacher_id,
  cohort_code, cohort_name, sale_price, max_student_count, current_student_count,
  yn, start_date, end_date, created_at, updated_at
)
SELECT
  @institution_id,
  s.id,
  (SELECT id FROM org_campus WHERE institution_id=@institution_id ORDER BY id LIMIT 1),
  @teacher_id,
  CONCAT('C_', s.series_code),
  CONCAT(s.series_name, ' · 默认班'),
  0.00,
  200,
  0,
  1,
  CURDATE(),
  NULL,
  NOW(),
  NOW()
FROM series s;

-- Insert modules into series_cohort_course by joining stg_series_course to series -> cohort
INSERT INTO series_cohort_course (
  cohort_id, module_code, module_name, description,
  lesson_count, total_hours, stage_no, start_date, end_date, created_at, updated_at
)
SELECT
  c.id AS cohort_id,
  sc.module_code,
  sc.module_name,
  NULL,
  CAST(sc.lesson_count AS SIGNED),
  CAST(sc.total_hours AS DECIMAL(8,2)),
  CAST(sc.stage_no AS SIGNED),
  CURDATE(),
  CURDATE(),
  NOW(),
  NOW()
FROM stg_series_course sc
JOIN series s ON s.institution_id=@institution_id AND s.series_code = (sc.series_code COLLATE utf8mb4_unicode_ci)
JOIN series_cohort c ON c.institution_id=@institution_id AND c.series_id=s.id;

SELECT COUNT(*) AS series_cohort_rows FROM series_cohort;
SELECT COUNT(*) AS series_cohort_course_rows FROM series_cohort_course;

