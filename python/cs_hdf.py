"""
This file contains some helper functions for interfacing with hdf5 files

author=Martin Lichtman
created=2014-01-09
modified>=2014-01-09
"""

__author__ = 'Martin Lichtman'

def dict2hdf(dict,hdf):
    for i in dict:
        hdf[i]=dict[i]
        

#TODO: complete this
# class hdf2dict(object):
#     '''A class to iterface with an hdf5 group using the python dict syntax.'''
#     def __init__(self,hdf):
#         self.hdf=hdf
#     def keys(self):
#     def values(self):
#     def items(self):
#     def has_key(self):
#     def get(self):
#     def clear(self):
#     def setdefault(self):
#     def iterkeys(self):
#     def itervalues(self):
#     def iteritems(self):
#     def pop(self):
#     def popitem(self):
#     def copy(self):
#     def update(self):
#     def __len__(self):
#     def __getitem__(self,key):
#     def __setitem__(self,key,value):
#     def __delitem__(self,key):
#     def __iter__(self):
#     def __contains__(self,item):