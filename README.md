FlickrFS Next Generation
===========

Why Flickr?
------
Nowadays it provides 1TB storage for free. Perfect cloud backup solution to my
millions of photos.

Why a FS?
------
I like the idea of mounting flickr photos to a file system. Dictionary is the
most intuitive way to organize photos. Plus, mounting a file system provide
easy integration with the rest of the system to upload/download photos from
Flickr.

Previous flickfs is a very good implementation demostrating this concept.
Unfortuntely it is dead. So I decided to rewrite a new file system to replace
and call it flickrfs-ng.

What's new?
------
FUSE has been improved a lot since its first 1.X branch. However the python-fuse
module is still quite out-of-date. flickrfs-ng will use fusepy instead to provide
python binding.

The original flickrapi is also out-of-maintain, and will be replaced with
python-flickr-api which is in actively development.

* python-flickr-api https://github.com/alexis-mignon/python-flickr-api/
* fusepy https://github.com/terencehonles/fusepy

New features
------
- Indexing by date
  An auto directionary structure will be provided to list photos by date. e.g.
  /mnt/flickr/date/2013-01 refers to the photos taken in Jan 2013, while
  /mnt/flickr/date/2013 refers to all photos taken in year 2013.

- Indexing by tags
  Easily filter photos with given tags.
  /mnt/flickr/tags/newzealand/ will get all photos with tag newzealand

- EXIF integration
  exif info will be used, i.e. the date. The data could be viewed as
  /mnt/flickr/stream/.P23012345.JPG.exif

- Metadata
  Could be found and updated in /mnt/flickr/stream/.P23012345.JPG.meta

- Transparent resizing
  To get a smaller size of photo, just get
  /mnt/flickr/stream/P23012345.1024.JPG
