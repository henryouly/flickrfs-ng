#!/usr/bin/env python

from __future__ import with_statement

import logging, logging.handlers
import os

from errno import EACCES, ENOENT
from sys import argv, exit
from threading import Lock

from libs.fusepy.fuse import FUSE, FuseOSError, Operations, LoggingMixIn
import libs.python_flickr_api.flickr_api as flickr
from i_node import INode, MODE_DIR, MODE_FILE
from oauth_http_server import OAuthHTTPServer
from photo import PhotoStream
from ConfigParser import ConfigParser


class Flickrfs(LoggingMixIn, Operations):
  def __init__(self):
    self.rwlock = Lock()
    self.nodes = {}
    self.__init_config()
    self.__init_logging()
    self.__init_fs()
    self.__auth()
    self.photo_stream = PhotoStream(self.nodes['/stream'], '/stream', self.user)
    self.fd = 0
    #self._get_photos()

  def __init_logging(self):
    logger = logging.getLogger()
    handler = logging.handlers.RotatingFileHandler(self.log_file, "a", 5242880, 3)
    formatter = logging.Formatter(
        "%(asctime)s %(name)-14s %(levelname)-7s %(threadName)-10s %(funcName)-22s %(message)s", "%x %X")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

  def __init_fs(self):
    self.nodes['/'] = INode.root()
    self.nodes['/tags'] = self.nodes['/'].mknod(st_mode = MODE_DIR)
    self.nodes['/tags/personal'] = self.nodes['/tags'].mknod(st_mode = MODE_DIR)
    self.nodes['/tags/public'] = self.nodes['/tags'].mknod(st_mode = MODE_DIR)
    self.nodes['/sets'] = self.nodes['/'].mknod(st_mode = MODE_DIR)
    self.nodes['/date'] = self.nodes['/'].mknod(st_mode = MODE_DIR)
    self.nodes['/stream'] = self.nodes['/'].mknod(st_mode = MODE_DIR)
    self.nodes['/user'] = self.nodes['/'].mknod(st_mode = MODE_FILE)

  def __init_config(self):
    self.home = os.getenv('HOME')
    self.config_dir = os.path.join(self.home, '.flickrfs-ng')
    self.config_file = os.path.join(self.config_dir, 'config.txt')
    self.auth_file = os.path.join(self.config_dir, 'auth.txt')
    self.log_file = os.path.join(self.config_dir, 'flickrfs-ng.log')
    self.browser = "/usr/bin/x-www-browser"
    if os.path.exists(self.config_file):
      config = ConfigParser()
      config.read(self.config_file)
      self.browser = config.get('flickrfs-ng', 'browser')

  def __auth(self):
    print "Start authenticate..."
    if os.path.exists(self.auth_file):
      a = flickr.auth.AuthHandler.load(self.auth_file)
    else:
      server = OAuthHTTPServer()
      a = flickr.auth.AuthHandler(callback='http://localhost:%d/verifier' %
                                server.port)
      pid = os.fork()
      if pid == 0:
        os.system("%s '%s'" % (self.browser, a.get_authorization_url('write')))
        exit(0)
      try:
        server.serve_forever()
      except IOError:
        # safely ignore
        pass
      a.set_verifier(server.oauth_verifier)
      a.save(self.auth_file)
    flickr.set_auth_handler(a)
    print "Login..."
    self.user = flickr.test.login()
    print "Authentication done."

  def _get_photos(self):
    photos = self.user.getPhotos(per_page=500)
    print photos.info.pages
    print photos.info.page
    print photos.info.total
    for photo in photos:
      print photo.id, photo.title.encode('utf-8')

  def getattr(self, path, fh=None):
    if path.startswith('/stream/'):
      attr = self.photo_stream.getattr(path, fh)
      if not attr:
        raise FuseOSError(ENOENT)
      return attr
    if path not in self.nodes.keys():
      raise FuseOSError(ENOENT)
    return self.nodes[path].getattrs()

  def readdir(self, path, fh):
    if path.startswith('/stream'):
      return ['.', '..'] + self.photo_stream.file_list()
    p = [x.rsplit('/', 1) for x in self.nodes.keys()]
    if path == '/':
      path = ''
    return [t[1] for t in p if t[0] == path and len(t[1]) > 0] + ['.', '..']

  def read(self, path, size, offset, fh):
    log.info("%s offset %s length %s", path, offset, size)
    if path.startswith('/stream'):
      return self.photo_stream.read(path, size, offset)

  def open(self, path, flags):
    # if open is called with read flag, it should notify the photo_stream to
    # prefetch file content
    log.info("path: %s flags: %d" % (path, flags))
    if path.startswith('/stream'):
      self.photo_stream.prefetch_file(path)
    self.fd += 1
    return self.fd

  def statfs(self, path):
    return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)


if __name__ == '__main__':
  if len(argv) != 2:
    print('usage: %s <mountpoint>' % argv[0])
    exit(1)

  log = logging.getLogger()
  fuse = FUSE(Flickrfs(), argv[1], foreground=True)
