"""PL-001: Validate sample data constants are non-empty and well-formed."""
import test.pipeline_sample_data as d


def test_pl001_student_id_nonempty():
    assert d.SAMPLE_STUDENT_ID.strip()


def test_pl001_course_and_cohort_nonempty():
    assert d.SAMPLE_SERIES_CODE.strip()
    assert d.SAMPLE_COURSE_DISPLAY_NAME.strip()
    assert d.SAMPLE_COHORT_CODE.strip()
    assert d.SAMPLE_COHORT_DISPLAY_NAME.strip()


def test_pl001_order_no_pattern():
    assert d.ORDER_NO_RE.match(d.SAMPLE_ORDER_NO)


def test_pl001_cohort_code_follows_seed_convention():
    assert d.SAMPLE_COHORT_CODE.startswith("C_")
    assert d.SAMPLE_SERIES_CODE in d.SAMPLE_COHORT_CODE
