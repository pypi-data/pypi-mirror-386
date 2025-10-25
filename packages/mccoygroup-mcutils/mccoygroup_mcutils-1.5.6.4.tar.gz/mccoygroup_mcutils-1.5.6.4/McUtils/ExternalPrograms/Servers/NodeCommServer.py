"""
A simple handler interprocess communication on HPC systems
"""
import abc
import os
import threading, time
import socket, socketserver, json, traceback, subprocess
import sys
import multiprocessing as mp

__all__ = [
    "NodeCommTCPServer",
    "NodeCommUnixServer",
    "NodeCommHandler",
    "NodeCommClient",
    "ShellCommHandler",
    "setup_parent_terminated_listener",
    "setup_server",
    "handle_command_line"
]


# PUT HERE TO CHECK IF THE PROCESS SHOULD DIE OR NOT
def check_kill_process(w_pid, cur_pid):
    import psutil, signal
    if not psutil.pid_exists(w_pid):
        os.kill(cur_pid, signal.SIGKILL)  # maybe make this less dramatic
        exit(1)
    return True


def listen_for_proc(w_pid, cur_pid, polling_time=5):
    while check_kill_process(w_pid, cur_pid):
        time.sleep(polling_time)


def setup_parent_terminated_listener(PARENT_PID, CURRENT_PID):
    thread = threading.Thread(
        target=listen_for_proc,
        args=(PARENT_PID, CURRENT_PID)
    )
    thread.start()
    return thread


def infer_mode(connection):
    if (
            isinstance(connection, tuple)
            and isinstance(connection[0], str) and isinstance(connection[1], int)
    ):
        mode = "TCP"
    elif isinstance(connection, str):
        mode = "Unix"
    else:
        raise ValueError(f"invalid connection spec {connection}")
    return mode


class NodeCommTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


class NodeCommUnixServer(socketserver.UnixStreamServer):
    allow_reuse_address = True

    def server_bind(self):
        """Called by constructor to bind the socket.

        May be overridden.

        """

        if self.allow_reuse_address:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)
        self.server_address = self.socket.getsockname()


class NodeCommClient:
    def __init__(self, connection, timeout=10):
        self.conn = connection
        mode = infer_mode(connection)
        if mode == "TCP":
            self.mode = socket.AF_INET
        elif mode == "Unix":
            self.mode = socket.AF_UNIX
        else:
            raise NotImplementedError(mode)
        self.timeout = timeout

    SEND_CWD = True
    def prep_command_env(self):
        env = {}
        if self.SEND_CWD:
            env['pwd'] = os.getcwd()
        return env

    def communicate(self, command, args, kwargs):
        request = json.dumps({
            "command": command,
            "args": args,
            "kwargs": kwargs,
            "env": self.prep_command_env()
        }) + "\n"
        request = request.encode()

        # Create a socket (SOCK_STREAM means a TCP socket)
        mode = infer_mode(self.conn)
        # print(f"Sending request over {mode}")
        if mode == "Unix" and not os.path.exists(self.conn):
            raise ValueError(f"socket file {self.conn} doesn't exist")
        with socket.socket(self.mode, socket.SOCK_STREAM) as sock:
            # Connect to server and send data
            sock.connect(self.conn)
            sock.settimeout(self.timeout)
            sock.sendall(request)
            # Receive data from the server and shut down
            body = b''
            while b'\n' not in body:
                body = body + sock.recv(1024)


        return json.loads(body.strip().decode())

    @classmethod
    def print_response(cls, response):
        msg = response.get("stdout", "")
        if len(msg) > 0: print(msg, file=sys.stdout)
        msg = response.get("stderr", "")
        if len(msg) > 0: print(msg, file=sys.stderr)

    def call(self, command, *args, **kwargs):
        return self.communicate(command, args, kwargs)

