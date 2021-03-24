#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Bassem Aly"
__email__ = "basim.alyy@gmail.com"
__company__ = "Juniper Networks"
__version__ = 0.1

# -----


from flask import Flask, jsonify, redirect, request, url_for
from flask_restful import Resource, Api
from async_blog.devices import *
from async_blog.tasks import get_route_data,celery_app
import datetime
from celery.result import AsyncResult

app = Flask(__name__)
app.config['SECRET_KEY'] = 'MySuperKey'
prefix = "/api/v1/"
api = Api(app, prefix=prefix)
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0',
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

@app.route('/error')
def return_error():
    status_code = request.args.get("status_code", False)
    error = request.args.get("error", False)
    respponse_object = {
        "status_code": status_code,
        "error": error
    }
    return jsonify(respponse_object), status_code

    # "devices" : ["Gateway1","Gateway2", "Leaf1", "Leaf2", "Border_Leaf1"],


@api.resource('/fabric/routes')
class RestfulCollectionServer(Resource):
    def post(self):
        json_data = request.get_json(force=True)
        devices = json_data['devices']
        results = []
        app.logger.debug("Received the following list of devices: {}".format(devices))
        begin_time = datetime.datetime.now()
        for dev in devices:
            if nodes_inventory.get(dev, False):
                ip_address = nodes_inventory[dev]
                result = get_route_data.delay(ip_address, dev)
                print(result)
                results.append(f"http://{request.host}{prefix}tasks/{result.task_id}")
                print(results)
            else:
                return redirect(
                    url_for('return_error', error=f'Device is not exist in inventory {dev}', status_code=500))
        app.logger.debug("Time taken to return the result is: {}".format(datetime.datetime.now() - begin_time)) # 7 minutes
        return jsonify({"message": results})


@api.resource("/tasks/<task_id>")
class RestfulTaskServer(Resource):
    def get(self, task_id):
        task_result = AsyncResult(task_id, app=celery_app)
        result = {
            "task_id": task_id,
            "task_status": task_result.status,
            "task_result": task_result.result
        }
        return jsonify({"message": result})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
