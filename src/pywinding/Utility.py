import os
import glob
import logging
import time

def cleanup():
    # Delete all *.fem and *.ans files in the current directory
    for pattern in ["*.fem", "*.ans"]:
        for file in glob.glob(pattern):
            try:
                os.remove(file)
                logging.info(f"Deleted: {file}")
            except Exception as e:
                logging.info(f"Error deleting {file}: {e}")

    # Delete all *.fem and *.ans files in the 'temp' subdirectory
    temp_directory = "temp"
    if os.path.exists(temp_directory):
        for pattern in ["*.fem", "*.ans"]:
            for file in glob.glob(os.path.join(temp_directory, pattern)):
                try:
                    os.remove(file)
                    logging.info(f"Deleted: {file}")
                except Exception as e:
                    logging.info(f"Error deleting {file}: {e}")
    else:
        logging.info(f"Directory '{temp_directory}' does not exist.")

class Timer(object):
    def __init__(self, name=None):
        self.name = name

    def __enter__(self):
        self.tstart = time.time()

    def __exit__(self, type, value, traceback):
        if self.name:
            logging.info('[%s]' % self.name,)
        logging.info('Elapsed: %s' % (time.time() - self.tstart))