import socket
import sys
import code
import StringIO
import contextlib
@contextlib.contextmanager
def stdoutIO(stdout=None):
    old = sys.stdout
    if stdout is None:
        stdout = StringIO.StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old

class sockInt(code.InteractiveConsole):
    def __init__(self,connection, locals=None, filename="<<<Socket>>>"):
        self.connection = connection
        code.InteractiveConsole.__init__(self,locals=locals,filename=filename)
    def write (self,data) :
        """ send the data out the socket
        """
        self.connection.sendall(data)
    def raw_input(self,prompt) :
        self.write(prompt)
        return(self.connection.recv(1024).rstrip())
    def runcode(self,code) :
        """copied from code.py with a twist to capture the output
        """
        try:
            with stdoutIO() as s:
                exec(code, self.locals)
            self.write(s.getvalue())
        except SystemExit:
            raise
        except:
            self.showtraceback()
 
 
class socketPython:
    def __init__(self,locals) :
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Bind the socket to the address given on the command line
        #server_name = sys.argv[1]
        #server_address = (server_name, 10000)
        self.hostname = socket.gethostname()
        self.server_address = ('', 62222)
    def run(self);
        self.sock.bind(self.server_address)
        self.sock.listen(1)
        while True:
            connection, client_address = self.sock.accept()
            interp = sockInt(connection,locals=self.locals)
            try:
                print('client connected:', client_address)
                interp.interact(banner="Hello Socket Python")
            finally:
                connection.close()
