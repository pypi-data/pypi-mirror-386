import os
import signal
import subprocess
import threading
import time
import atexit
import sys


class PythonExecutor:
    def __init__(self, timeout=6):
        self.timeout = timeout
        self.stop_event = threading.Event()
        self.processes = []  # track all processes

        self.errored_out_with = None

        # Register cleanup at exit
        atexit.register(self.cleanup)

         # Handle signals differently on Windows vs Unix
        if sys.platform != "win32":
            signal.signal(signal.SIGINT, self.handle_exit)
            signal.signal(signal.SIGTERM, self.handle_exit)
        else:
            # Windows-specific signal handling
            try:
                signal.signal(signal.CTRL_C_EVENT, self.handle_exit)
                signal.signal(signal.CTRL_BREAK_EVENT, self.handle_exit)
            except AttributeError:
                # Some Windows Python builds might not have these signals
                signal.signal(signal.SIGINT, self.handle_exit)

    def read_stream(self, stream, stream_name):
        try:
            for line in stream:
                if self.stop_event.is_set():
                    break
                if stream_name == "stdout":
                    self.output[0].append(line)
                else:
                    self.output[1].append(line)
                # self.output.append((stream_name, line))
        finally:
            stream.close()

    def timeout_handler(self, process):
        time.sleep(self.timeout)
        if not self.stop_event.is_set():
            self.stop_event.set()
            self.kill_process(process)

    def kill_process(self, process):
        if process and process.poll() is None:
            try:
                # Kill the whole process group
                if sys.platform == "win32":
                    # On Windows, use taskkill to force-terminate the process tree
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(process.pid)])
                else:
                    # Unix systems can use process groups
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                if sys.platform == "win32":
                    # If still running, try harder
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(process.pid)])
                else:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass  # already gone

    def executeSelfExitingCommand(self,command,kwargs):
        
        process = subprocess.Popen(command,**kwargs)
        
        stdout, stderr = process.communicate()

        if stdout:
            lines = stdout.decode()
            lines = lines.split("\n")
            for line in lines:
                if len(line.strip()) > 0:
                    self.output[0].append(line)

        if stderr:
            lines = stderr.decode()
            lines = lines.split("\n")
            for line in lines:
                if len(line.strip()) > 0:
                    self.output[1].append(line)

        # Check if successful
        if process.returncode != 0:
            self.errored_out_with = f"Command failed with exit code {process.returncode}"
        else:
            print("Command was successful")

    def runCommand(self, command, cwd,env=None, self_exit=True):
        self.output = [[],[]]
        self.stop_event = threading.Event()

        # print("self exist ", "#"*5, self_exit)

        kwargs = {
            'env': env,
            'cwd': cwd,
            'stdout': subprocess.PIPE,
            'stderr': subprocess.PIPE
        }

        # Add shell=True on Windows to handle .cmd/.bat files
        if sys.platform == "win32":
            kwargs['shell'] = True
            # Add Windows-specific creation flags if needed
            kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            if not self_exit:
                kwargs['preexec_fn'] = os.setsid

        if self_exit:
            self.executeSelfExitingCommand(command,kwargs)
            # tell us if command su]ceded or not
            if self.errored_out_with :
                raise ValueError(f"{command} exited with {self.errored_out_with} and error : {"\n".join(self.output[1])}")
        else:
            kwargs['text'] = True
            kwargs['bufsize'] = 1

            process = subprocess.Popen(
                command,
                **kwargs
            )
            self.processes.append(process)

            stdout_thread = threading.Thread(
                target=self.read_stream,
                args=(process.stdout, 'stdout'),
                daemon=True
            )
            stderr_thread = threading.Thread(
                target=self.read_stream,
                args=(process.stderr, 'stderr'),
                daemon=True
            )
            timeout_thread = threading.Thread(
                target=self.timeout_handler,
                args=(process,),
                daemon=True
            )

            stdout_thread.start()
            stderr_thread.start()
            timeout_thread.start()

            process.wait()
            self.stop_event.set()

            stdout_thread.join(timeout=2)
            stderr_thread.join(timeout=2)
            timeout_thread.join(timeout=1)

            self.kill_process(process)

        return self.output

    def cleanup(self):
        """Kill all subprocesses at exit"""
        for process in self.processes:
            self.kill_process(process)

    def handle_exit(self, signum, frame):
        """Handle Ctrl+C or kill signals"""
        print(f"\nReceived signal {signum}, cleaning up...")
        self.cleanup()
        sys.exit(1)
