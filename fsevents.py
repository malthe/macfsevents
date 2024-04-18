import os
import sys
import threading
import unicodedata

from _fsevents import (
    CF_POLLIN,
    CF_POLLOUT,
    FS_CFLAGFILEEVENTS,
    FS_CFLAGIGNORESELF,
    FS_CFLAGNODEFER,
    FS_CFLAGNONE,
    FS_CFLAGUSECFTYPES,
    FS_CFLAGWATCHROOT,
    FS_EVENTIDSINCENOW,
    FS_FILEEVENTS,
    FS_FLAGEVENTIDSWRAPPED,
    FS_FLAGHISTORYDONE,
    FS_FLAGKERNELDROPPED,
    FS_FLAGMOUNT,
    FS_FLAGMUSTSCANSUBDIRS,
    FS_FLAGNONE,
    FS_FLAGROOTCHANGED,
    FS_FLAGUNMOUNT,
    FS_FLAGUSERDROPPED,
    FS_IGNORESELF,
    FS_ITEMCHANGEOWNER,
    FS_ITEMCREATED,
    FS_ITEMFINDERINFOMOD,
    FS_ITEMINODEMETAMOD,
    FS_ITEMISDIR,
    FS_ITEMISFILE,
    FS_ITEMISSYMLINK,
    FS_ITEMMODIFIED,
    FS_ITEMREMOVED,
    FS_ITEMRENAMED,
    FS_ITEMXATTRMOD,
    loop,
    schedule,
    stop,
    unschedule
)


class Mask(int):
    stringmap = {
        FS_FLAGMUSTSCANSUBDIRS:    'MustScanSubDirs',
        FS_FLAGUSERDROPPED:        'UserDropped',
        FS_FLAGKERNELDROPPED:      'KernelDropped',
        FS_FLAGEVENTIDSWRAPPED:    'EventIDsWrapped',
        FS_FLAGHISTORYDONE:        'HistoryDone',
        FS_FLAGROOTCHANGED:        'RootChanged',
        FS_FLAGMOUNT:              'Mount',
        FS_FLAGUNMOUNT:            'Unmount',

        # Flags when creating the stream.
        FS_ITEMCREATED:            'ItemCreated',
        FS_ITEMREMOVED:            'ItemRemoved',
        FS_ITEMINODEMETAMOD:       'ItemInodeMetaMod',
        FS_ITEMRENAMED:            'ItemRenamed',
        FS_ITEMMODIFIED:           'ItemModified',
        FS_ITEMFINDERINFOMOD:      'ItemFinderInfoMod',
        FS_ITEMCHANGEOWNER:        'ItemChangedOwner',
        FS_ITEMXATTRMOD:           'ItemXAttrMod',
        FS_ITEMISFILE:             'ItemIsFile',
        FS_ITEMISDIR:              'ItemIsDir',
        FS_ITEMISSYMLINK:          'ItemIsSymlink'
    }

    _svals = list(stringmap.items())
    _svals.sort()

    del stringmap

    def __str__(self):
        vals = []
        for k, s in self._svals:
            if self & k:
                vals.append(s)

        return "[" + "|".join(vals) + "]"


# inotify event flags
IN_MODIFY = 0x00000002
IN_ATTRIB = 0x00000004
IN_CREATE = 0x00000100
IN_DELETE = 0x00000200
IN_MOVED_FROM = 0x00000040
IN_MOVED_TO = 0x00000080

if sys.version_info[0] >= 3:
    unicode = str


def check_path_string_type(*paths):
    for path in paths:
        if not isinstance(path, str):
            raise TypeError(
                "Path must be string, not '%s'." % type(path).__name__)


class Observer(threading.Thread):
    event = None
    runloop = None

    def __init__(self):
        self.streams = set()
        self.schedulings = {}
        self.lock = threading.Lock()
        threading.Thread.__init__(self)

    def run(self):
        # wait until we have streams registered
        while not self.streams:
            self.event = threading.Event()
            self.event.wait()
            if self.event is None:
                return
            self.event = None

        self.lock.acquire()

        try:
            # schedule all streams
            for stream in self.streams:
                self._schedule(stream)

            self.streams = None
        finally:
            self.lock.release()

        # start run-loop
        loop(self)

    def _schedule(self, stream):
        if not stream.paths:
            raise ValueError("No paths to observe.")
        if stream.file_events:
            callback = FileEventCallback(stream.callback, stream.raw_paths)
        else:
            def callback(paths, masks, ids):
                for path, mask, id in zip(paths, masks, ids):
                    if sys.version_info[0] >= 3:
                        path = path.decode('utf-8')
                    if stream.ids is False:
                        stream.callback(path, mask)
                    elif stream.ids is True:
                        stream.callback(path, mask, id)
            
        schedule(self, stream, callback, stream.paths, stream.since, stream.latency, stream.cflags)

    def schedule(self, stream):
        self.lock.acquire()
        try:
            if self.streams is None:
                self._schedule(stream)
            elif stream in self.streams:
                raise ValueError("Stream already scheduled.")
            else:
                self.streams.add(stream)
                if self.event is not None:
                    self.event.set()
        finally:
            self.lock.release()

    def unschedule(self, stream):
        self.lock.acquire()
        try:
            if self.streams is None:
                unschedule(stream)
            else:
                self.streams.remove(stream)
        finally:
            self.lock.release()

    def stop(self):
        if self.event is None:
            stop(self)
        else:
            event = self.event
            self.event = None
            event.set()

