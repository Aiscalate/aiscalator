from logging import info
from re import search


class LogRegexAnalyzer(object):
    """
    A regular expression analyzer object to parse logs and extract
    values from patterns in the logs.
    ...

    Attributes
    ----------
    artifact : string
        Value of the pattern found in the logs
    pattern : bytes
        Regular expression to search for in the logs
    """

    def __init__(self, pattern=None):
        """
        Parameters
        ----------
        pattern : string
            Regular expression to search for in the logs
        """
        self.artifact = "latest"
        self.pattern = pattern

# https://fangpenlin.com/posts/2012/08/26/good-logging-practice-in-python/
    def grep_logs(self, pipe):
        """
        Reads the logs and extract values defined by the pattern

        Parameters
        ----------
        pipe
            Stream of logs to analyze
        """
        for line in iter(pipe.readline, b''):  # b'\n'-separated lines
            # TODO improve logging in its own subprocess log file?
            info(line)
            if self.pattern is not None:
                m = search(self.pattern, line)
                if m:
                    self.artifact = m.group(1).decode("utf-8")
