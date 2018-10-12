from logging import info
from threading import Thread
from subprocess import Popen, PIPE, STDOUT


def find(collection, item, field='name'):
    for s in collection:
        if s[field] == item:
            return s
    return None


def copy_replace(src, dst, pattern='', replace_value=''):
    # replacing special tag for a custom requirements.txt file
    f1 = open(src, 'r')
    f2 = open(dst, 'w')
    for line in f1:
        f2.write(line.replace(pattern, replace_value))
    f1.close()
    f2.close()


def log_info(pipe):
    for line in iter(pipe.readline, b''):
        info(line)
    return True


class DockerThreadRunner(object):

    def __init__(self, command, log_function):
        self.process = Popen(command, stdout=PIPE, stderr=STDOUT)
        self.log_function = log_function
        self.worker = Thread(name='worker', target=self.run)
        self.worker.start()

    def run(self):
        self.log_function(self.process.stdout)


def subprocess_run(command, log_function=log_info, wait=True):
    if wait:
        process = Popen(command, stdout=PIPE, stderr=STDOUT)
        with process.stdout:
            log_function(process.stdout)
        return process.wait()
    else:
        return DockerThreadRunner(command, log_function)
