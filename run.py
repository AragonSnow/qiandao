#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2016 Binux <roy@binux.me>

import sys
import os.path
import logging
import tornado.log
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.httpserver import HTTPServer

import config
from web.app import Application
from worker import MainWorker

import sqlite3_db_task_converter
import requests

requests.packages.urllib3.disable_warnings()

if __name__ == "__main__":
    if sys.getdefaultencoding() != 'utf-8':
        reload(sys)
        sys.setdefaultencoding('utf-8')
    # init logging
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if config.debug else logging.INFO)
    channel = logging.StreamHandler(sys.stdout)
    channel.setFormatter(tornado.log.LogFormatter())
    logger.addHandler(channel)

    if not config.debug:
        channel = logging.StreamHandler(sys.stderr)
        channel.setFormatter(tornado.log.LogFormatter())
        channel.setLevel(logging.WARNING)
        logger.addHandler(channel)

    if len(sys.argv) > 2 and sys.argv[1] == '-p' and sys.argv[2].isdigit():
        port = int(sys.argv[2])
    else:
        port = config.port

    http_server = HTTPServer(Application(), xheaders=True)
    http_server.bind(port, config.bind)
    http_server.start()

    https_enable = False
    if os.path.exists(config.certfile) & os.path.exists(config.keyfile):
        https_enable = True
        https_server = HTTPServer(Application(), ssl_options={
            "certfile": os.path.abspath(config.certfile),
            "keyfile": os.path.abspath(config.keyfile),
        }, xheaders=True)
        https_server.bind(config.https_port, config.bind)
        https_server.start()

    converter = sqlite3_db_task_converter.DBconverter()
    converter.ConvertNewType() 
    
    worker = MainWorker()
    PeriodicCallback(worker, config.check_task_loop).start()
    worker()

    logging.info("http server started on %s:%s", config.bind, port)
    if https_enable:
        logging.info("https server started on %s:%s", config.bind, config.https_port)

    IOLoop.instance().start()
