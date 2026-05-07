DROP TABLE IF EXISTS stg_series;
CREATE TABLE stg_series (
  product_code TEXT,
  product_name TEXT,
  series_code TEXT,
  series_name TEXT,
  category_level1_code TEXT,
  category_level2_code TEXT,
  category_level3_code TEXT,
  delivery_mode_codes TEXT,
  sale_status_code TEXT,
  target_learning_goal_codes TEXT,
  target_learner_identity_codes TEXT,
  target_grade_codes TEXT,
  sale_price TEXT,
  original_price TEXT
);

TRUNCATE stg_series;

LOAD DATA INFILE '/var/lib/mysql-files/edu_seeds/2_course/series.csv'
INTO TABLE stg_series
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES;

SHOW WARNINGS LIMIT 5;
SELECT COUNT(*) AS stg_series_rows FROM stg_series;

