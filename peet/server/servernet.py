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
Threads to handle server-client communication - server side

The public interface consists of the classes
  Communicator
  ClientConnection

Every message is a dictionary, assumed to have at least a 'type' key.
Communicator pickles before sending and unpickles after receiving.  Messages
are communicated to the server through the postEvent method that the server
passes in.  If the message['type'] is 'gm' (for Game Message), then the
message is also put on a queue for retrieval by the game controller using the
recv() and recv_nowait() methods.

Inspired by s2cthread by Theodore Turocy
turocy@econmail.tamu.edu
"""

import sys
import socket
import thread

# Higher-level interface, for Timer; should probably use for everything
import threading

import Queue
import time
#import pickle

from peet.shared import cerealizer
from peet.shared import network

class Communicator:

    """
    """

    def __init__(self, port, postEvent):
        """ postEvent is a function that will be called when a client connects,
        disconnects or sends a message.  Arguments will be clientConn, message.
        It should post an event with this information using the event system of
        whatever GUI toolkit is being used.  This allows the application to
        respond to messages without consuming them from the queue. """

        self.port = port
        self.postEvent = postEvent

        # The inQueue contains all incoming client messages waiting to be
        # processed.  Each element in the queue is a tuple in the form
        # (clientConnection, messageDict)
        self.inQueue = Queue.Queue()

        self.paused = False
        self.pauseLock = thread.allocate_lock()

        self.timer = None

    def acceptConnections(self):
        """
        Start accepting client connections, placing each connection message in
        the incoming message queue as it arrives.  Non-blocking.  Connection
        messages have type 'connect' and the associated ClientConnection has
        id=None.
        """

        def run():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # to prevent socket.error: (98, 'Address already in use'):
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', self.port))
            while True:
                sock.listen(1)
                csock, addr = sock.accept()
                csock.settimeout(network.timeout)
                clientConn = ClientConnection(None, csock, addr)
                self.postEvent(clientConn, {'type': 'connect'})
                    # Need to post 'connect' message before starting the
                    # listenerThread; otherwise we may get the 'login' message
                    # from the client before the 'connect' message.
                    # Also need to start the sender thread before the
                    # listenerthread, otherwise we may get the login message
                    # before the senderthread has been started, so when
                    # --autostart is enabled, the server may try to start the
                    # game before the senderthread has been started -> crash
                clientConn.senderThread = network.SenderThread(csock)
                clientConn.senderThread.Start()
                clientConn.listenerThread = ListenerThread(self, clientConn)
                clientConn.listenerThread.Start()
                clientConn.sync()

        thread.start_new_thread(run, ())

    def recv(self):
        """ Return (clientConn, messageDict), blocking until a message is
        available.  Messages received using this function are all of type 'gm' -
        other types are received using postEvent only. """
        if self.paused:
            # Wait for the communicator to be unpaused.  The effect of acquire()
            # and immediate release() is that all threads calling this method
            # when the communicator is paused will wait for the lock to be
            # released by the thread that locked it by calling pause().  Once
            # that thread unlocks it, allowing these threads to continue, they
            # might as well release their own locks immediately after acquiring.
            self.pauseLock.acquire()
            self.pauseLock.release()

        return self.inQueue.get()

    def recv_nowait(self):
        """ Return (clientConn, messageDict), or None if no message is
        available.  Non-blocking, unless the communicator is paused. """
        if self.paused:
            self.pauseLock.acquire()
            self.pauseLock.release()
        try:
            mes = self.inQueue.get_nowait()
        except Queue.Empty:
            return None
        else:
            return mes

    def send(self, clientConn, message):
        if self.paused and message['type'] == 'gm':
            # Here, we allow threads to bypass the pauseLock if they are not
            # sending a game message (e.g., messages need to be sent during the
            # reconnection process).
            self.pauseLock.acquire()
            self.pauseLock.release()
        clientConn.senderThread.send(message)

    def pause(self):
        """ Cause all calls to recv(), recv_nowait() to block until unpause() is
        called, and cause all calls to send(message) where message['type'] ==
        'gm' to block until unpause is called.  No effect if already paused.
        Also, cancels any running timer (see self.cancelTimer()). """
        # It's important that self.paused=True comes after acquire().
        # Explanation a bit too lengthy.
        if self.paused:
            return
        self.pauseLock.acquire()
        self.paused = True
        self.cancelTimer()

    def unpause(self):
        """ No effect if not paused. """
        if not self.paused:
            return
        self.paused = False
        self.pauseLock.release()

    def startTimer(self, interval):
        """ Start a timer that will run for <interval> seconds and then put a
        timer expiration message on the queue (which will be picked up by recv()
        just as a normal game message).  The message will look like this:
        {'type': 'gm', 'subtype': 'timeup'}
        and will have None in place of the client connection object. """

        self.timerInterval = interval

        def timeup():
            self.timer = None
            self.inQueue.put((None, {'type': 'gm', 'subtype': 'timeup'}))

        self.timer = threading.Timer(interval, timeup)
        self.timer.start()
        self.timerStartTime = time.time()

    def cancelTimer(self):
        """ Cancel the timer, and don't send the timeup message.  No effect if
        the timer is not running.  Also sets a variable self.timeLeftAtCancel
        that is the number of seconds remaining on the timer at the moment it
        was canceled. """
        if self.timer != None:
            self.timer.cancel()
            elapsed = time.time() - self.timerStartTime
            self.timeLeftAtCancel = self.timerInterval - elapsed
            print 'timeLeftAtCancel =', self.timeLeftAtCancel

    def getTimeElapsed(self):
        """ Get the number of seconds since the timer was started. """
        return time.time() - self.timerStartTime
    
    def getTimeLeft(self):
        """ Get the number of seconds remaining on the timer. """
        #              Total time - elapsed time
        return self.timerInterval - (time.time() - self.timerStartTime)


class ClientConnection:

    """
    A ClientConnection contains all the relevant information about
    communicating with a client (importantly, it houses the connection
    object representing the socket connection).  Also, the Listener and
    SenderThreads.
    """

    def __init__(self, id, sock, address):
        self.id = id
        self.sock = sock
        self.address = address
        self.listenerThread = None
        self.senderThread = None
        self.syncQueue = Queue.Queue() # Client's sync replies get put here
        self.clockOffset = 0

    def close(self):
        """ Shut down the listenerThread, the senderThread, and close the
        socket. """
        self.listenerThread.Stop()
        self.senderThread.Stop()
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except socket.error:
            print 'ClientConnection.close(): caught exception on '\
                    + 'sock.shutdown() (OK)'

        self.sock.close()

    def sync(self):
        """ Synchronize with the client (that is, learn the difference between
        the server's clock and the client's clock). """

        sync_count = 4

        rtt = 999
        for i in range(sync_count):
            st1 = time.time()
            self.senderThread.send({'type': 'sync'})
            reply = self.syncQueue.get()
            st2 = time.time()
            new_rtt = st2 - st1
            if new_rtt < rtt:
                rtt = new_rtt
                self.clockOffset = reply['ct'] + rtt / 2 - st2

        clientID = self.id+1 if self.id != None else "(no ID)"
        print 'synchronized with client', clientID, ': clockOffset =',\
            self.clockOffset

class ListenerThread:

    """
    {ListenerThread} listens on the specified connection (to a single client)
    for messages.  When a message is received, it puts it on the queue and then
    waits for the next message.
    """

    def __init__(self, communicator, client):
        """
        Initializes the thread.  No action is taken; use
        C{Start()} to launch the thread.

        @param client: The client that should receive the message
        @type client: C{ClientConnection}
        @param communicator: the Communicator that created this thread
        """
        self.client = client
        self.queue = communicator.inQueue
        self.postEvent = communicator.postEvent
        self.keepListening = True

    def Start(self):
        """
        Does the actual business of running the thread.
        Call this member when the thread is to be launched.
        """
        self.keepListening = True
        thread.start_new_thread(self.Run, ())

    def Stop(self):
        """ Stop the thread (causes the Run function to terminate after the
        current call to network.recvmessage() returns). """
        self.keepListening = False

    def Run(self):
        """
        The program body for the thread.  This is not called
        directly, but is launched indirectly using the C{Start}
        member.
        """

        leftovers = ''
        while self.keepListening:
            try:
                pmessage, leftovers = network.recvmessage(self.client.sock,
                        leftovers)
                if pmessage == None:
                    print "ListenerThread: connection closed; terminating"
                    # FIXME: change client status to disconnected, notify GUI
                    self.keepListening = False
                    break
            except:
                print "ListenerThread: caught exception; terminating: "
                print "    ", sys.exc_info()
                self.keepListening = False
                break

            else:
                message = cerealizer.loads(pmessage)
                if message['type'] == 'gm':
                    # Only place Game Messages ('gm') on the queue.
                    self.queue.put((self.client, message))
                elif message['type'] == 'sync':
                    # Place sync messages on the client's sync queue (client is
                    # responding to server's sync message)
                    self.client.syncQueue.put(message)
                self.postEvent(self.client, message)

        # Thread is terminating.
        self.postEvent(self.client, {'type': 'disconnect'})
