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

import random

def makeGroups(num):
    """ Return a list of newly created groups.  Each group's id attribute is set
    to its index in the list.  The game controller class should use this.  Does
    not assign clients to the group - do this using GroupData.assignClients().
    """
    groups = []
    for i in range(num):
        groups.append(GroupData(i))
    return groups

def groupClients_simple(clients, groupSize=None, numGroups=None):
    """ Create groups and assign clients to them in a simple fashion.  Takes
    either groupSize (number of clients per group) or numGroups (number of
    groups), with groupSize taking precedence if both are given.  Clients are
    assigned sequentially in whatever order they are given in the clients
    parameter (list of ClientData).  All groups will have the same number of
    clients, except possibly the last one, which is where "leftover" clients go.
    Return the list of GroupData. """

    if groupSize != None:
        # Use groupSize if available, setting numGroups (overriding parameter
        # value, in the case that both are given)
        numGroups = int(len(clients)) / int(groupSize)
        if int(len(clients)) % int(groupSize) > 0:
            numGroups += 1
    elif numGroups != None:
        # Otherwise, use numGroups if available, setting groupSize
        if numGroups > len(clients):
            numGroups = len(clients)
        groupSize = int(len(clients)) / int(numGroups)
        if int(len(clients)) % int(numGroups) > 0:
            groupSize += 1
    else:
        # Neither groupSize nor numGroups were given; can't do anything
        return None

    groups = makeGroups(numGroups)
    for group in groups:
        groupClients = clients[group.id*groupSize : (group.id+1)*groupSize]
        group.assignClients(groupClients)

    # Check group assignments
    print 'groupClients_simple: '
    for group in groups:
        print "group ", group.id
        for client in group.clients:
            print 'client ', client.id
    
    return groups

def groupClients_random(clients, groupSize=None, numGroups=None):
    """ This just shuffles the clients (without altering the original clients
    list) and then calls groupClients_simple on the shuffled list."""
    clients2 = []
    for c in clients:
        clients2.append(c)
    random.shuffle(clients2)
    return groupClients_simple(clients2, groupSize, numGroups)

class GroupData:
    """ GroupData is used for grouping clients, e.g. when outcomes depend on the
    actions of all the players in the group, and you want to have it only affect
    those players. Contains a sequential ID of the group, the list of clients,
    and then whatever other data attributes you assign to it. """

    def __init__(self, id):
        self.id = id
        self.clients = []

    def assignClients(self, clients):
        """ Assign the given list of clients to this group, replacing any
        clients already assigned to this group.  Also give the ClientData
        objects the group assignment. """
        for client in self.clients:
            client.group = None
        for client in clients:
            client.group = self
        self.clients = clients
