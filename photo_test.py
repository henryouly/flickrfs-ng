#!/usr/bin/env python
"""Tests for photo."""

import logging
import photo
import sys
import time
import unittest

from stat import S_IFREG

class MockINode:
  def __init__(self):
    self.attr = {}

  def mknod(self, *args, **kw):
    node = MockINode()
    for key in kw:
      node.attr[key] = kw[key]
    return node

  def __getitem__(self, key, default=None):
    if not key in self.attr:
      return default
    return self.attr[key]

class MockPhoto:
  def __init__(self, *args, **kw):
    self.attr = kw

  def __getattr__(self, key):
    return self.__dict__['attr'][key]

class MockUser:
  def getPhotos(self):
    return [
        MockPhoto(id=1,lastupdate=1,dateuploaded=1,title="Photo 1",originalformat='jpg',
                  taken='2001-01-01 01:01:01',ispublic=1,isfamily=1,isfriend=1),
        MockPhoto(id=2,lastupdate=2,dateuploaded=2,title="Photo 2",originalformat='png',
                  taken='2001-01-01 01:01:01',ispublic=0,isfamily=1,isfriend=1),
        MockPhoto(id=3,lastupdate=2,dateuploaded=2,title="",originalformat='png',
                  taken='2001-01-01 01:01:01',ispublic=1,isfamily=0,isfriend=0),
        MockPhoto(id=4,lastupdate=2,dateuploaded=2,title="",originalformat='png',
                  taken='2001-01-01 01:01:01',ispublic=0,isfamily=0,isfriend=1),
        MockPhoto(id=5,lastupdate=2,dateuploaded=2,title="",originalformat='png',
                  taken='2001-01-01 01:01:01',ispublic=0,isfamily=1,isfriend=0),
        MockPhoto(id=6,lastupdate=2,dateuploaded=1,title="P6",originalformat='png',
                  taken='2001-01-01 01:01:01',ispublic=0,isfamily=0,isfriend=0),
    ]

class PhotoStreamTest(unittest.TestCase):

  def setUp(self):
    self.inode = MockINode()
    self.pstream = photo.PhotoStream(self.inode, '/stream', MockUser())
    time.sleep(1)

  def test(self):
    self.assertEqual(len(self.pstream.photos), 6)
    self.assertTrue('Photo 1.jpg' in self.pstream.photos.keys())
    self.assertTrue('Photo 2.png' in self.pstream.photos.keys())
    self.assertTrue('2001-01-01.png' in self.pstream.photos.keys())
    self.assertTrue('2001-01-01 001.png' in self.pstream.photos.keys())
    self.assertTrue('2001-01-01 002.png' in self.pstream.photos.keys())
    self.assertTrue('P6.png' in self.pstream.photos.keys())
    self.assertFalse('Photo 3.png' in self.pstream.photos.keys())
    self.assertFalse('2001-01-01 003.png' in self.pstream.photos.keys())
    self.assertEqual(self.pstream.photos['Photo 1.jpg']['st_mode'],
                     S_IFREG | 0775)
    self.assertEqual(self.pstream.photos['Photo 2.png']['st_mode'],
                     S_IFREG | 0774)
    self.assertEqual(self.pstream.photos['2001-01-01.png']['st_mode'],
                     S_IFREG | 0755)
    self.assertEqual(self.pstream.photos['2001-01-01 001.png']['st_mode'],
                     S_IFREG | 0754)
    self.assertEqual(self.pstream.photos['2001-01-01 002.png']['st_mode'],
                     S_IFREG | 0764)
    self.assertEqual(self.pstream.photos['P6.png']['st_mode'],
                     S_IFREG | 0744)
    self.assertEqual(self.pstream.photos['P6.png']['st_mtime'],2)
    self.assertEqual(self.pstream.photos['P6.png']['st_ctime'],1)


if __name__ == '__main__':
  root = logging.getLogger()
  handler = logging.StreamHandler(sys.stdout)
  handler.setLevel(logging.DEBUG)
  root.addHandler(handler)
  unittest.main()
