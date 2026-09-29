"""Independent variation: all task copies succeed together or none survive."""
from services import create_task


def copy_titles(session, project_id, user_id, titles):
    return [create_task(session, project_id, title=title, created_by=user_id)
            for title in titles]
