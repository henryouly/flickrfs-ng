import anydbm
import logging
import thread, threading
from stat import S_IFREG
from traceback import format_exc

import libs.python_flickr_api.flickr_api as flickr

log = logging.getLogger('flickrfs-ng')

#Utility functions.
NUMRETRIES = 3
def _log_exception_wrapper(func, *args, **kw):
  """Call 'func' with args and kws and log any exception it throws.
  """
  for i in range(0, NUMRETRIES):
    log.debug("retry attempt %s for func %s", i, func.__name__)
    try:
      func(*args, **kw)
      return
    except:
      log.error("exception in function %s", func.__name__)
      log.error(format_exc())

def getTakenDateStr(photo):
  return photo.taken.split(' ', 1)[0]

def getTakenDate(photo):
  import time
  return time.mktime(time.strptime("%Y-%m-%d %H:%M:%S", photo.taken))

def _get_unix_perms(isfriend, isfamily, ispublic):
  perms = 0744
  if isfriend:
    perms |= 0010
  if isfamily:
    perms |= 0020
  if ispublic:
    perms |= 0011
  return perms


class PhotoStream:
  def __init__(self, inode, path, user):
    self.stream_inode = inode
    self.path = path
    self.photos = dict()
    self.syncer = PhotoSyncer(user, self.add_photo)
    self.syncer.start_sync_thread()

  def add_photo(self, photo):
    photo.filename = self._get_filename(photo)
    log.info("adding photo " + photo.filename)
    photo.inode = self.stream_inode.mknod(st_mode = S_IFREG | photo.mode,
                                          st_ctime = photo.upload,
                                          st_mtime = photo.update)
    self.photos[photo.filename] = photo

  def getattr(self, path, fh=None):
    (parent, base) = path.rsplit('/', 1)
    assert parent == self.path
    return self.photos[base].inode.getattrs()

  def file_list(self):
    return self.photos.keys()

  def _get_filename(self, photo):
    existing = self.photos.keys()
    filebase = photo.title
    if len(filebase) == 0:
      filebase = getTakenDateStr(photo)
    while (filebase + "." + photo.ext) in existing:
      filesplit = filebase.rsplit(' ', 1)
      num = 0
      if len(filesplit) == 2:
        try:
          num = int(filesplit[1])
        except ValueError:
          pass
      if num > 0:
        num += 1
        new_base = filesplit[0]
      else:
        num = 1
        new_base = filebase
      filebase = "%s %03d" % (new_base, num)
    return "%s.%s" % (filebase, photo.ext)


class PhotoSyncer:
  def __init__(self, user, photo_sync_callback, sync_interval=300):
    self.user = user
    self.sync_callback = photo_sync_callback
    self.sync_interval = sync_interval

  def populate_stream_thread(self):
    log.info("populate_stream_thread start")
    pages = 1
    current_page = 1
    while current_page <= pages:
      photos = self.user.getPhotos(per_page=500, page=current_page,
                                   extras="original_format,last_update,date_upload,date_taken")
      pages = photos.info.pages
      for p in photos:
        if self.sync_callback:
          self.sync_callback(Photo(p))
      current_page += 1
    log.info("populate_stream_thread end")

  def update_stream_thread(self):
    # To implement
    pass

  def start_sync_thread(self):
    thread.start_new_thread(_log_exception_wrapper,
                            (self.populate_stream_thread, ))


class Photo(object):
  def __init__(self, photo):
    self.id = photo.id
    self.title = photo.title.replace('/', '_')
    self.mode = _get_unix_perms(photo.isfriend, photo.isfamily, photo.ispublic)
    self.ext = photo.originalformat
    self.taken = photo.datetaken
    self.upload = int(photo.dateupload)
    self.update = photo.lastupdate
    self.filename = None
    self.inode = None

  def data(self, start=0, end=0):
    cache = PhotoCache.instance()
    if cache.has_cache(self.id, start, end):
      return cache.get(self.id, start, end)




class PhotoCache(object):
  instance = None
  cache_file = None

  def __init__(self, cache_file):
    assert PhotoCache.cache_file is not None
    self.db = anydbm.open(PhotoCache.cache_file, flag='c')
    self.keys = set()

  def has_cache(self, key, start, end):
    if not db.has_key(key):
      return False


  @staticmethod
  def set_cache_file(file):
    PhotoCache.cache_file = file

  @staticmethod
  def instance():
    if not isinstance(PhotoCache._instance, PhotoCache):
      PhotoCache.instance = PhotoCache()
      return PhotoCache.instance

