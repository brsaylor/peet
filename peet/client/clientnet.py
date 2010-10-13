# Copyright 2009 University of Alaska Anchorage Experimental Economics
# Laboratory
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Threads to handle server-client communication - client side

# Inspired by c2sthread by Theodore Turocy
# turocy@econmail.tamu.edu

# The public interface consists of the Communicator class.

import thread
import socket
import sys
import time
#import pickle
import traceback

from peet.shared import cerealizer
from peet.shared import network

class Communicator:

    """
    """

    def __init__(self, address, port, postEvent):
        """ @param{postEvent}  A function to handle posting the message event to
        the client interface.  Note that the clientnet.Communicator has no
        message queue, just postEvent. """
        self.address = address
        self.port = port
        self.postEvent = postEvent
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connectToServer(self, loginName):

        self.loginName = loginName

        def run():
            connected = False
            while not connected:
                try:
                    self.sock.connect((self.address, self.port))
                    connected = True
                except:
                    #print "Couldn't connect, retrying in 1 second"
                    time.sleep(1)

            self.postEvent({'type': 'connect'})
            self.senderThread = network.SenderThread(self.sock, True)
            self.senderThread.Start()
            self.listenerThread = ListenerThread(self)
            self.listenerThread.Start()
            self.send({'type': 'login', 'name': loginName})

        thread.start_new_thread(run, ())

    def reconnectToServer(self):
        # FIXME: since this is mostly the same as connectToServer(), it would be
        # better to combine them.

        # FIXME: At some point, need to set self.loginName

        def run():
            try:
                self.sock.connect((self.address, self.port))
            except:
                print "failed to connect: ", sys.exc_info()[0]
                raise
            else:
                self.postEvent({'type': 'reconnect'})
                self.senderThread = network.SenderThread(self.sock)
                self.senderThread.Start()
                self.listenerThread = ListenerThread(self)
                self.listenerThread.Start()

        thread.start_new_thread(run, ())

    def send(self, message):
        self.senderThread.send(message)

class ListenerThread:

    """
    {ListenerThread} listens on the specified socket for messages from the
    server.  When a message is received, it 
    , and then waits for the next message.
    """

    def __init__(self, communicator):
        self.communicator = communicator
        self.keepListening = True

    def Start(self):
        thread.start_new_thread(self.Run, ())

    def Stop(self):
        self.keepListening = False

    def Run(self):
        try:
            leftovers = ''
            while self.keepListening:
                data, leftovers = network.recvmessage(self.communicator.sock,
                        leftovers)
                if data == None:
                    print "ListenerThread: connection closed; terminating"
                    self.keepListening = False
                    break
                message = cerealizer.loads(data)
                if message['type'] == 'sync':
                    # Server sent a sync message; send back a reply immediately
                    # with our wall-clock time
                    self.communicator.send({'type': 'sync', 'ct': time.time()})
                else:
                    self.communicator.postEvent(message)

        except:
            print "ListenerThread.Run(): caught exception:"
            traceback.print_exc(file=sys.stdout)

        # Thread is terminating.
        self.communicator.postEvent({'type': 'disconnect'})
