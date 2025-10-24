from project.core.settings import get_cached_settings
from project.sqladmin_.create_sqladmin_app import create_sqladmin_app

app = create_sqladmin_app(base_url=get_cached_settings().sqladmin_prefix)
