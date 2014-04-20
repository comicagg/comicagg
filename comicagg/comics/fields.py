# -*- coding: utf-8 -*-
from django.db import models

class ComicNameField(models.CharField):
    
    __metaclass__ = models.SubfieldBase
    
    def __init__(self, *args, **kwargs):
        super(models.CharField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        ret = super(models.CharField, self).to_python(value)
        return try_encodings(ret)

class AltTextField(models.TextField):
    
    __metaclass__ = models.SubfieldBase
    
    def __init__(self, *args, **kwargs):
        super(models.TextField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        ret = super(models.TextField, self).to_python(value)
        return try_encodings(ret)

def try_encodings(value):
    try:
        value = unicode(value, 'utf-8')
    except:
        try:
            value = unicode(value, 'iso-8859-1')
        except:
            pass
    return value 
