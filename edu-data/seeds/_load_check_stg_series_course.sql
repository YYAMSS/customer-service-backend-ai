DROP TABLE IF EXISTS stg_series_course;
CREATE TABLE stg_series_course (
  series_code TEXT,
  module_code TEXT,
  module_name TEXT,
  stage_no TEXT,
  lesson_count TEXT,
  total_hours TEXT,
  module_keywords TEXT
);

TRUNCATE stg_series_course;

LOAD DATA INFILE '/var/lib/mysql-files/edu_seeds/2_course/series_course.csv'
INTO TABLE stg_series_course
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES;

SHOW WARNINGS LIMIT 5;
SELECT COUNT(*) AS stg_series_course_rows FROM stg_series_course;

