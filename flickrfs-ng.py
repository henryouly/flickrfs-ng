#!/usr/bin/env python

from __future__ import with_statement

import logging
import os

from errno import EACCES, ENOENT
from os.path import realpath
from sys import argv, exit
from threading import Lock
import stat

from libs.fusepy.fuse import FUSE, FuseOSError, Operations, LoggingMixIn
from i_node import INode, MODE_DIR

class Flickrfs(LoggingMixIn, Operations):
  def __init__(self):
    self.logger = logging.getLogger()
    self.home = os.getenv('HOME')
    self.config_dir = os.path.join(self.home, '.flickrfs')
    self.config_file = os.path.join(self.config_dir, 'config.txt')
    self.rwlock = Lock()
    self.nodes = {}
    self.nodes['/'] = INode.root()
    self.nodes['/stream'] = self.nodes['/'].mknod(st_mode = MODE_DIR)

  def getattr(self, path, fh=None):
    if path not in self.nodes.keys():
      raise FuseOSError(ENOENT)
    return self.nodes[path].getattrs()

  def readdir(self, path, fh):
    ret = ['.', '..']
    for x in self.nodes.keys():
      if x == '/':
        continue
      (parent, base) = x.rsplit('/')
      if len(parent) == 0: parent = '/'
      if parent == path:
        ret.append(base)

    return ret


if __name__ == '__main__':
  if len(argv) != 2:
    print('usage: %s <mountpoint>' % argv[0])
    exit(1)

  logging.getLogger().setLevel(logging.DEBUG)
  fuse = FUSE(Flickrfs(), argv[1], foreground=True)
