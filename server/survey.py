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

import os
import os.path
import shutil
import re
import thread

import BaseHTTPServer
import CGIHTTPServer

def start(server,sessionID,experimentID, outputDir, surveyFilename, numClients):
    thread.start_new_thread(run,\
            (server, sessionID, experimentID, outputDir, surveyFilename,\
            numClients))

def run(server, sessionID, experimentID, outputDir, surveyFilename, numClients):

    print 'survey.run():'
    print '  sessionID = ', sessionID
    print '  outputDir = ', outputDir
    print '  surveyFilename = ', surveyFilename
    print '  numClients = ', numClients

    webroot = os.path.join(os.path.dirname(__file__), 'webroot')

    # copy the survey file to output dir
    dirname, filename = os.path.split(surveyFilename)
    copyFilename = os.path.join(outputDir, sessionID + '-surveypage.html')
    shutil.copy(surveyFilename, copyFilename)

    # read the data
    infile = open(surveyFilename, 'r')
    inhtml = infile.read()
    infile.close()

    # tweak and copy into webroot a version of the survey file for each client
    for c in range(numClients):

        groupID = ''
        if server.clients[c].group != None:
            groupID = str(server.clients[c].group.id)

        outhtml = re.sub('<form.*?>',\
                '<form action="/cgi-bin/submit-survey.py" method="POST">'\
                        '<input type="hidden" name="subject" value="%d">' % c\
                        + '<input type="hidden" name="group" value="%s">'\
                        % groupID,\
                inhtml)
        outfile = open(os.path.join(webroot, 'survey%d.html' % c), 'w')
        outfile.write(outhtml)
        outfile.close()

    # set the needed parameters as environment variables, so the CGI script can
    # get them.
    os.environ['sessionID'] = sessionID
    os.environ['experimentID'] = experimentID
    os.environ['outputDir'] = outputDir

    # start server
    ServerClass = BaseHTTPServer.HTTPServer
    HandlerClass = SurveyHTTPRequestHandler
    os.chdir(webroot)
    port = 9124
    server_address = ('', port)
    protocol="HTTP/1.0"
    HandlerClass.protocol_version = protocol
    httpd = ServerClass(server_address, HandlerClass)
    sa = httpd.socket.getsockname()
    print "Serving HTTP on", sa[0], "port", sa[1], "..."
    httpd.serve_forever()

class SurveyHTTPRequestHandler(CGIHTTPServer.CGIHTTPRequestHandler):

    def do_POST(self):
        """ For security, reject POST requests to any path except
        /cgi-bin/submit-survey.py.

        Then pass it along to the real do_POST().
        """

        print 'SurveyHTTPRequestHandler.do_POST()'

        if self.path != '/cgi-bin/submit-survey.py':
            print 'Rejecting POST to ', self.path
            self.send_error(404, "Invalid path to CGI script.")
        else:
            CGIHTTPServer.CGIHTTPRequestHandler.do_POST(self)
