import logging
import sys


class TestFilter(logging.Filter):
    """Filters logs when running in testing"""

    def filter(self, record):
        return not (len(sys.argv) > 1 and sys.argv[1] == "test")
