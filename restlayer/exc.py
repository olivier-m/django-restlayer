# -*- coding: utf-8 -*-
#
# This file is part of Django restlayer released under the MIT license.
# See the LICENSE for more information.


class HttpException(Exception):
    def __init__(self, msg, status=500):
        super(HttpException, self).__init__(msg, status)


class Http406(HttpException):
    def __init__(self):
        super(HttpException, self).__init__('', 406)


class FormErrors(dict):
    pass


class FormValidationError(HttpException):
    def __init__(self, form):
        super(FormValidationError, self).__init__(FormErrors(form.errors), 400)
