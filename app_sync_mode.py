#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Bassem Aly"
__email__ = "babdelmageed@juniper.net"
__company__ = "Juniper Networks"
__version__ = 0.1

# -----

from flask import Flask, jsonify, redirect, request, url_for
from flask_restful import Resource, Api
from jnpr.junos import Device
from jnpr.junos.exception import *
from async_blog.devices import *
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'MySuperKey'
api = Api(app, prefix="/api/v1/")


@app.route('/error')
def return_error():
    status_code = request.args.get("status_code", False)
    error = request.args.get("error", False)
    respponse_object = {
        "status_code": status_code,
        "error": error
    }
    return jsonify(respponse_object)


def get_route_data(ip_address, dev_name):
    try:
        app.logger.debug(f'Trying to establish connection to {dev_name}')
        with Device(host=ip_address, user=username, password=password, gather_facts=False,
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

    # "devices" : ["Gateway1","Gateway2", "Leaf1", "Leaf2", "Border_Leaf1"],


@api.resource('/fabric/routes')
class RestfulCollectionServer(Resource):
    def post(self):
        json_data = request.get_json(force=True)
        devices = json_data['devices']
        os = json_data['os']
        results = []
        app.logger.debug("Received the following list of devices: {}".format(devices))
        begin_time = datetime.datetime.now()
        for dev in devices:
            if nodes_inventory.get(dev, False):
                ip_address = nodes_inventory[dev]
                _, result = get_route_data(ip_address, dev)
                results.append(result)

            else:
                return redirect(
                    url_for('return_error', error=f'Device is not exist in inventory {dev}', status_code=500))
        app.logger.debug("Time taken to return the result is: {}".format(datetime.datetime.now() - begin_time))
        return jsonify(message=results)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