class NodeCommHandler(socketserver.StreamRequestHandler):

    def handle(self):
        try:
            # self.rfile is a file-like object created by the handler;
            # we can now use e.g. readline() instead of raw recv() calls
            self.data = self.rfile.readline().strip()
            response = self.handle_json_request(self.data)
            # Likewise, self.wfile is a file-like object used to write back
            # to the client
        except:
            response = {
                "stdout": "",
                "stderr": traceback.format_exc(limit=1)
            }
        try:
            self.wfile.write(json.dumps(response).encode() + b'\n')
        except:
            traceback.print_exc(limit=1)  # big ol' fallback

    def handle_json_request(self, message: bytes):
        try:
            request = json.loads(message.decode())
        except:
            response = {
                "stdout": "",
                "stderr": traceback.format_exc(limit=1)
            }
        else:
            # comm = request.get("command", '<unknown>')
            # args = request.get("args", [])
            env = request.get("env", {})
            # print(f"Got: {comm} {args}")
            response = self.dispatch_request(request, env)
            # print(f"Sending: {response}")

        return response

    def setup_env(self, env):
        ...

    @property
    def method_dispatch(self):
        return self.get_methods()

    def dispatch_request(self, request: dict, env: dict):
        method = request.get("command", None)
        if method is None:
            response = {
                "stdout": "",
                "stderr": f"no command specified"
            }
        else:
            caller = self.method_dispatch.get(method.lower(), None)
            if caller is None:
                response = {
                    "stdout": "",
                    "stderr": f"unknown command {method}"
                }
            else:
                args = request.get("args", [])
                kwargs = request.get("kwargs", {})
                # if args is None:
                #     response = {
                #         "stdout": "",
                #         "stderr": f"malformatted request {request}"
                #     }
                # else:
                try:
                    self.setup_env(env)
                    response = caller(args, kwargs)
                except:
                    response = {
                        "stdout": "",
                        "stderr": traceback.format_exc(limit=1)
                    }

        return response


    @abc.abstractmethod
    def get_methods(self) -> 'dict[str,method]':
        ...

    @staticmethod
    def get_valid_port(git_port, min_port=4000, max_port=65535):
        git_port = int(git_port)
        if git_port > max_port:
            git_port = git_port % max_port
        if git_port < min_port:
            git_port = max_port - (git_port % (max_port - min_port))
        return git_port

    @classmethod
    def get_default_connection(cls, port=None, hostname='localhost', session_var='SESSION_ID'):
        if port is None:
            port = os.environ.get(cls.DEFAULT_PORT_ENV_VAR, os.environ.get(session_var))
            if port is None:
                raise ValueError(f"`{cls.DEFAULT_PORT_ENV_VAR}` must be set at the environment level")
        port = cls.get_valid_port(port)

        return (hostname, port)

    TCP_SERVER = NodeCommTCPServer
    UNIX_SERVER = NodeCommUnixServer
    DEFAULT_CONNECTION = ("localhost", 9999)
    DEFAULT_PORT_ENV_VAR = None
    DEFAULT_SOCKET_ENV_VAR = None

    @classmethod
    def start_server(cls, connection=None, port=None):
        # Create the server, binding to localhost on port 9999
        if connection is None and cls.DEFAULT_SOCKET_ENV_VAR is not None:
            connection = os.environ.get(cls.DEFAULT_SOCKET_ENV_VAR)
        if connection is None:
            if port is None and cls.DEFAULT_PORT_ENV_VAR:
                port = os.environ.get(cls.DEFAULT_PORT_ENV_VAR)
            if port is not None:
                connection = ('localhost', cls.get_valid_port(port))
        if connection is None:
            connection = cls.DEFAULT_CONNECTION
        mode = infer_mode(connection)
        # print(f"Starting server at {connection} over {mode}")
        if mode == "TCP":
            server_type = cls.TCP_SERVER
        elif mode == "Unix":
            server_type = cls.UNIX_SERVER
        else:
            raise NotImplementedError(mode)
        with server_type(connection, cls) as server:
            # Activate the server; this will keep running until you
            # interrupt the program with Ctrl-C
            server.serve_forever()
            if mode == "Unix":
                try:
                    os.remove(connection)
                except OSError:
                    ...

    class MultiprocessingServerContext:
        def __init__(self, proc:mp.Process, timeout=3):
            self.proc = proc
            self.timeout = timeout

        def __enter__(self):
            self.proc.start()
            time.sleep(self.timeout)
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            # self.proc.join(timeout=self.timeout)
            self.proc.kill()
    @classmethod
    def start_multiprocessing_server(cls, connection=None, port=None, timeout=3):
        proc = mp.Process(target=cls.start_server, kwargs={'connection':connection, 'port':port})
        return cls.MultiprocessingServerContext(proc, timeout=timeout)

    client_class = NodeCommClient
    @classmethod
    def client_request(cls, *args, client_class=None, connection=None):
        if client_class is None:
            client_class = cls.client_class
        if connection is None:
            connection = cls.DEFAULT_CONNECTION
        return client_class(connection).communicate(*args)

class ShellCommHandler(NodeCommHandler):

    @classmethod
    def subprocess_response(cls, command, args):
        pipes = subprocess.Popen([command, *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        std_out, std_err = pipes.communicate()
        return {
            "stdout": std_out.strip().decode(),
            "stderr": std_err.strip().decode()
        }

    @property
    def method_dispatch(self):
        return dict(
            {
                "cd": self.change_pwd,
                "pwd": self.get_pwd
            },
            **self.get_methods()
        )

    def change_pwd(self, args, kwargs):
        os.chdir(args[0])
        return {
            'stdout': "",
            'stderr': ""
        }

    def get_pwd(self, args, kwargs):
        cwd = os.getcwd()
        return {
            'stdout': cwd,
            'stderr': ""
        }

    def setup_env(self, env):
        if 'pwd' in env:
            os.chdir(env['pwd'])

    @abc.abstractmethod
    def get_subprocess_call_list(self):
        ...

    def get_methods(self) -> 'dict[str,method]':
        return {
            k: self._wrap_subprocess_call(v)
            for k, v in self.get_subprocess_call_list()
        }

    def _wrap_subprocess_call(self, command):
        if isinstance(command, str):
            def command(*args, _cmd=command, **kwargs):
                return self.subprocess_response(_cmd, *args, **kwargs)
        elif not callable(command):
            def command(*args, _cmd=command, **kwargs):
                return self.subprocess_response(*_cmd, *args, **kwargs)
        return command


def setup_server(handler_class, connection=None, port=None, ppid=None, hostname=None):
    if connection is None:
        connection = handler_class.get_default_connection(port, hostname)
    if ppid is None:
        ppid = os.environ.get("PARENT_PROCESS_ID")
    if ppid is not None:
        curpid = os.environ.get("WORKER_PROCESS_ID", os.getpid())
        setup_parent_terminated_listener(ppid, curpid)

    try:
        handler_class.start_server(connection=connection)
    except OSError:  # server exists
        print(f"Already serving on {connection}")
        pass

def handle_command_line(handler_class, client_class, connection=None, port=None, ppid=None, hostname=None):
    import sys, os

    if connection is None:
        connection = handler_class.get_default_connection(port, hostname)

    if len(sys.argv) == 1:
        setup_server(handler_class, connection=connection, ppid=ppid)
    else:
        client_class.print_response(
            client_class.client_request(sys.argv[1], sys.argv[2:], connection=ppid)
        )