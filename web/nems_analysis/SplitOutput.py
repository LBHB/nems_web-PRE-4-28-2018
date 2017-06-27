"""Custom splitter to output to both sys.stdout and StringIO."""

class SplitOutput():
    def __init__(self, *streams):
        self.streams = streams
    def write(self, s):
        for stream in self.streams:
            stream.write(s)