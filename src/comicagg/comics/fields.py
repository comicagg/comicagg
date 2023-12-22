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
