# -*- coding: utf-8 -*-
import contextlib
from django.db import models

class ComicNameField(models.CharField):
    def __init__(self, *args, **kwargs):
        super(ComicNameField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        ret = super(ComicNameField, self).to_python(value)
        return try_encodings(ret)

class AltTextField(models.TextField):
    def __init__(self, *args, **kwargs):
        super(AltTextField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        ret = super(AltTextField, self).to_python(value)
        return try_encodings(ret)

def try_encodings(value):
    try:
        value = unicode(value, 'utf-8')
    except Exception:
        with contextlib.suppress(Exception):
            value = unicode(value, 'iso-8859-1')
    return value
