#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/mnt/d/CODE/AI/customer-service-backend-ai"
SEEDS_DIR="$PROJECT_ROOT/edu-data/seeds"
SQL_DB="edu"
CONTAINER="mysql-server"
MYSQL=(docker exec -i "$CONTAINER" mysql -uroot -p123321 "$SQL_DB")

if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "ERROR: container '$CONTAINER' is not running."
  exit 1
fi

echo "Copying seeds into container..."
SEED_BASE="/var/lib/mysql-files/edu_seeds"
docker exec "$CONTAINER" rm -rf "$SEED_BASE"
docker exec "$CONTAINER" mkdir -p "$SEED_BASE"
docker cp "$SEEDS_DIR/." "$CONTAINER:$SEED_BASE/"

import_csv() {
  local table="$1"
  local relpath="$2"
  local host_path="$SEEDS_DIR/$relpath"
  local container_path="$SEED_BASE/$relpath"

  if [[ ! -f "$host_path" ]]; then
    echo "SKIP: $relpath not found"
    return 0
  fi

  # Check table exists
  local exists
  exists="$(docker exec "$CONTAINER" mysql -uroot -p123321 -N -e \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='${SQL_DB}' AND table_name='${table}';")"
  if [[ "$exists" != "1" ]]; then
    echo "SKIP: table '$table' not found"
    return 0
  fi

  # Build column list from CSV header
  local header cols
  header="$(head -n 1 "$host_path" | tr -d '\r')"
  IFS=',' read -r -a cols <<< "$header"
  local load_fields=""
  local idx=0
  for c in "${cols[@]}"; do
    c="$(echo "$c" | xargs)"
    [[ -z "$c" ]] && continue
    # If column exists in table, load into it; otherwise load into a user variable and discard.
    if docker exec "$CONTAINER" mysql -uroot -p123321 -N -D "$SQL_DB" -e \
      "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='${SQL_DB}' AND table_name='${table}' AND column_name='${c}';" \
      | grep -qx "1"; then
      load_fields+="\`${c}\`,"
    else
      load_fields+="@skip_${idx},"
    fi
    idx=$((idx + 1))
  done
  load_fields="${load_fields%,}"

  echo "Importing $relpath -> $table"
  # Truncate then load
  docker exec "$CONTAINER" mysql -uroot -p123321 "$SQL_DB" -e \
    "SET FOREIGN_KEY_CHECKS=0; TRUNCATE TABLE \`$table\`; SET FOREIGN_KEY_CHECKS=1;"

  "${MYSQL[@]}" -e \
    "SET FOREIGN_KEY_CHECKS=0;
     LOAD DATA INFILE '${container_path}'
     INTO TABLE \`${table}\`
     CHARACTER SET utf8mb4
     FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '\"' ESCAPED BY '\"'
     LINES TERMINATED BY '\n'
     IGNORE 1 LINES
     (${load_fields});
     SET FOREIGN_KEY_CHECKS=1;"
}

# 1) foundation
import_csv dim_channel "1_foundation/dim_channel.csv"
import_csv dim_course_category "1_foundation/dim_course_category.csv"
import_csv dim_education_level "1_foundation/dim_education_level.csv"
import_csv dim_grade "1_foundation/dim_grade.csv"
import_csv dim_learner_identity "1_foundation/dim_learner_identity.csv"
import_csv dim_learning_goal "1_foundation/dim_learning_goal.csv"
import_csv dim_question_type "1_foundation/dim_question_type.csv"
import_csv org_institution "1_foundation/org_institution.csv"
import_csv org_department "1_foundation/org_department.csv"
import_csv org_campus "1_foundation/org_campus.csv"

# 2) course
import_csv series "2_course/series.csv"
import_csv series_course "2_course/series_course.csv"

# 3) question
import_csv question_bank "3_question/question_bank.csv"
import_csv question "3_question/question.csv"

echo "Done."

