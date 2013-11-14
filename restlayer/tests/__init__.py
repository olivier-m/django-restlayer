# -*- coding: utf-8 -*-
#
# This file is part of Django restlayer released under the MIT license.
# See the LICENSE for more information.
from django.db import models
from django import forms


class SimpleModel(models.Model):
    foo = models.TextField()
    bar = models.IntegerField()


class SimpleForm(forms.ModelForm):
    class Meta:
        model = SimpleModel
        fields = ('foo', 'bar')


from .test_resources import *
