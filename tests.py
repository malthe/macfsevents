import unittest

class BaseTestCase(unittest.TestCase):
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
        f.flush()
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

class PathObservationTestCase(BaseTestCase):
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
        del events[:]
        f.close()
        time.sleep(1.1)

        # stop and join observer
        observer.stop()
        observer.unschedule(stream)
        observer.join()

        self.assertEquals(events[0][0], path)

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
            del events[:]
            f.close()
            g.close()
            h.close()
            time.sleep(0.2)
            events = [e[0] for e in events]
            self.assertEqual(sorted(events), sorted([path1, path2]))
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
        del events[:]
        f.close()
        time.sleep(0.2)

        # stop and join observer
        observer.stop()
        observer.unschedule(stream1)
        observer.unschedule(stream2)
        observer.join()

        self.assertEquals(events[0][0], path)
        self.assertEquals(events[1][0], path)

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
        del events[:]
        f.close()
        time.sleep(0.1)

        # stop and join observer
        observer.stop()
        observer.join()

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
        del events[:]
        f.close()
        time.sleep(0.2)

        # stop and join observer
        observer.stop()
        observer.join()

        self.assertEquals(events[0][0], path)

    def test_single_file_added_to_subdirectory(self):
        events = []
        def callback(*args):
            events.append(args)

        import os
        directory = self._make_tempdir()
        subdirectory = os.path.realpath(os.path.join(directory, 'subdir')) + '/'
        os.mkdir(subdirectory)
        import time
        time.sleep(0.1)

        try:
            from fsevents import Stream
            stream = Stream(callback, directory)

            from fsevents import Observer
            observer = Observer()
            observer.schedule(stream)
            observer.start()

            # add single file
            while not observer.isAlive():
                time.sleep(0.1)
            del events[:]
            f = open(os.path.join(subdirectory, "test"), "w")
            f.write("abc")
            f.close()
            time.sleep(0.2)

            # stop and join observer
            observer.stop()
            observer.unschedule(stream)
            observer.join()

            self.assertEquals(len(events), 1)
            self.assertEquals(events[0][0], subdirectory)
        finally:
            os.unlink(f.name)
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
        del events[:]
        f.close()
        time.sleep(0.2)

        # stop and join observer
        observer.unschedule(stream)
        observer.stop()
        observer.join()

        self.assertEquals(events[0][0], path)

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
        del events[:]
        f.close()
        time.sleep(0.2)

        # stop and join observer
        observer.stop()
        observer.unschedule(stream)
        observer.join()

        self.assertEquals(events[0][0], path)

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
        del events[:]
        f.close()
        time.sleep(0.2)

        # stop and join observer
        observer.stop()
        observer.join()

        self.assertEquals(events, [])

