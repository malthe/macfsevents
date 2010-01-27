import unittest

class PathObservationTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = self._make_tempdir()

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

    def _make_tempdir(self):
        import os
        import tempfile
        tempdir = tempfile.gettempdir()
        f = tempfile.NamedTemporaryFile(dir=tempdir)
        tempdir = os.path.join(tempdir, os.path.basename(f.name))
        f.close()
        os.mkdir(tempdir)
        return tempdir

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
        time.sleep(0.1)
        f.flush()
        time.sleep(0.2)

        # stop and join observer
        observer.stop()
        observer.unschedule(stream)
        observer.join()

        f.close()
        self.assertEquals(events, [(path, 0)])

    def test_multiple_files_added(self):
        events = []
        def callback(*args):
            events.append(args)

        from fsevents import Observer
        observer = Observer()
        from fsevents import Stream
        observer.start()

        # wait until activation
        import time
        while not observer.isAlive():
            time.sleep(0.1)
        time.sleep(0.1)

        # two files in same directory
        import os
        path1 = os.path.realpath(self._make_tempdir()) + '/'
        f = self._make_temporary(path1)[0]
        g = self._make_temporary(path1)[0]

        # one file in a separate directory
        path2 = os.path.realpath(self._make_tempdir()) + '/'
        h = self._make_temporary(path2)[0]

        stream = Stream(callback, path1, path2)
        observer.schedule(stream)

        try:
            f.flush()
            g.flush()
            h.flush()
            time.sleep(1.0)
            self.assertEqual(sorted(events), sorted([(path1, 0), (path2, 0)]))
        finally:
            f.close()
            g.close()
            h.close()
            os.rmdir(path1)
            os.rmdir(path2)

            # stop and join observer
            observer.stop()
            observer.unschedule(stream)
            observer.join()

    def test_single_file_added_multiple_streams(self):
        events = []
        def callback(*args):
            events.append(args)

        f, path = self._make_temporary()
        from fsevents import Stream
        stream1 = Stream(callback, path)
        stream2 = Stream(callback, path)

        from fsevents import Observer
        observer = Observer()
        observer.schedule(stream1)
        observer.schedule(stream2)
        observer.start()

        # add single file
        import time
        while not observer.isAlive():
            time.sleep(0.1)
        time.sleep(0.1)
        f.flush()
        time.sleep(0.2)

        # stop and join observer
        observer.stop()
        observer.unschedule(stream1)
        observer.unschedule(stream2)
        observer.join()

        f.close()
        self.assertEquals(events, [(path, 0), (path, 0)])

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
        directory = self._make_tempdir()
        subdirectory = os.path.realpath(os.path.join(directory, 'subdir')) + '/'
        os.mkdir(subdirectory)
        import time
        time.sleep(1)
        f, path = self._make_temporary(subdirectory)

        try:
            from fsevents import Stream
            stream = Stream(callback, directory)

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

            self.assertEquals(events, [(subdirectory, 0)])
        finally:
            f.close()
            os.rmdir(subdirectory)
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

