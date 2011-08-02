import os
import threading
import _fsevents

# inotify event flags
IN_MODIFY = 0x00000002
IN_ATTRIB = 0x00000004
IN_CREATE = 0x00000100
IN_DELETE = 0x00000200
IN_MOVED_FROM = 0x00000040
IN_MOVED_TO = 0x00000080

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
        _fsevents.loop(self)

    def _schedule(self, stream):
        if not stream.paths:
            raise ValueError("No paths to observe.")
        if stream.file_events:
            callback = FileEventCallback(stream.callback, stream.paths)
        else:
            def callback(paths, masks):
                for path, mask in zip(paths, masks):
                    stream.callback(path, mask)
        _fsevents.schedule(self, stream, callback, stream.paths)

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
                _fsevents.unschedule(stream)
            else:
                self.streams.remove(stream)
        finally:
            self.lock.release()

    def stop(self):
        if self.event is None:
            _fsevents.stop(self)
        else:
            event = self.event
            self.event = None
            event.set()

class Stream(object):
    def __init__(self, callback, *paths, **options):
        file_events = options.pop('file_events', False)
        assert len(options) == 0, "Invalid option(s): %s" % repr(options.keys())
        for path in paths:
            if not isinstance(path, str):
                raise TypeError(
                    "Path must be string, not '%s'." % type(path).__name__)

        self.callback = callback
        self.paths = list(paths)
        self.file_events = file_events

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
            self.snapshot(path)
        self.callback = callback
        self.cookie = 0

    def __call__(self, paths, masks):
        events = []
        deleted = {}

        for path in sorted(paths):
            path = path.rstrip('/')
            snapshot = self.snapshots[path]

            current = {}
            try:
                for name in os.listdir(path):
                    try:
                        current[name] = os.stat(os.path.join(path, name))
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
                    observed.discard(name)
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
        refs[path] = {}

        for root, dirs, files in os.walk(path):
            entry = refs[root]
            for filename in files:
                try:
                    entry[filename] = os.stat(os.path.join(root, filename))
                except OSError:
                    continue
            for directory in dirs:
                refs[os.path.join(root, directory)] = {}

        if os.path.isdir(path):
            refs[os.path.join(root, path)] = {}
            for name in os.listdir(os.path.join(root, path)):
                try:
                    refs[path][name] = os.stat(os.path.join(path, name))
                except OSError:
                    pass
