import threading
import _fsevents

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
        _fsevents.schedule(self, stream, stream.callback, stream.paths)

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
    def __init__(self, callback, *paths):
        for path in paths:
            if not isinstance(path, str):
                raise TypeError("Path must be string, not '%s'." % type(path).__name__)
        self.callback = callback
        self.paths = list(paths)