class FileObservationTestCase(BaseTestCase):
    def test_single_file_created(self):
        events = []
        def callback(event):
            events.append(event)

        from fsevents import Stream
        stream = Stream(callback, self.tempdir, file_events=True)

        from fsevents import Observer
        observer = Observer()
        observer.schedule(stream)
        observer.start()

        # add single file
        import time
        while not observer.isAlive():
            time.sleep(0.1)
        del events[:]
        time.sleep(0.1)
        import os
        f = open(os.path.join(self.tempdir, "test"), "w")
        f.write("abc")
        f.flush()
        f.close()
        time.sleep(0.1)

        # stop and join observer
        observer.stop()
        observer.unschedule(stream)
        observer.join()

        os.unlink(f.name)
        from fsevents import IN_CREATE, IN_MODIFY
        # We get to events, create and modify
        self.assertEquals(len(events), 2)
        self.assertEquals(events[0].mask, IN_CREATE)
        self.assertEquals(events[0].name, os.path.realpath(f.name))
        self.assertEquals(events[1].mask, IN_MODIFY)
        self.assertEquals(events[1].name, os.path.realpath(f.name))

    def _assert_action_after_watcher(self, process_asap, assertions_cb):
        events = []
        def callback(event):
            events.append(event)

        import os
        import time
        from fsevents import Stream
        from fsevents import Observer

        observer = Observer(process_asap=process_asap)
        observer.start()

        stream = Stream(callback, self.tempdir, file_events=True)
        observer.schedule(stream)
        # add single file
        del events[:]
        f = open(os.path.join(self.tempdir, "test"), "w")
        f.write("abc")
        f.flush()
        f.close()
        time.sleep(0.2)

        # stop and join observer
        observer.stop()
        observer.unschedule(stream)
        observer.join()

        os.unlink(f.name)
        assertions_cb(events, f)

    def test_single_file_created_just_after_the_watcher(self):

        def assertions_cb(events, f):
            import os
            from fsevents import IN_CREATE, IN_MODIFY
            self.assertEquals(len(events), 2)
            self.assertEquals(events[0].mask, IN_CREATE)
            self.assertEquals(events[0].name, os.path.realpath(f.name))
            self.assertEquals(events[1].mask, IN_MODIFY)
            self.assertEquals(events[1].name, os.path.realpath(f.name))

        self._assert_action_after_watcher(True, assertions_cb)

    def test_single_file_created_just_after_the_watcher_ignored(self):

        def assertions_cb(events, f):
            self.assertEquals(len(events), 0)

        self._assert_action_after_watcher(False,
                lambda e, f: self.assertEquals(len(e), 0))

    def test_single_file_deleted(self):
        events = []
        def callback(event):
            events.append(event)

        import os
        f = open(os.path.join(self.tempdir, "test"), "w")
        f.write("abc")
        f.flush()
        f.close()
        from fsevents import Stream
        stream = Stream(callback, self.tempdir, file_events=True)

        from fsevents import Observer
        observer = Observer()
        observer.schedule(stream)
        observer.start()

        # add single file
        import time
        while not observer.isAlive():
            time.sleep(0.1)
        del events[:]
        time.sleep(2.1)
        os.unlink(f.name)
        time.sleep(0.1)

        # stop and join observer
        observer.stop()
        observer.unschedule(stream)
        observer.join()

        from fsevents import IN_DELETE
        self.assertEquals(len(events), 1)
        self.assertEquals(events[0].mask, IN_DELETE)
        self.assertEquals(events[0].name, os.path.realpath(f.name))

    def test_single_file_moved(self):
        events = []
        def callback(event):
            events.append(event)

        import os
        f = open(os.path.join(self.tempdir, "test"), "w")
        f.write("abc")
        f.flush()
        f.close()
        from fsevents import Stream
        stream = Stream(callback, self.tempdir, file_events=True)

        from fsevents import Observer
        observer = Observer()
        observer.schedule(stream)
        observer.start()

        # add single file
        import time
        while not observer.isAlive():
            time.sleep(0.1)
        del events[:]
        time.sleep(2.1)
        new = "%s.new" % f.name
        os.rename(f.name, new)
        time.sleep(0.1)

        # stop and join observer
        observer.stop()
        observer.unschedule(stream)
        observer.join()

        os.unlink(new)
        from fsevents import IN_MOVED_FROM
        from fsevents import IN_MOVED_TO
        self.assertEquals(len(events), 2)
        self.assertEquals(events[0].mask, IN_MOVED_FROM)
        self.assertEquals(events[0].name, os.path.realpath(f.name))
        self.assertEquals(events[1].mask, IN_MOVED_TO)
        self.assertEquals(events[1].name, os.path.realpath(new))
        self.assertEquals(events[0].cookie, events[1].cookie)

    def test_single_file_modified(self):
        events = []
        def callback(event):
            events.append(event)

        import os
        f = open(os.path.join(self.tempdir, "test"), "w")
        f.write("abc")
        f.flush()
        from fsevents import Stream
        stream = Stream(callback, self.tempdir, file_events=True)

        from fsevents import Observer
        observer = Observer()
        observer.schedule(stream)
        observer.start()

        # add single file
        import time
        while not observer.isAlive():
            time.sleep(0.1)
        del events[:]
        time.sleep(2.1)
        f.write("abc")
        f.flush()
        f.close()
        time.sleep(0.1)

        # stop and join observer
        observer.stop()
        observer.unschedule(stream)
        observer.join()

        os.unlink(f.name)
        from fsevents import IN_MODIFY
        self.assertEquals(len(events), 1)
        self.assertEquals(events[0].mask, IN_MODIFY)
        self.assertEquals(events[0].name, os.path.realpath(f.name))

    def test_single_file_created_and_modified(self):
        events = []
        def callback(event):
            events.append(event)

        from fsevents import Stream
        stream = Stream(callback, self.tempdir, file_events=True)

        from fsevents import Observer
        observer = Observer()
        observer.schedule(stream)
        observer.start()

        # add single file
        import time
        while not observer.isAlive():
            time.sleep(0.1)
        del events[:]
        time.sleep(2.1)

        import os
        f = open(os.path.join(self.tempdir, "test"), "w")
        f.write("abc")
        f.flush()

        time.sleep(1.0)

        f.write("def")
        f.flush()
        f.close()
        time.sleep(0.1)

        # stop and join observer
        observer.stop()
        observer.unschedule(stream)
        observer.join()

        os.unlink(f.name)
        from fsevents import IN_CREATE, IN_MODIFY
        self.assertEquals(len(events), 2)
        self.assertEquals(events[0].mask, IN_CREATE)
        self.assertEquals(events[0].name, os.path.realpath(f.name))
        self.assertEquals(events[1].mask, IN_MODIFY)
        self.assertEquals(events[1].name, os.path.realpath(f.name))

    def test_single_directory_deleted(self):
        events = []
        def callback(event):
            events.append(event)

        import os
        new1 = os.path.join(self.tempdir, "newdir1")
        new2 = os.path.join(self.tempdir, "newdir2")
        try:
            os.mkdir(new1)
            os.mkdir(new2)
            import time
            time.sleep(0.2)
            from fsevents import Stream
            stream = Stream(callback, self.tempdir, file_events=True)

            from fsevents import Observer
            observer = Observer()
            observer.schedule(stream)
            observer.start()

            # add single file
            import time
            while not observer.isAlive():
                time.sleep(0.1)
            del events[:]
            time.sleep(0.1)
            os.rmdir(new2)
            time.sleep(1.0)

            # stop and join observer
            observer.stop()
            observer.unschedule(stream)
            observer.join()

            from fsevents import IN_DELETE
            self.assertEquals(len(events), 1)
            self.assertEquals(events[0].mask, IN_DELETE)
            self.assertEquals(events[0].name, os.path.realpath(new2))
        finally:
            os.rmdir(new1)

    def test_existing_directories_are_not_reported(self):
        import os
        from fsevents import Stream, Observer

        events = []
        def callback(event):
            events.append(event)

        stream = Stream(callback, self.tempdir, file_events=True)
        new1 = os.path.join(self.tempdir, "newdir1")
        new2 = os.path.join(self.tempdir, "newdir2")
        os.mkdir(new1)
        observer = Observer()
        observer.schedule(stream)
        observer.start()

        import time
        while not observer.isAlive():
            time.sleep(0.1)
        del events[:]
        time.sleep(1)
        os.mkdir(new2)
        try:
            time.sleep(1.1)
            observer.stop()
            observer.unschedule(stream)
            observer.join()

            from fsevents import IN_CREATE
            self.assertEquals(len(events), 1)
            self.assertEquals(events[0].mask, IN_CREATE)
            self.assertEquals(events[0].name, os.path.realpath(new2))
        finally:
            os.rmdir(new1)
            os.rmdir(new2)
