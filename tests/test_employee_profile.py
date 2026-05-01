from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEmployeeProfile(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Users = self.env["res.users"].with_context(no_reset_password=True)
        self.Profile = self.env["university.employee.profile"]
        self.Member = self.env["university.project.member"]
        self.Project = self.env["project.project"]

        self.group_employee = self.env.ref("project_management.employee")
        self.group_admin = self.env.ref("project_management.administrator")
        self.role_manager = self.env.ref("project_management.role_manager")
        self.role_developer = self.env.ref("project_management.role_developer")

        self.user_admin = self.Users.create({
            "name": "Profile Admin",
            "login": "profile_admin",
            "email": "profile_admin@example.com",
            "groups_id": [(6, 0, [self.group_admin.id])],
        })
        self.user_pm = self.Users.create({
            "name": "Profile PM",
            "login": "profile_pm",
            "email": "profile_pm@example.com",
            "groups_id": [(6, 0, [self.group_employee.id])],
        })
        self.user_employee = self.Users.create({
            "name": "Profile Employee",
            "login": "profile_employee",
            "email": "profile_employee@example.com",
            "groups_id": [(6, 0, [self.group_employee.id])],
        })
        self.user_other = self.Users.create({
            "name": "Profile Other",
            "login": "profile_other",
            "email": "profile_other@example.com",
            "groups_id": [(6, 0, [self.group_employee.id])],
        })

        self.project = self.Project.with_user(self.user_admin).create({"name": "Profile Test Project"})
        self.Member.create({
            "project_id": self.project.id,
            "user_id": self.user_pm.id,
            "role_id": self.role_manager.id,
        })
        self.Member.create({
            "project_id": self.project.id,
            "user_id": self.user_employee.id,
            "role_id": self.role_developer.id,
        })

    # ------------------------------------------------------------------
    # Profile creation and uniqueness
    # ------------------------------------------------------------------

    def test_admin_can_create_profile(self):
        profile = self.Profile.with_user(self.user_admin).create({
            "user_id": self.user_employee.id,
            "position": "Senior Dev",
            "degree": "master",
        })
        self.assertEqual(profile.user_id, self.user_employee)
        self.assertEqual(profile.degree, "master")

    def test_duplicate_profile_raises_constraint(self):
        self.Profile.sudo().create({"user_id": self.user_employee.id})
        with self.assertRaises(Exception):
            self.Profile.sudo().create({"user_id": self.user_employee.id})

    def test_employee_can_create_own_profile(self):
        profile = self.Profile.with_user(self.user_employee).create({
            "user_id": self.user_employee.id,
            "position": "Developer",
        })
        self.assertEqual(profile.user_id, self.user_employee)

    # ------------------------------------------------------------------
    # Record rule: employee reads own, manager reads team, admin reads all
    # ------------------------------------------------------------------

    def test_employee_can_read_own_profile(self):
        self.Profile.sudo().create({"user_id": self.user_employee.id, "position": "Dev"})
        result = self.Profile.with_user(self.user_employee).search(
            [("user_id", "=", self.user_employee.id)]
        )
        self.assertEqual(len(result), 1)

    def test_employee_cannot_read_other_profile(self):
        self.Profile.sudo().create({"user_id": self.user_other.id, "position": "Other Dev"})
        result = self.Profile.with_user(self.user_employee).search(
            [("user_id", "=", self.user_other.id)]
        )
        self.assertEqual(len(result), 0)

    def test_manager_can_read_team_member_profile(self):
        self.Profile.sudo().create({"user_id": self.user_employee.id, "position": "Dev"})
        result = self.Profile.with_user(self.user_pm).search(
            [("user_id", "=", self.user_employee.id)]
        )
        self.assertEqual(len(result), 1)

    def test_manager_cannot_read_non_team_member_profile(self):
        self.Profile.sudo().create({"user_id": self.user_other.id})
        result = self.Profile.with_user(self.user_pm).search(
            [("user_id", "=", self.user_other.id)]
        )
        self.assertEqual(len(result), 0)

    def test_admin_can_read_any_profile(self):
        self.Profile.sudo().create({"user_id": self.user_employee.id})
        self.Profile.sudo().create({"user_id": self.user_other.id})
        result = self.Profile.with_user(self.user_admin).search([])
        user_ids = result.mapped("user_id")
        self.assertIn(self.user_employee, user_ids)
        self.assertIn(self.user_other, user_ids)

    # ------------------------------------------------------------------
    # Write permissions
    # ------------------------------------------------------------------

    def test_employee_can_write_own_profile(self):
        profile = self.Profile.sudo().create({"user_id": self.user_employee.id})
        profile.with_user(self.user_employee).write({"position": "Lead Dev"})
        self.assertEqual(profile.position, "Lead Dev")

    def test_employee_cannot_write_other_profile(self):
        profile = self.Profile.sudo().create({"user_id": self.user_other.id})
        with self.assertRaises(AccessError):
            profile.with_user(self.user_employee).write({"position": "Hijacked"})

    def test_admin_can_write_any_profile(self):
        profile = self.Profile.sudo().create({"user_id": self.user_employee.id})
        profile.with_user(self.user_admin).write({"position": "Staff Engineer"})
        self.assertEqual(profile.position, "Staff Engineer")

    # ------------------------------------------------------------------
    # action_open_employee_profile button on member row
    # ------------------------------------------------------------------

    def test_action_open_profile_returns_act_window(self):
        member = self.Member.search([
            ("project_id", "=", self.project.id),
            ("user_id", "=", self.user_employee.id),
        ])
        action = member.with_user(self.user_admin).action_open_employee_profile()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "university.employee.profile")

    def test_action_open_profile_lazy_creates_profile(self):
        existing = self.Profile.sudo().search([("user_id", "=", self.user_employee.id)])
        self.assertFalse(existing)
        member = self.Member.search([
            ("project_id", "=", self.project.id),
            ("user_id", "=", self.user_employee.id),
        ])
        member.with_user(self.user_admin).action_open_employee_profile()
        created = self.Profile.sudo().search([("user_id", "=", self.user_employee.id)])
        self.assertTrue(created)

    def test_action_open_profile_edit_mode_for_self(self):
        member = self.Member.search([
            ("project_id", "=", self.project.id),
            ("user_id", "=", self.user_employee.id),
        ])
        action = member.with_user(self.user_employee).action_open_employee_profile()
        self.assertEqual(action["context"].get("form_view_initial_mode"), "edit")

    def test_action_open_profile_readonly_mode_for_manager(self):
        member = self.Member.search([
            ("project_id", "=", self.project.id),
            ("user_id", "=", self.user_employee.id),
        ])
        action = member.with_user(self.user_pm).action_open_employee_profile()
        self.assertEqual(action["context"].get("form_view_initial_mode"), "readonly")

    def test_action_open_profile_denied_for_unrelated_employee(self):
        member = self.Member.search([
            ("project_id", "=", self.project.id),
            ("user_id", "=", self.user_employee.id),
        ])
        with self.assertRaises(AccessError):
            member.with_user(self.user_other).action_open_employee_profile()

    # ------------------------------------------------------------------
    # Computed workload and project data
    # ------------------------------------------------------------------

    def test_workload_zero_with_no_tasks(self):
        profile = self.Profile.sudo().create({"user_id": self.user_employee.id})
        self.assertEqual(profile.active_task_count, 0)
        self.assertEqual(profile.workload_percent, 0.0)

    def test_project_count_reflects_memberships(self):
        profile = self.Profile.sudo().create({"user_id": self.user_employee.id})
        self.assertEqual(profile.project_count, 1)
        self.assertIn(self.project, profile.project_ids)

    def test_project_count_zero_for_non_member(self):
        profile = self.Profile.sudo().create({"user_id": self.user_other.id})
        self.assertEqual(profile.project_count, 0)

    # ------------------------------------------------------------------
    # Team list: degree/academic_direction from profile
    # ------------------------------------------------------------------

    def test_member_degree_pulled_from_profile(self):
        self.Profile.sudo().create({
            "user_id": self.user_employee.id,
            "degree": "candidate",
            "academic_direction": "Machine Learning",
        })
        member = self.Member.search([
            ("project_id", "=", self.project.id),
            ("user_id", "=", self.user_employee.id),
        ])
        self.assertEqual(member.degree, "Кандидат наук")
        self.assertEqual(member.academic_direction, "Machine Learning")

    def test_member_degree_empty_when_no_profile(self):
        member = self.Member.search([
            ("project_id", "=", self.project.id),
            ("user_id", "=", self.user_employee.id),
        ])
        self.assertEqual(member.degree, "")
        self.assertEqual(member.academic_direction, "")
