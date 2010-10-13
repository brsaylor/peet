#!/usr/bin/env python

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

# See survey.py for the bigger picture.

import os
import os.path
import cgi
import cgitb; cgitb.enable()
import csv
import re

print "Content-Type: text/html"     # HTML is following
print                               # blank line, end of headers

# Environment variables set by survey.py
outputDir = os.environ['outputDir']
sessionID = os.environ['sessionID']
experimentID = os.environ['experimentID']

form = cgi.FieldStorage()

id = int(form.getfirst('subject'))
outfilename = os.path.join(outputDir, sessionID + '-survey' + str(id) + '.csv')

# In case someone submits the form a second time by mistake, or someone submits
# a form under the wrong ID,
# avoid overwriting existing file by trying for unique filenames in this order:
# 080915165617-survey0.csv
# 080915165617-survey0_1.csv
# 080915165617-survey0_2.csv
# etc...
num = 0
while os.path.exists(outfilename):
    num += 1
    outfilename = re.sub('survey.*$', 'survey%d_%d.csv' % (id,num), outfilename)

# Write header and values to CSV file
outfile = open(outfilename, 'w')
csvwriter = csv.writer(outfile)
csvwriter.writerow(['sessionID', 'experimentID'] + form.keys())
values = [sessionID, experimentID]
for key in form.keys():
    values.append(form.getfirst(key))
csvwriter.writerow(values)
outfile.close()

print "<TITLE>Thank you</TITLE>"
print "<H1>Survey processed successfully</H1>"
print "<p>Please wait for your name to be called as we count your earnings.</p>"
print "<p>Thank you for your participation.<p>"