class Stream(object):
    def __init__(self, callback, *paths, **options):
        file_events = options.pop('file_events', False)
        since = options.pop('since',FS_EVENTIDSINCENOW)
        cflags = options.pop('flags', FS_CFLAGNONE)
        latency = options.pop('latency', 0.01)
        ids = options.pop('ids', False)
        assert len(options) == 0, "Invalid option(s): %s" % repr(options.keys())
        check_path_string_type(*paths)

        self.callback = callback
        self.raw_paths = paths

        # The C-extension needs the path in 8-bit form.
        self.paths = [
            path if isinstance(path, bytes) 
            else path.encode('utf-8') for path in paths
        ]

        self.file_events = file_events
        self.since = since
        self.cflags = cflags
        self.latency = latency
        self.ids = ids

class FileEvent(object):
    __slots__ = 'mask', 'cookie', 'name'

    def __init__(self, mask, cookie, name):
        self.mask = mask
        self.cookie = cookie
        self.name = name

    def __repr__(self):
        return repr((self.mask, self.cookie, self.name))

class FileEventCallback(object):
    def __init__(self, callback, paths):
        self.snapshots = {}
        for path in paths:
            check_path_string_type(path)
            self.snapshot(path)
        self.callback = callback
        self.cookie = 0

    def __call__(self, paths, masks, ids):
        events = []
        deleted = {}
        created = {}

        for path in sorted(paths):
            # supports UTF-8-MAC(NFD)
            if not isinstance(path, unicode):
                path = path.decode('utf-8')
            path = unicodedata.normalize('NFD', path).encode('utf-8')

            if sys.version_info[0] >= 3:
                path = path.decode('utf-8')
                
            path = path.rstrip('/')
            snapshot = self.snapshots[path]
            current = {}
            try:
                for name in os.listdir(path):
                    try:
                        current[name] = os.lstat(os.path.join(path, name))
                    except OSError:
                        pass
            except OSError:
                # recursive delete causes problems with path being non-existent
                pass
            observed = set(current)

            for name, snap_stat in snapshot.items():
                filename = os.path.join(path, name)
                if name in observed:
                    stat = current[name]
                    if stat.st_mtime > snap_stat.st_mtime:
                        events.append(FileEvent(IN_MODIFY, None, filename))
                    elif stat.st_ctime > snap_stat.st_ctime:
                        events.append(FileEvent(IN_ATTRIB, None, filename))
                    observed.discard(name)
                else:
                    event = created.get(snap_stat.st_ino)
                    if (event is not None):
                        self.cookie += 1
                        event.mask = IN_MOVED_FROM
                        event.cookie = self.cookie
                        tmp_filename = event.name
                        event.name = filename
                        events.append(FileEvent(IN_MOVED_TO, self.cookie, tmp_filename))
                    else:
                        event = FileEvent(IN_DELETE, None, filename)
                        deleted[snap_stat.st_ino] = event
                        events.append(event)

            for name in observed:
                stat = current[name]
                filename = os.path.join(path, name)

                event = deleted.get(stat.st_ino)
                if event is not None:
                    self.cookie += 1
                    event.mask = IN_MOVED_FROM
                    event.cookie = self.cookie
                    event = FileEvent(IN_MOVED_TO, self.cookie, filename)
                else:
                    event = FileEvent(IN_CREATE, None, filename)
                    created[stat.st_ino] = event

                if os.path.isdir(filename):
                    self.snapshot(filename)
                events.append(event)

            snapshot.clear()
            snapshot.update(current)

        for event in events:
            self.callback(event)

    def snapshot(self, path):
        path = os.path.realpath(path)
        refs = self.snapshots

        for root, dirs, files in os.walk(path):
            refs[root] = {}
            entry = refs[root]
            for obj in files + dirs:
                try:
                    entry[obj] = os.lstat(os.path.join(root, obj))
                except OSError:
                    continue
