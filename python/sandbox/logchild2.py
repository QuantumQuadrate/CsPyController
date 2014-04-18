import logging
logger = logging.getLogger(__name__)

class child():
    def foo2(self):
        print 'hey'
        logger.info('doing foo2')