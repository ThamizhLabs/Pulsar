from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid
from multiprocessing import Process, Queue
from threading import Thread
from queue import Empty
from copy import deepcopy
from pulsar.tools import sequential_solver, parallel_solver_pooling, sat_solver

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

        self.pulsar = Flask(__name__)
        self.pulsar.add_url_rule('/set', 'take_action', self.take_action, methods=['POST'])
        # self.pulsar.add_url_rule('/get', 'send_response', self.send_response, methods=['GET'])

        self.socketio = SocketIO(self.pulsar, cors_allowed_origins="*")
        self.clients = {}  # Dictionary to track connected clients

        # Dynamically register WebSocket events
        self.socketio.on_event('connect', self.handle_connect)
        self.socketio.on_event('disconnect', self.handle_disconnect)

        # Start the listener thread for checking the response queue
        self.listener_thread = Thread(target=self.check_and_send_response, daemon=True)
        self.listener_thread.start()

        print("Pulsar at your service!")

    def take_action(self):
        req_msg = request.json
        session_id = req_msg.get('session_id')
        print(f"Request received: from client {session_id}")

        if req_msg['action'] == 'solve_puzzle':
            try:
                while not response_queue.empty():
                    response_queue.get()
                puzzle = req_msg['puzzle']
                solver = req_msg.get('solver')
                self.trigger_solver(puzzle, solver=solver, session_id=session_id)
                return self.response(200)
            except KeyError:
                return self.response(413)

        return self.response(412)

    @staticmethod
    def trigger_solver(puzzle, solver='sequential', session_id=None):
        """
        Trigger the solver process in the background and send results to the response queue.
        This function will immediately return after triggering the solver.
        """
        if solver == 'parallel':
            p = Process(target=parallel_solver_pooling, args=(deepcopy(puzzle), response_queue, session_id))
        elif solver == 'SAT':
            p = Process(target=sat_solver, args=(deepcopy(puzzle), response_queue, session_id))
        else:
            p = Process(target=sequential_solver, args=(deepcopy(puzzle), response_queue, session_id))

        p.start()

    def check_and_send_response(self):
        """
        Check the response queue in a background thread and emit the solution to clients
        using SocketIO. This ensures the solution is sent once it's ready.
        """
        print("Queue check started!")

        while True:
            try:
                # Get data from the queue (non-blocking with timeout)
                payload = response_queue.get(timeout=0.1)

                # Use the start_background_task method to safely emit from the background thread
                if payload['session'] in self.clients:
                    self.socketio.start_background_task(self.emit_solution, payload)
            except Empty:
                pass
            except ValueError:
                print(f"Error occurred while getting data from response queue")
                return

    def emit_solution(self, payload):
        """ Emit the solution to the client. This function runs in the main process. """
        try:
            self.socketio.emit('solution_found', payload, room=payload['session'])
            print(f"Solution sent to client {payload['session']}")
        except Exception as e:
            print(f"Error emitting solution: {e}")

    def handle_connect(self):
        """ When a client connects, generate and send a unique session ID """
        session_id = str(uuid.uuid4())  # Generate a unique ID for the client
        self.clients[session_id] = request.sid  # Map session ID to WebSocket session
        join_room(session_id)  # Join a private room for this client
        emit('session_id', {'session_id': session_id})  # Send ID to client
        print(f"Client {session_id} connected")

    def handle_disconnect(self):
        """ When a client disconnects, remove them from tracking """
        for session_id, sid in list(self.clients.items()):
            if sid == request.sid:
                leave_room(session_id)
                del self.clients[session_id]
                print(f"Client {session_id} disconnected")
                break

    def run(self, host='0.0.0.0', port=5000):
        """Starts the Flask-SocketIO server."""
        self.socketio.run(self.pulsar, host=host, port=port, debug=True, allow_unsafe_werkzeug=True)

    @staticmethod
    def response(err, data=None):
        if not data:
            data = {}

        data['message'] = error_db[err]
        return jsonify(data), err
