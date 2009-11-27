import unittest

class PathObservationTestCase(unittest.TestCase):
    def setUp(self):
        import os
        import tempfile
        tempdir = tempfile.gettempdir()
        f = tempfile.NamedTemporaryFile(dir=tempdir)
        self.tempdir = os.path.join(tempdir, os.path.basename(f.name))
        f.close()
        os.mkdir(self.tempdir)

    def tearDown(self):
        import os
        os.rmdir(self.tempdir)

    def _make_temporary(self, directory=None):
        import os
        import tempfile
        if directory is None:
            directory = self.tempdir
        f = tempfile.NamedTemporaryFile(dir=directory)
        path = os.path.realpath(os.path.dirname(f.name)).rstrip('/') + '/'
        return f, path

    def test_single_file_added(self):
        events = []
        def callback(*args):
            events.append(args)

        f, path = self._make_temporary()
        from fsevents import Stream
        stream = Stream(callback, path)

        from fsevents import Observer
        observer = Observer()
        observer.schedule(stream)
        observer.start()

        # add single file
        import time
        while not observer.isAlive():
            time.sleep(0.1)
        f.flush()
        time.sleep(0.2)

        # stop and join observer
        observer.stop()
        observer.unschedule(stream)
        observer.join()

        f.close()
        self.assertEquals(events, [(path, 0)])

    def test_single_file_added_with_observer_unscheduled(self):
        events = []
        def callback(*args):
            events.append(args)

        f, path = self._make_temporary()
        from fsevents import Stream
        stream = Stream(callback, path)

        from fsevents import Observer
        observer = Observer()
        observer.start()
        import time
        while not observer.isAlive():
            time.sleep(0.1)

        observer.schedule(stream)
        observer.unschedule(stream)

        # add single file
        f.flush()
        time.sleep(0.2)

        # stop and join observer
        observer.stop()
        observer.join()

        f.close()
        self.assertEquals(events, [])

    def test_single_file_added_with_observer_rescheduled(self):
        events = []
        def callback(*args):
            events.append(args)

        f, path = self._make_temporary()
        from fsevents import Stream
        stream = Stream(callback, path)

        from fsevents import Observer
        observer = Observer()
        observer.start()

        import time
        while not observer.isAlive():
            time.sleep(0.1)

        observer.schedule(stream)
        observer.unschedule(stream)
        observer.schedule(stream)

        # add single file
        f.flush()
        time.sleep(0.2)

        # stop and join observer
        observer.stop()
        observer.join()

        f.close()
        self.assertEquals(events, [(path, 0)])

    def test_single_file_added_to_subdirectory(self):
        events = []
        def callback(*args):
            events.append(args)

        import os
        tempdir = self.tempdir
        directory = os.path.join(tempdir, "fsevents")
        directory = os.path.realpath(directory).rstrip('/') + '/'
        if os.path.exists(directory):
            removedir = False
        else:
            os.mkdir(directory)
            removedir = True

        try:
            f, path = self._make_temporary(directory)
            from fsevents import Stream
            stream = Stream(callback, path)

            from fsevents import Observer
            observer = Observer()
            observer.schedule(stream)
            observer.start()

            # add single file
            import time
            while not observer.isAlive():
                time.sleep(0.1)
            f.flush()
            time.sleep(0.2)

            # stop and join observer
            observer.stop()
            observer.unschedule(stream)
            observer.join()

            self.assertEquals(events, [(directory, 0)])
        finally:
            f.close()
            if removedir:
                os.rmdir(directory)

    def test_single_file_added_unschedule_then_stop(self):
        events = []
        def callback(*args):
            events.append(args)

        f, path = self._make_temporary()
        from fsevents import Stream
        stream = Stream(callback, path)

        from fsevents import Observer
        observer = Observer()
        observer.schedule(stream)
        observer.start()

        # add single file
        import time
        while not observer.isAlive():
            time.sleep(0.1)
        f.flush()
        time.sleep(0.2)

        # stop and join observer
        observer.unschedule(stream)
        observer.stop()
        observer.join()

        f.close()
        self.assertEquals(events, [(path, 0)])

    def test_start_then_watch(self):
        events = []
        def callback(*args):
            events.append(args)

        f, path = self._make_temporary()
        from fsevents import Stream
        stream = Stream(callback, path)

        from fsevents import Observer
        observer = Observer()
        observer.schedule(stream)
        observer.start()

        # add single file
        import time
        while not observer.isAlive():
            time.sleep(0.1)
        f.flush()
        time.sleep(0.2)

        # stop and join observer
        observer.stop()
        observer.unschedule(stream)
        observer.join()

        f.close()
        self.assertEquals(events, [(path, 0)])

    def test_start_no_watch(self):
        events = []
        def callback(*args):
            events.append(args)

        from fsevents import Observer
        observer = Observer()

        f, path = self._make_temporary()
        observer.start()

        # add single file
        import time
        while not observer.isAlive():
            time.sleep(0.1)
        f.flush()
        time.sleep(0.2)

        # stop and join observer
        observer.stop()
        observer.join()

        f.close()
        self.assertEquals(events, [])

