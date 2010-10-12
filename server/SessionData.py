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

""" A "session" is one run of an experiment.  A single SessionData object holds
variables associated with this session that need to be accessed from different
classes (the server, the GameControl, the HistoryWriter, etc.). """

# FIXME: Not sure about this idea.  Was going to put server, params,
# communicator, clients, outputDir, sessionID in here.  But does it make sense
# to hand around this object containing all this stuff, rather than just handing
# around the subset of info needed by a particular object? (e.g. the
# HistoryWriter only needs the client histories, output dir, and session ID)

class SessionData:

    def __init__(self):
        pass
