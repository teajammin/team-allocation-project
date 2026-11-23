"""The views of the application.

The views are grouped into modules. They are all imported here, so that
other code can keep using them as views.home, views.user_list, and so on.
"""

from .session_views import dashboard, home, log_in, log_out
from .allocation_views import (
    allocation_create,
    allocation_export,
    allocation_run_detail,
    cohort_upload,
    project_create,
    project_detail,
    project_list,
)
from .user_management_views import (
    password,
    profile,
    superuser_required,
    user_create,
    user_delete,
    user_detail,
    user_list,
    user_update,
)
