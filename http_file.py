#!/usr/bin/env python

from libs.requests import requests
from urlparse import urlparse
import logging
from Queue import Queue
import anydbm
import thread
from traceback import format_exc
import cPickle

_session_pool = {}

log = logging.getLogger(__name__)

def get_session(url):
  hostname = urlparse(url).hostname
  assert hostname
  session = _session_pool.get(hostname, None)
  if not session:
    session = requests.Session()
    #adapter = requests.adapters.HTTPAdapter(pool_connections=1,pool_maxsize=1,pool_block=True)
    #session.mount('http://', adapter)
    _session_pool[hostname] = session
  log.debug('reusing session for host %s' % hostname)
  return session

def _log_exception_wrapper(func, *args, **kw):
  """Call 'func' with args and kws and log any exception it throws.
  """
  try:
    func(*args, **kw)
    return
  except:
    log.error("exception in function %s", func.__name__)
    log.error(format_exc())


class HTTPFile:
  """ Returns a file handle representing a HTTP file.

  Once it is created, it will check the availablity in a local cache factory. If
  a cached version is not availble, it will immediately issue a background
  thread to download the file into the cache."""
  def __init__(self, url):
    self.url = url
    self.queue = Queue()
    cache = CacheFactory.get()
    log.debug("Test")
    if url not in cache.keys():
      self.start_download_in_background()

  def start_download_in_background(self):
    log.debug("start_download_in_background")
    def _run_thread():
      log.info("start_download_in_background._run_thread")
      session = get_session(self.url)
      data = session.get(self.url).content
      self.queue.put(data)
    thread.start_new_thread(_log_exception_wrapper, (_run_thread,))

  def get_content(self):
    cache = CacheFactory.get()
    data = cache[self.url]
    if data:
      return data
    data = self.queue.get(self.url)
    cache[self.url] = data
    return data


class CacheFactory:
  cache_file = None
  cache_instance = None

  class Cache:
    def __init__(self, cache_file, max_items=10):
      self.db = anydbm.open(cache_file, flag='n')
      self.key_order = self.db.keys()
      self.max_items = max_items

    def __getitem__(self, key):
      if key not in self.key_order:
        return None
      self.mark(key)
      val = self.db.get(str(key))
      return cPickle.loads(val)

    def __setitem__(self, key, value):
      self.db[str(key)] = cPickle.dumps(value)
      self.mark(key)

    def mark(self, key):
      if key in self.key_order:
        self.key_order.remove(key)
      self.key_order.insert(0, key)
      if len(self.key_order) > self.max_items:
        key = self.key_order[-1]
        del self.db[str(key)]
        self.key_order.remove(key)

    def keys(self):
      return sorted(self.key_order)

  @staticmethod
  def get():
    assert CacheFactory.cache_file
    if not CacheFactory.cache_instance:
      log.debug("creating cache factory")
      CacheFactory.cache_instance = CacheFactory.Cache(CacheFactory.cache_file)
    return CacheFactory.cache_instance


if __name__ == '__main__':
  ch = logging.StreamHandler()
  ch.setLevel(logging.DEBUG)
  ch.setFormatter(logging.Formatter(
      '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
  root = logging.getLogger()
  root.addHandler(ch)
  root.setLevel(logging.DEBUG)

  log.info("init")

  from test_photo_list import file_list
  CacheFactory.cache_file = '/tmp/test_http_file'
  files = [HTTPFile(u) for u in file_list]
  for file in files:
    file.get_content()
