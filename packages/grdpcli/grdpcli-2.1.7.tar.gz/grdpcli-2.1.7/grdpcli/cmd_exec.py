import errno
import fcntl
import json
import os
import pty
import select
import signal
import struct
import sys
import termios
import time
import tty
import subprocess
from kubernetes import config
from kubernetes.client import Configuration
from kubernetes.client.api import core_v1_api
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream
from grdpcli import *

# The following escape codes are xterm codes.
# See http://rtfm.etla.org/xterm/ctlseq.html for more.
START_ALTERNATE_MODE = set('\x1b[?{0}h'.format(i) for i in
                           ('1049', '47', '1047'))
END_ALTERNATE_MODE = set('\x1b[?{0}l'.format(i) for i in
                         ('1049', '47', '1047'))
ALTERNATE_MODE_FLAGS = tuple(START_ALTERNATE_MODE) + tuple(END_ALTERNATE_MODE)

class Interceptor(object):
    """
    This class does the actual work of the pseudo terminal. The spawn()
           function is the main entrypoint.
    """

    def __init__(self, k8s_stream=None):
        self.k8s_stream = k8s_stream
        self.master_fd = None

    def findlast(self, s, substrs):
        """
        Finds whichever of the given substrings occurs last in the given string
               and returns that substring, or returns None if no such strings
               occur.
        """
        i = -1
        result = None
        for substr in substrs:
            pos = s.rfind(substr)
            if pos > i:
                i = pos
                result = substr
        return result


    def spawn(self, argv=None):
        """
        Create a spawned process.
        Based on the code for pty.spawn().
        """
        if not argv:
            argv = [os.environ['SHELL']]

        pid, master_fd = pty.fork()
        self.master_fd = master_fd
        if pid == pty.CHILD:
            os.execlp(argv[0], *argv)

        old_handler = signal.signal(signal.SIGWINCH, self._signal_winch)
        try:
            mode = tty.tcgetattr(pty.STDIN_FILENO)
            tty.setraw(pty.STDIN_FILENO)
            restore = 1
        except tty.error:    # This is the same as termios.error
            restore = 0
        self._init_fd()
        try:
            self._copy()
        except (IOError, OSError):
            if restore:
                tty.tcsetattr(pty.STDIN_FILENO, tty.TCSAFLUSH, mode)

        self.k8s_stream.close()
        self.k8s_stream = None
        if self.master_fd:
            os.close(self.master_fd)
            self.master_fd = None
        signal.signal(signal.SIGWINCH, old_handler)

    def _init_fd(self):
        """
        Called once when the pty is first set up.
        """
        self._set_pty_size()

    def _signal_winch(self, signum, frame):
        """
        Signal handler for SIGWINCH - window size has changed.
        """
        self._set_pty_size()

    def _set_pty_size(self):
        """
        Sets the window size of the child pty based on the window size of
               our own controlling terminal.
        """
        packed = fcntl.ioctl(pty.STDOUT_FILENO,
                             termios.TIOCGWINSZ,
                             struct.pack('HHHH', 0, 0, 0, 0))
        rows, cols, h_pixels, v_pixels = struct.unpack('HHHH', packed)
        self.k8s_stream.write_channel(4, json.dumps({"Height": rows, "Width": cols}))

    def _copy(self):
        """
        Main select loop. Passes all data to self.master_read() or
               self.stdin_read().
        """
        assert self.k8s_stream is not None
        k8s_stream = self.k8s_stream
        while True:
            try:
                rfds, wfds, xfds = select.select([pty.STDIN_FILENO, k8s_stream.sock.sock], [], [])
            except select.error as e:
                no = e.errno if sys.version_info.major >= 3 else e[0]
                if no == errno.EINTR:
                    continue

            if pty.STDIN_FILENO in rfds and not k8s_stream.sock.sock in rfds:
                data = os.read(pty.STDIN_FILENO, 1024)
                self.stdin_read(data)
            if k8s_stream.sock.sock in rfds and not pty.STDIN_FILENO in rfds:
                # error occurs
                if k8s_stream.peek_channel(3):
                    break
                # read from k8s_stream
                if k8s_stream.peek_stdout():
                    data = k8s_stream.read_stdout()
                    self.master_read(data)

    def write_stdout(self, data):
        """
        Writes to stdout as if the child process had written the data.
        """
        os.write(pty.STDOUT_FILENO, data.encode())

    def write_master(self, data):
        """
        Writes to the child process from its controlling terminal.
        """
        assert self.k8s_stream is not None
        self.k8s_stream.write_stdin(data)

    def master_read(self, data):
        """
        Called when there is data to be sent from the child process back to
               the user.
        """
        flag = self.findlast(data, ALTERNATE_MODE_FLAGS)
        if flag is not None:
            if flag in START_ALTERNATE_MODE:
                # This code is executed when the child process switches the
                #       terminal into alternate mode. The line below
                #       assumes that the user has opened vim, and writes a
                #       message.
                # self.write_master('IEntering special mode.\x1b')
                pass
            elif flag in END_ALTERNATE_MODE:
                # This code is executed when the child process switches the
                #       terminal back out of alternate mode. The line below
                #       assumes that the user has returned to the command
                #       prompt.
                # self.write_master('echo "Leaving special mode."\r')
                pass
        self.write_stdout(data)

    def stdin_read(self, data):
        """
        Called when there is data to be sent from the user/controlling
               terminal down to the child process.
        """
        self.write_master(data)

def joinToPod(namespace, pod_name, exec_command):
    # Init Kube Api
    v1 = core_v1_api.CoreV1Api()
    
    # Getting the list of containers in the pod.
    try:
        pod_info = v1.read_namespaced_pod(pod_name, namespace)
        containers = [container.name for container in pod_info.spec.containers]
        
        # If there is more than one container, we offer the user to choose.
        if len(containers) > 1:
            container_name = questionary.select(
                "Select a container to connect:",
                choices=containers
            ).ask()
        else:
            container_name = containers[0]  # If there is only one container, we select it automatically.
        
        print(f"Selected container: {container_name}")
    except ApiException as e:
        print(f"Error: {e}")
        return

    try:
        result = stream(v1.connect_get_namespaced_pod_exec, name=pod_name, namespace=namespace,
                        command="/bin/bash", container=container_name, stderr=True, stdin=False, stdout=True, tty=False).rstrip()
        
        if "OCI runtime exec failed" in result:
            exec_command = "/bin/sh"

        resp = stream(core_v1_api.CoreV1Api().connect_post_namespaced_pod_exec,
                      pod_name,
                      namespace,
                      command=exec_command,
                      container=container_name,
                      stderr=True, stdin=True, stdout=True, tty=True, _preload_content=False)
        
        i = Interceptor(k8s_stream=resp)
        i.spawn(sys.argv[1:])
        
        if exec_command == "/bin/bash" or exec_command == "/bin/sh":
            os.system('reset')
    except ApiException as e:
        print(f"Error during exec: {e}")

# name = 'nginx-7db9fccd9b-bx4cv'
# exec_command = ['/bin/sh']
#
# resp = stream(core_v1_api.CoreV1Api().connect_post_namespaced_pod_exec, name, NAMESPACE, command=exec_command, stderr=True, stdin=True, stdout=True, tty=True, _preload_content=False)
#
# i = Interceptor(k8s_stream=resp)
# i.write_stdout('Now in pty mode.\r\n')
# i.spawn(sys.argv[1:])
# i.write_stdout('\r\nThe pty mode is over.\r\n')
# os.system('reset')
