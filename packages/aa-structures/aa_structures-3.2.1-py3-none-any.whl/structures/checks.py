"""Django checks."""

import numbers

from django.conf import settings
from django.core.checks import Warning, register


@register()
def structures_config_check(app_configs, **kwargs):  # pylint: disable=W0613
    """structures_config_check is a Django check that verifies that all periodic tasks
    have been configured correctly in settings.
    """
    if not hasattr(settings, "CELERYBEAT_SCHEDULE"):
        return []

    warnings = []
    for name, obj in settings.CELERYBEAT_SCHEDULE.items():
        _verify_task_config(
            warnings, name, obj, "structures.tasks.update_all_structures"
        )
        _verify_task_config(
            warnings, name, obj, "structures.tasks.fetch_all_notifications"
        )
    return warnings


def _verify_task_config(warnings: list, name: str, obj: dict, task_name: str):
    if obj["task"] != task_name:
        return

    schedule = obj["schedule"]
    if isinstance(schedule, numbers.Number):
        return

    warnings.append(
        Warning(
            (
                "Periodic task has deprecated schedule: "
                f'CELERYBEAT_SCHEDULE["{name}"]'
            ),
            hint=(
                'The value for "schedule" must be a positive number, '
                "not e.g. a cron definition. "
                f"Current value is: {schedule}"
            ),
            id="structures.W001",
        )
    )
