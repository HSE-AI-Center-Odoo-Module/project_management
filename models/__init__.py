# ===== BASE REFERENCE MODELS =====
# Foundational models - no dependencies on other project models
from . import project_role
from . import project_type
from . import project_customer

# ===== MAIN PROJECT MODEL =====
# Core project model with all extensions
from . import project_project

# ===== PROJECT STRUCTURE =====
# Team and organizational structure
from . import project_member
from . import project_stage

# ===== PROJECT TASKS =====
# Task management
from . import project_task
from . import project_stage_sync_wizard
from . import task_tab
from . import task_approval_item
from . import task_tab_comment
from . import task_approval_comment

# ===== PROJECT RESOURCES =====
# Documents and links attached to projects
from . import project_document
from . import project_link

# ===== EMPLOYEE PROFILE =====
from . import employee_profile
from . import employee_certification

# ===== SYSTEM EXTENSIONS =====
# Extended Odoo system models
from . import res_users
