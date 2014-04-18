import logging
logger = logging.getLogger(__name__)

class child():
    def foo1(self):
        print 'hi'
        logger.info('doing foo1')