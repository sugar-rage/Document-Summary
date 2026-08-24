from app.core.auth import CurrentUser
from app.core.db import SupabaseRest


def db_for(user: CurrentUser) -> SupabaseRest:
    return SupabaseRest(user.token)
