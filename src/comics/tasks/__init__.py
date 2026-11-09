# Import task modules so that celery.autodiscover_tasks() will work
from . import (
    cleanup_read_strips,
    distribute_strips,
    fix_unreads,
    max_unreads,
    update_comics,
)
