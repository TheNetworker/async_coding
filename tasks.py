#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Bassem Aly"
__email__ = "basim.alyy@gmail.com"
__company__ = "Juniper Networks"
__version__ = 0.1

# -----

from celery import Celery, group
from jnpr.junos import Device
from jnpr.junos.exception import *
import logging
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import devices

logging.basicConfig(level=logging.DEBUG)

celery_app = Celery(
    "tasks",
    backend="redis://localhost:6379",
    broker="redis://localhost:6379"
)


@celery_app.task(name="get_route_data")
def get_route_data(ip_address, dev_name):
    try:
        logging.debug(f'Trying to establish connection to {dev_name}')
        with Device(host=ip_address, user=devices.username, password=devices.password, gather_facts=False,
                    ssh_config="~/.ssh/config") as dev:
            dev.open()
            routes = dev.rpc.get_route_information(normalize=True, level="extensive")
            return (True, {dev_name: "routes returned!"})

    except ConnectTimeoutError:
        return (False, f'Unable to establish connection to: {ip_address}')

    except ConnectRefusedError:
        return (False, f'Authentication failed to: {ip_address}')

    except Exception as e:
        return (False, str(e))
