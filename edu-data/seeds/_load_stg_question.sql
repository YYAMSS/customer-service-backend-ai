TRUNCATE stg_question;

LOAD DATA INFILE '/var/lib/mysql-files/edu_seeds/3_question/question.csv'
INTO TABLE stg_question
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES;

