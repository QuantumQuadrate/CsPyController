__author__ = 'Hexagon'

import ConfigParser

CONFIG_FILE = 'config/config.cfg'

def import_config():
	# import config file
	config = ConfigParser.ConfigParser()
	try:
	    config.read(CONFIG_FILE)
	except ConfigParser.NoSectionError:
	    logger.critical('Could not find config file at %s', CONFIG_FILE)
	return config