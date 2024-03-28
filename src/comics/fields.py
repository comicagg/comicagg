from django.db import models


class ComicNameField(models.CharField):
    def __init__(self, *args, **kwargs):
        super(ComicNameField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        return super(ComicNameField, self).to_python(value)


class AltTextField(models.TextField):
    def __init__(self, *args, **kwargs):
        super(AltTextField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        return super(AltTextField, self).to_python(value)


class ComicStatus(models.IntegerChoices):
    """
    Comics can be:
    - Inactive: comic should not be shown to users.
    - Active: comic gets updated regularly.
    - Ended: comic has ended. Does not get updates.
    - Broken: does not work. Must be reconfigured by an admin.
    """

    INACTIVE = 0, "Inactive. Never shown"
    ACTIVE = 1, "Active"
    ENDED = 2, "Ended"
    BROKEN = 3, "Broken"
