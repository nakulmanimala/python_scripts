from config import conf


class Logger:
    def __init__(self, l):
        self.l = l
        self.l.basicConfig(filename=conf['logLocation'], level=self.l.INFO, filemode='a+',
                           format='%(name)s - %(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

    def warn(self, s):
        self.l.warning(s)

    def error(self, s):
        self.l.error(s)

    def info(self, s):
        self.l.info(s)

