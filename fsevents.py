import logging
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

# flags from FSEvents to match event types:
FSE_CREATED_FLAG = 0x0100
FSE_MODIFIED_FLAG = 0x1000
FSE_REMOVED_FLAG = 0x0200
FSE_RENAMED_FLAG = 0x0800


# loggin
def logger_init():
    log = logging.getLogger("fsevents")
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("[%(asctime)s %(name)s %(levelname)s] %(message)s"))
    log.addHandler(console_handler)
    log.setLevel(20)
    return log

log = logger_init()


class Observer(threading.Thread):
    event = None
    runloop = None

    def __init__(self, latency=0.01, process_asap=False):
        self.process_asap = process_asap
        self.latency = latency
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
            msg = "No paths to observe."
            log.error(msg)
            raise ValueError(msg)

        if stream.file_events:
            callback = FileEventCallback(stream.callback, stream.paths)
        else:
            def callback(paths, masks):
                for path, mask in zip(paths, masks):
                    stream.callback(path, mask)
        _fsevents.schedule(self, stream, callback, stream.paths,
                 stream.raw_file_events, latency=self.latency)

    def schedule(self, stream):

        def schedule_callback():
            if self.streams is None:
                self._schedule(stream)
            elif stream in self.streams:
                msg = "Stream already scheduled."
                log.error(msg)
                raise ValueError(msg)
            else:
                self.streams.add(stream)
                if self.event is not None:
                    self.event.set()
                if self.process_asap and self.is_alive():
                    while self.streams is not None:
                        pass

        # decide if we want to block and thefore listen for events before all
        # streams have been added or do the oposite
        if self.process_asap:
            log.debug('Processing events asap')
            schedule_callback()
        else:
            self.lock.acquire()
            try:
                schedule_callback()
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
        raw_file_events = options.pop('raw_file_events', False)
        assert len(options) == 0, "Invalid option(s): %s" % repr(options.keys())
        for path in paths:
            if not isinstance(path, str):
                raise TypeError(
                    "Path must be string, not '%s'." % type(path).__name__)

        self.callback = callback
        self.paths = list(paths)
        self.file_events = file_events
        self.raw_file_events = raw_file_events


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

        paths_masks = zip(paths, masks)
        log.debug('Processing paths with masks:%s', paths_masks)
        for path, mask in sorted(paths_masks):
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
                    log.debug('File "%s" is observed')
                    stat = current[name]
                    if stat.st_mtime != snap_stat.st_mtime:
                        event = FileEvent(IN_MODIFY, None, filename)
                        log.debug('Appending event "%s"', event)
                        events.append(event)
                        if not mask & FSE_MODIFIED_FLAG:
                            log.debug("No matching flag for detected modify")
                    elif stat.st_ctime > snap_stat.st_ctime:
                        event = FileEvent(IN_ATTRIB, None, filename)
                        log.debug('Appending event "%s"', event)
                        events.append(event)
                    observed.discard(name)
                else:
                    event = FileEvent(IN_DELETE, None, filename)
                    deleted[snap_stat.st_ino] = event
                    log.debug('Appending event "%s"', event)
                    events.append(event)
                    if ((not mask & FSE_REMOVED_FLAG) and
                            (not mask & FSE_RENAMED_FLAG)):
                        log.debug("delete detected with no "
                                  "delete or rename flag")

            for name in observed:
                stat = current[name]
                filename = os.path.join(path, name)

                event = deleted.get(stat.st_ino)
                if event is not None:
                    self.cookie += 1
                    event.mask = IN_MOVED_FROM
                    event.cookie = self.cookie
                    moved_to_event = FileEvent(IN_MOVED_TO, self.cookie,
                            filename)
                    log.debug('Appending event "%s"', event)
                    events.append(moved_to_event)
                    if not mask & FSE_RENAMED_FLAG:
                        log.debug('Rename detected without matching flag')
                else:
                    in_create_event = FileEvent(IN_CREATE, None, filename)
                    log.debug('Appending event "%s"', in_create_event)
                    events.append(in_create_event)
                    modified_event = FileEvent(IN_MODIFY, None, filename)
                    log.debug('Appending event "%s"', modified_event)
                    events.append(modified_event)

                    if not mask & FSE_MODIFIED_FLAG:
                        log.debug('Adding IN_MODIFY event when the flag was'
                                  ' missing. Possible reason was a copy.')

                    if not mask & FSE_CREATED_FLAG:
                        log.debug("Create detected from snapshot"
                                 "but event is not marked as create")

                if os.path.isdir(filename):
                    self.snapshot(filename)

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
