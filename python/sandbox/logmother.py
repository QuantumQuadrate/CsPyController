import logging
import logchild1
import logchild2

#get the root logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

#set up logging to console
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)

#set up logging to file
fh = logging.FileHandler('log.txt')
fh.setLevel(logging.DEBUG)

#set format
formatter = logging.Formatter(fmt='%(asctime)s - %(threadName)s - %(filename)s.%(funcName)s.%(lineno)s - %(levelname)s\n%(message)s\n', datefmt='%Y/%m/%d %H:%M:%S')
#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

sh.setFormatter(formatter)
fh.setFormatter(formatter)

#add handlers (i.e. put them to use)
logger.addHandler(sh)
logger.addHandler(fh)

logger.info('creating child 1')
lc1=logchild1.child()
logger.info('creating child 2')
lc2=logchild2.child()

logger.info('mother doing foo1')
lc1.foo1()
logger.info('mother doing foo2')
lc2.foo2()
logger.debug('ended')
