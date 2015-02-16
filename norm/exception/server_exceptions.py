#!/usr/bin/env python
# encoding: utf-8
'''
Created on June 21, 2013

@author: sarah
'''


class Connection_Error(Exception):
    """
    Exception used to catch connection errors with the timbl server.
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
