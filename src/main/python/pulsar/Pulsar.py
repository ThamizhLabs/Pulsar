from flask import Flask, request, jsonify
from multiprocessing import Process, Queue
from copy import deepcopy
from queue import Empty

from pulsar.tools import sequential_solver, parallel_solver, parallel_solver_pooling

error_db = {
    200: "Success",
    204: "Response Queue Empty",
    410: "Please request with a connection key",
    411: "Connection Key Invalid",
    412: "Request message contains invalid action",
    413: "Request message contains invalid puzzle format"
}
response_queue = Queue()


class Pulsar:
    def __init__(self):
        # self.response_queue = Queue()

        self.keys = []

        self.pulsar = Flask(__name__)
        self.pulsar.add_url_rule('/set', 'take_action', self.take_action, methods=['POST'])
        self.pulsar.add_url_rule('/get', 'send_response', self.send_response, methods=['GET'])

        print("Pulsar at your service!")

    def take_action(self):

        req_msg = request.json
        print(f"Request receeived1: {req_msg}")

        if req_msg['action'] == 'connect':
            return self.generate_new_key()

        if not req_msg.get('key'):
            return self.response(410)

        if not self.key_valid(req_msg['key']):
            return self.response(411)

        if req_msg['action'] == 'solve_puzzle':
            try:
                while not response_queue.empty():
                    response_queue.get()
                puzzle = req_msg['puzzle']
                solver = req_msg.get('solver')
                self.trigger_solver(puzzle, solver=solver)
                return self.response(200)
            except KeyError:
                return self.response(413)

        return self.response(412)

    @staticmethod
    def response(err, data=None):

        if not data:
            data = {}

        data['message'] = error_db[err]
        return jsonify(data), err

    def generate_new_key(self):
        new_key = "key_kahsdkfjsdf0182738kjsd"
        self.keys.append(new_key)
        return self.response(200, {"key": new_key})

    def key_valid(self, key):
        return key in self.keys

    @staticmethod
    def trigger_solver(puzzle, solver='sequential'):
        if solver == 'parallel':
            p = Process(target=parallel_solver_pooling, args=(deepcopy(puzzle), response_queue))
            # p.daemon = True
        else:
            p = Process(target=sequential_solver, args=(deepcopy(puzzle), response_queue))
            # p.daemon = True
        p.start()

    def send_response(self):
        try:
            payload = response_queue.get(timeout=0.1)
            return self.response(200, {"payload": payload})
        except Empty:
            return self.response(204)
        except ValueError:
            print(f"Error occurred while getting data from response queue")
            self.response(400)
