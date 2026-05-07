-- Minimal seed rows to satisfy FK constraints for series / series_cohort
-- Safe to re-run.

-- Ensure at least one sys_user
INSERT INTO sys_user (nickname, real_name, mobile, email, gender, avatar_url, birthday, yn, last_login_at, created_at, updated_at)
SELECT
  'admin',
  '系统管理员',
  '13000000000',
  'admin@example.com',
  NULL,
  NULL,
  NULL,
  1,
  NULL,
  NOW(),
  NOW()
WHERE NOT EXISTS (SELECT 1 FROM sys_user);

-- Prepare institution id
SET @institution_id := (SELECT id FROM org_institution ORDER BY id LIMIT 1);

-- Ensure at least one staff role (head_teacher)
INSERT INTO org_staff_role (institution_id, role_code, role_name, role_category, sort_no, yn, created_at, updated_at)
SELECT
  @institution_id,
  'head_teacher',
  '班主任',
  'teacher',
  10,
  1,
  NOW(),
  NOW()
WHERE NOT EXISTS (
  SELECT 1 FROM org_staff_role r WHERE r.institution_id=@institution_id AND r.role_code='head_teacher'
);

-- Ensure at least one staff_profile (head teacher)
SET @user_id := (SELECT id FROM sys_user ORDER BY id LIMIT 1);
SET @role_id := (SELECT id FROM org_staff_role WHERE institution_id=@institution_id AND role_code='head_teacher' ORDER BY id LIMIT 1);
SET @campus_id := (SELECT id FROM org_campus WHERE institution_id=@institution_id ORDER BY id LIMIT 1);
SET @dept_id := (SELECT id FROM org_department WHERE institution_id=@institution_id ORDER BY id LIMIT 1);

INSERT INTO staff_profile (user_id, institution_id, campus_id, dept_id, staff_no, staff_role_id, teacher_intro, yn, created_at, updated_at)
SELECT
  @user_id,
  @institution_id,
  @campus_id,
  @dept_id,
  'T0001',
  @role_id,
  '默认班主任（用于初始化数据导入）',
  1,
  NOW(),
  NOW()
WHERE NOT EXISTS (
  SELECT 1 FROM staff_profile s WHERE s.institution_id=@institution_id AND s.staff_no='T0001'
);

-- Minimal seed rows to satisfy FK constraints for series / series_cohort
-- Safe to re-run (uses deterministic values + INSERT IGNORE where possible)

-- 1) Ensure at least one sys_user
INSERT INTO sys_user (nickname, real_name, mobile, email, gender, avatar_url, birthday, yn, last_login_at, created_at, updated_at)
SELECT
  'admin',
  '系统管理员',
  '13000000000',
  'admin@example.com',
  NULL,
  NULL,
  NULL,
  1,
  NULL,
  NOW(),
  NOW()
WHERE NOT EXISTS (SELECT 1 FROM sys_user);

-- 2) Ensure at least one org_staff_role for the first institution
SET @institution_id := (SELECT id FROM org_institution ORDER BY id LIMIT 1);
INSERT INTO org_staff_role (institution_id, role_code, role_name, role_category, sort_no, yn, created_at, updated_at)
SELECT
  @institution_id,
  'head_teacher',
  '班主任',
  'teacher',
  10,
  1,
  NOW(),
  NOW()
WHERE NOT EXISTS (
  SELECT 1 FROM org_staff_role r WHERE r.institution_id=@institution_id AND r.role_code='head_teacher'
);

-- 3) Ensure at least one staff_profile (head teacher)
SET @user_id := (SELECT id FROM sys_user ORDER BY id LIMIT 1);
SET @role_id := (SELECT id FROM org_staff_role WHERE institution_id=@institution_id AND role_code='head_teacher' ORDER BY id LIMIT 1);
SET @campus_id := (SELECT id FROM org_campus WHERE institution_id=@institution_id ORDER BY id LIMIT 1);
SET @dept_id := (SELECT id FROM org_department WHERE institution_id=@institution_id ORDER BY id LIMIT 1);

INSERT INTO staff_profile (user_id, institution_id, campus_id, dept_id, staff_no, staff_role_id, teacher_intro, yn, created_at, updated_at)
SELECT
  @user_id,
  @institution_id,
  @campus_id,
  @dept_id,
  'T0001',
  @role_id,
  '默认班主任（用于初始化数据导入）',
  1,
  NOW(),
  NOW()
WHERE NOT EXISTS (
  SELECT 1 FROM staff_profile s WHERE s.institution_id=@institution_id AND s.staff_no='T0001'
);

