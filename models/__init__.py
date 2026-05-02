# ===== BASE REFERENCE MODELS =====
# Foundational models - no dependencies on other project models
from . import project_role
from . import project_type
from . import project_customer
from . import project_trl

# ===== PROJECT PASSPORT SUB-MODELS =====
from . import project_division
from . import project_partner
from . import project_objective
from . import project_result
from . import project_indicator
from . import project_signatory

# ===== MAIN PROJECT MODEL =====
# Core project model with all extensions
from . import project_project

# ===== PROJECT STRUCTURE =====
# Team and organizational structure
from . import project_member
from . import project_stage
from . import project_comment

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
