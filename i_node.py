import cPickle
import os
import time
from stat import S_IFDIR, S_IFREG

MODE_FILE = 0644 | S_IFREG
MODE_DIR = 0755 | S_IFDIR

class INode(object):

  def __init__(self, **kwargs):
    now = int(time.time())
    self.attr = dict(st_atime = now, st_ctime = now, st_gid = int(os.getgid()),
                     st_mode = MODE_FILE, st_mtime = now, st_nlink = 1,
                     st_size = 0L, st_uid = int(os.getuid()))
    for k in kwargs:
      self.attr[k] = kwargs[k]

  def __getitem__(self, key):
    return self.attr.get(key)

  def __setitem__(self, key, value):
    self.attr[key] = value

  def getattrs(self):
    return self.attr

  @staticmethod
  def root():
    return INode(st_mode = MODE_DIR, st_nlink = 2)

  def mknod(self, **kwargs):
    node = INode(**kwargs)
    if kwargs.get('st_mode', 0) & S_IFDIR:
      node['st_nlink'] = 2
    self['st_nlink'] += 1
    return node
