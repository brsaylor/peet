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

"""
network.py

Ben Saylor
2008-02-27

Networking code common to client and server

The main purpose is to define functions to send and receive whole messages, one
at a time, without losing any.  There is a subtle problem one encounters when
trying to send messages over sockets: sockets (at least TCP sockets) transfer
data in streams, not discrete messages (well, thinking above the packet level).
That means that each send() is not necessarily matched with exactly one
corresponding recv() on the other end, and vice versa.  For example, if the
server sends two messages in quick succession, they may both be sitting in the
client's receive buffer, and the client's call to recv() will return both
messages concatenated together.  When the client unpickles this, any pickled
representations in the data buffer after the first one will be discarded,
resulting in lost messages.  It's also possible to receive a partial message,
which cannot be unpickled without calling recv() again and waiting for the rest.

These functions prefix each message with its length to make sure they get
through whole and nothing gets discarded.

Also, SenderThread is defined in this file, because there are no differences
between how client and server do the sending part.  ListenerThread, however, is
defined separately for server (servernet.py) and client (clientnet.py)

see servernet.py and clientnet.py
"""

import sys
import socket
import thread
import Queue
import traceback
#import pickle
import cerealizer

# Register with Cerealizer the classes we need to be able to send over the
# network
import decimal
cerealizer.register(decimal.Decimal)

timeout = 10
""" Number of seconds the server waits for a message from the client before
considering it disconnected """

ping_interval = 2
""" Number of seconds to wait after sending a message before sending a ping from
client to server to let the server know the client is still alive """

msglen_width = 10
""" Number of characters to use in the zero-padded text representation of the
message length field """

def sendmessage(sock, message):
    """ Send a complete pickled object over socket sock.  message should be
    pickled before being passed in.  Message sent is prefixed by its length in
    bytes (msglen_width determines the number of bytes in this field). """
    msglen_str = '%0*u' % (msglen_width, len(message))
    data = msglen_str + message
    sock.sendall(data)

def recvmessage(sock, leftovers):
    """ Receive a complete pickled object from socket sock.  Return a tuple
    containing the pickled message and and characters remaining in the buffer
    after the message.  Pass this string in again next time as the 'leftovers'
    parameter.  (To begin with, pass in an empty string as leftovers.)
    If the connection has been closed, return None in place of the pickled
    message.
    """

    # Leftovers will always start with 1 to <msglen_width> bytes of the
    # <msglen_width>-byte message-length number that prefixes each message,
    # or be empty.

    buf = leftovers
    while len(buf) < msglen_width:
        # Read until we have all bytes of the message-length number.
        data = sock.recv(4096)
        if data == '':  # Disconnected.
            return (None, leftovers)
        buf += data
    msglen = int(buf[:msglen_width])  # Parse the message length number
    buf = buf[msglen_width:]  # and chop it off the buffer.
    while len(buf) < msglen:
        # Read until we have all bytes of the message.
        data = sock.recv(4096)
        if data == '':  # Disconnected.
            return (None, leftovers)
        buf += data
    # buf now contains a complete message (pickled object), possibly followed by
    # some more characters to be processed later (new leftovers)
    message = buf[:msglen]    # Chop the message off the buffer
    leftovers = buf[msglen:]  # and store the leftovers.
    return (message, leftovers)


class SenderThread:

    """
    SenderThread buffers and sends messages over one socket.
    Use the send() method.
    """

    def __init__(self, sock, send_pings=False):
        """
        Initializes the thread.  No action is taken; use
        C{Start()} to launch the thread.
        @param{send_pings} If True, send a ping message whenever no other
        message has been sent for <network.ping_interval> seconds.  Clients do
        this to let the server know they are still connected.
        """
        self.sock = sock
        self.msgQueue = Queue.Queue()
        self.qtimeout = ping_interval if send_pings else None


    def Start(self):
        """
        Does the actual business of running the thread.
        Call this member when the thread is to be launched.
        """
        thread.start_new_thread(self.Run, ())

    def Stop(self):
        """ Stop the thread (causes the Run function to terminate). """
        self.msgQueue.put(None)

    def Run(self):
        """
        The program body for the thread.  This is not called
        directly, but is launched indirectly using the C{Start}
        member.
        """

        while True:
            # Wait at most self.qtimeout seconds for a new message to send
            # before sending a ping to let the other end know we're still
            # connected.
            try:
                # Queue.get([block[, timeout]])
                data = self.msgQueue.get(True, self.qtimeout)
                if data == None:
                    print "SenderThread: Stop() called, terminating"
                    break
            except Queue.Empty:
                data = cerealizer.dumps({'type': 'ping'})

            try:
                sendmessage(self.sock, data)
            except:
                print "SenderThread: caught exception, terminating: "
                traceback.print_exc(file=sys.stdout)
                break

    def send(self, message):
        # Putting messages on the queue, then having the SenderThread take them
        # off as available and send them, ensures that they get sent in order.
        self.msgQueue.put(cerealizer.dumps(message))
