import os
import re
import sys


class Tee:
    def __init__(self, *files):
        self.files = files

    # def write(self, obj):
    #     clean_obj = Tee.remove_ansi_escape(obj)
    #
    #     for f in self.files:
    #         obj_to_write = clean_obj if f == Tee.logfile else obj
    #         f.write(obj_to_write)

    # @staticmethod
    # def remove_ansi_escape(text):
    #     ansi_escape = re.compile(r'\x1B\[\d+(;\d+){0,2}m')
    #     return ansi_escape.sub('', text)

    def write(self, obj):
        for f in self.files:
            f.write(obj)

    def flush(self):
        for f in self.files:
            f.flush()

    @staticmethod
    def start(logfile_path):
        os.makedirs(os.path.dirname(logfile_path), exist_ok=True)

        logfile = open(logfile_path, 'w')

        sys.stdout = Tee(sys.stdout, logfile)
        sys.stderr = Tee(sys.stderr, logfile)

        Tee.logfile = logfile

    @staticmethod
    def end():
        if hasattr(Tee, 'logfile'):
            Tee.logfile.close()

        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    class _ContextManager:
        def __init__(self, logfile_path):
            self.logfile_path = logfile_path

        def __enter__(self):
            Tee.start(self.logfile_path)

        def __exit__(self, exc_type, exc_value, traceback):
            Tee.end()

    @classmethod
    def context(cls, logfile_path):
        return cls._ContextManager(logfile_path)
