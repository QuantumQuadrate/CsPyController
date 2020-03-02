"""ConfigInstrument.py

author=Matthew Ebert
created=2017-07-02

This instrument is used to save the settings from the config file.
"""

from __future__ import division
from atom.api import Member
from cs_instruments import Instrument
import numpy
import json
import pprint
import sys
import ConfigParser
from cs_errors import PauseError

import logging

__author__ = 'Matthew Ebert'
logger = logging.getLogger(__name__)


def print_conf(conf, title):
    """Print a json string nicely"""
    line_break = "*"*40
    print(line_break)
    print(title+'\n')
    pprint.pprint(conf)
    print(line_break)


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


class Config(Instrument):
    version = '2017.07.04'
    config = Member()  # config object
    config_dict = Member()  # config_dict for saving
    config_json = Member()  # serialized dictionary
    config_hash = Member()  # stores a hash of the json serialized config_dict

    def __init__(self, name, experiment, description='', config=None):
        super(Config, self).__init__(name, experiment, description)
        if not config:
            logger.critical("No config given to ConfigInstrument")
            raise PauseError
        self.config = config
        # save the config file as a dictionary
        self.config_dict = {s: dict(config.items(s)) for s in config.sections()}
        # hash the serialized dictionary so we can easily compare versions
        self.config_json = json.dumps(self.config_dict, sort_keys=True)
        self.config_hash = hash(self.config_json)

    def initialize(self):
        pass

    def start(self):
        self.isDone = True

    def writeResults(self, hdf5):
        pass

    def toHDF5(self, hdf, name=None):
        try:
            # serialize the config dictionary in a deterministic way
            conf_str = json.dumps(self.config_dict, sort_keys=True)
            # store in hdf file
            hdf.attrs[self.name] = numpy.string_(conf_str)
        except Exception:
            logger.exception('Error saving config to hdf file.')

    def fromHDF5(self, hdf):
        try:
            # read from hdf file
            conf_str = hdf
        except AttributeError:
            logger.warning('No configuration string found on hdf import.')
        except Exception:
            logger.exception('Error reading config to hdf file.')
        else:
            # compute the hash
            conf_hash = hash(conf_str)
            # compare the hash
            if conf_hash != self.config_hash:
                self.config_disagreement(conf_str)
            else:
                logger.info("configs match")

    def config_disagreement(self, new_conf):
        msg = (
            "Current configuration file and configuration file in "
            "settings do not agree."
        )
        logger.warning(msg)
        new_conf_dict = json.loads(new_conf)
        print_conf(new_conf_dict, "SAVED SETTINGS.HDF5 CONFIG")
        print_conf(self.config_dict, "CONFIG FILE")
        q = (
            "A change in the configuration file on disk has been detected.\n"
            "Would you like to use the configuration file saved in the "
            "settings.hdf5 file instead?"
        )
        if query_yes_no(q, default="no"):
            logger.info("Using configuration from settings.hdf5 file.")
            self.config_dict = new_conf_dict
            self.config_json = new_conf
            self.config_hash = hash(new_conf)
            self.config_from_dict(new_conf_dict)
        else:
            logger.info("Using configuration from config file.")
        print_conf(self.config_dict, "CURRENT CONF")

    def config_from_dict(self, conf_dict):
        """Creates a configuration file in memory based on a dictionary."""
        parser = ConfigParser.ConfigParser()
        for section in conf_dict.keys():
            parser.add_section(section)
            for item in conf_dict[section].keys():
                parser.set(section, item, conf_dict[section][item])

        self.config = parser
