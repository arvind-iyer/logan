class FileIter:
    def __init__(self, filepath, follow=True):
        self._file_handle = open(filepath)
        self._follow = follow

    def __next__(self):
        line = self._file_handle.readline()
        if line == "" and not self._follow:
            raise StopIteration
        return line

    def __iter__(self):
        return self

    def next(self):
        return self.__next__()
