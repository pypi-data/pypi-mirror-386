import logging

__prog_name__ = "git-sanity"
__version__ = "1.0.0"
__author__ = "yuqiaoyu"
__config_root_dir__ = "." + __prog_name__
__config_file_name__ = __prog_name__ + "_config.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s {} %(levelname)s: %(message)s".format(__prog_name__))