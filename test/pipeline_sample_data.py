"""
PL-001: Sample data constants aligned with edu-data seeds.
These constants are used across all pipeline tests for reproducibility.
"""
import re

# Student identity
SAMPLE_STUDENT_ID = "student_pipeline_demo"

# Course: from edu-data/seeds/2_course/series.csv
SAMPLE_SERIES_CODE = "fullstack_development_foundation"
SAMPLE_COURSE_DISPLAY_NAME = "全栈开发系统班"

# Cohort: follows seed naming convention C_<series_code>
SAMPLE_COHORT_CODE = "C_fullstack_development_foundation"
SAMPLE_COHORT_DISPLAY_NAME = "全栈开发系统班 · 默认班"

# Order number: follows ORD-prefix pattern
SAMPLE_ORDER_NO = "ORD20240401005"

ORDER_NO_RE = re.compile(r"^ORD[A-Z0-9_-]+$", re.I)
