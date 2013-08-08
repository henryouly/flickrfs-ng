#!/usr/bin/env python

from __future__ import with_statement

import logging
import os

from errno import EACCES, ENOENT
from sys import argv, exit
from threading import Lock

from libs.fusepy.fuse import FUSE, FuseOSError, Operations, LoggingMixIn
import libs.python_flickr_api.flickr_api as fapi
import libs.python_flickr_api.flickr_api.keys as fapi_keys
from libs.python_flickr_api.flickr_api.auth import AuthHandler
from i_node import INode, MODE_DIR, MODE_FILE

flickrAPIKey = "f8aa9917a9ae5e44a87cae657924f42d"  # API key
flickrSecret = "3fbf7144be7eca28"  # shared "secret"

class Flickrfs(LoggingMixIn, Operations):
  def __init__(self):
    self.logger = logging.getLogger()
    self.rwlock = Lock()
    self.nodes = {}
    self.__init_fs()
    self.__init_config()
    self.__auth()

  def __init_fs(self):
    self.nodes['/'] = INode.root()
    self.nodes['/tags'] = self.nodes['/'].mknod(st_mode = MODE_DIR)
    self.nodes['/tags/personal'] = self.nodes['/tags'].mknod(st_mode = MODE_DIR)
    self.nodes['/tags/public'] = self.nodes['/tags'].mknod(st_mode = MODE_DIR)
    self.nodes['/sets'] = self.nodes['/'].mknod(st_mode = MODE_DIR)
    self.nodes['/date'] = self.nodes['/'].mknod(st_mode = MODE_DIR)
    self.nodes['/stream'] = self.nodes['/'].mknod(st_mode = MODE_DIR)
    self.nodes['/stream/file'] = self.nodes['/stream'].mknod(st_mode = MODE_FILE)

  def __init_config(self):
    self.home = os.getenv('HOME')
    self.config_dir = os.path.join(self.home, '.flickrfs-ng')
    self.config_file = os.path.join(self.config_dir, 'config.txt')
    self.auth_file = os.path.join(self.config_dir, 'auth.txt')
    fapi_keys.set_keys(api_key=flickrAPIKey, api_secret=flickrSecret)

  def __auth(self):
    if os.path.exists(self.auth_file):
      a = AuthHandler.load(self.auth_file)
    else:
      a = AuthHandler('http://localhost')
      a.get_authorization_url('write')
      a.write(self.auth_file)
    fapi.set_auth_handler(a)

  def getattr(self, path, fh=None):
    if path not in self.nodes.keys():
      raise FuseOSError(ENOENT)
    return self.nodes[path].getattrs()

  def readdir(self, path, fh):
    p = [x.rsplit('/', 1) for x in self.nodes.keys()]
    if path == '/':
      path = ''
    return [t[1] for t in p if t[0] == path and len(t[1]) > 0] + ['.', '..']

  def read(self, path, size, offset, fh):
    log.debug("%s offset %s length %s", path, offset, size)


if __name__ == '__main__':
  if len(argv) != 2:
    print('usage: %s <mountpoint>' % argv[0])
    exit(1)

  logging.getLogger().setLevel(logging.DEBUG)
  fuse = FUSE(Flickrfs(), argv[1], foreground=True)
