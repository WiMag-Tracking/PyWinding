import femm
import logging

from .commands import *

class Magneto:
    """
    Attribute Proxy and API wrapper for PyFEMM
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """
    def __init__(self):
        self.__api = femm
        logging.info("PyFEMM API wrapper instanciated")
 
    def __getattr__(self, attr):
        """
        Dunder method to allow for pythonic commands

        Should really have a case for each pre processor and explicitly
        list commands, instead allowing pyfemm to raise exceptions
        """
        # case 1 - common commands
        if attr.upper() in COMMON:
            def common(*args):
                return self.COMMON(attr.lower(), *args)
            return common
        # finally, just recursively construct the command and let pyfemm raise an exception
        return Command(self.__api, attr)  
   
    def COMMON(self, command, *args):
        
        if command.upper() in COMMON:
            logging.debug(f"Executing: {command}")
            return getattr(self.__api, command)(*args)  

    def init(self, hide=True, preprocessor='mi', **sim_kwargs):
        self.openfemm(hide)
        self.newdocument(0)
        getattr(getattr(self, preprocessor), "probdef")(*sim_kwargs.values())

class Command(object):
    """
    Helper class to recursively contstruct and execute object command.
    Can be adopted for other situations by changing delimiter
    """
    def __init__(self, obj, attr, delimiter='_'):
        self.__delimiter = delimiter
        self.__obj = obj
        self.attr = attr
        
    def __getattr__(self, attr):
        """
        Recursively construct the query or write directive
        by joining parts of the request with _
        """
        return Command(
            self.__obj,
            self.__delimiter.join((self.attr, attr))
            )
    
    def __call__(self, *args):
        logging.debug(f"Executing: {self.attr}")
        return getattr(self.__obj, self.attr)(*args)