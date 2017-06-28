import socket
import sys
import threading
class tcpSocketCmd:
    def __init__(self,dict,q1,q2) :
        delf.dict = dict
        self.q1 = q1
        self.q2 = q2
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Bind the socket to the address given on the command line
        self.hostname = socket.gethostname()
        self.server_address = (hostname, 10000)
        print ('starting up on %s port %s' % server_address)
        self.sock.bind(server_address)
        self.sock.listen(1)
    def run(self):
        while True:
            print ('waiting for a connection')
            connection, client_address = sock.accept()
        try:
            print('client connected:', client_address)
            while True:
                data = connection.recv(1024)
                print ('received "%s"' % data)
                if data:
                    words = data.split()
                    if(words[0] == 'get') :
                        if(words[1] in self.dict):
                            result = self.dict[words[1]]
                            response = str(result)
                        else:
                            response = 'Not Found'
                    elsif(words[0] == 'set') : 
                        if(words[1] in self.dict):
                            if(result):
                                response = 'OK was ' + str(result)
                                self.dict[words[1]] = words[2]
                            else:
                                response = 'Not Found'
                    elsif(words[0] == 'tt') : 
                        if(words[1] == '1') :
                            self.q1.put(words[2] + ' ')
                            response = 'sent ' + words[2] + ' to port ' + words[1]
                        elsif(words[1] == '1') :
                            self.q2.put(words[2] + ' ')
                            response = 'sent ' + words[2] + ' to port ' + words[1]
                        else:
                            response = "No such port %s must be either 1 or 2" % words[2]
                    else :
                        response = "unknown command: %s"  % data
                    connection.sendall(response)
                else:
                    break
    finally:
        connection.close()