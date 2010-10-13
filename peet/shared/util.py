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

""" Miscellaneous utility functions """

import math
import random
random.seed()

def discrete(values, probabilities):
    """ Draw a random number from the discrete probability distribution given by
    the list of values and the list of corresponding probabilities.
    Probabilities need not total 1. """

    r = random.uniform(0, sum(probabilities))
    #print 'drew random number r = ' + str(r)
    c = 0
    for i, p in enumerate(probabilities):
        c += p
        #print 'c = ' + str(c)
        if r < c:
            #print ('r < c -- found it!  values[%d] = ' % i) + str(values[i])
            return values[i]

def stepround(value, steps, alwaysRoundUp=False):
    """ Round the given real number to the nearest rational number such that it
    could be expressed precisely as a fraction with an integer numerator and an
    integer denominator equal to 'steps'.
    Examples:
        stepround(1.234, 2) -> 1.5
        stepround(1.234, 4) -> 1.25
        stepround(1.234, 10) -> 1.2 """
    if alwaysRoundUp:
        return math.ceil(float(value) * steps) / steps
    else:
        return round(float(value) * steps) / steps

def randomdivide(Q, N):
    """ Return a list of N positive random integers that sum to positive integer
    quantity Q. """
    # Imagine Q pebbles lined up.
    # Randomly determine N-1 distinct positions in the line.
    # Separate the pebbles at those positions, resulting in N little lines of
    # pebbles, each having a random number of pebbles.

    positions = random.sample(xrange(1, Q), N-1)
    positions.append(Q)
    positions.sort()
    qlist = []
    prevPos = 0
    for pos in positions:
        # give this pile everything from prevPos up through pos-1.
        qlist.append(pos - prevPos)
        prevPos = pos
    return qlist

# Doesn't work - delete
def squashed_normalvariate(
        mu, sigma, trunc_min, trunc_max, flatness=0.0, tries=10):

    triesLeft = tries
    while triesLeft > 0:
        normalPart = random.normalvariate(mu, sigma)
        if normalPart >= trunc_min and normalPart <= trunc_max:
            break
        triesLeft -= 1

    if triesLeft == 0:
        print "squashed_normalvariate: %d tries exceeded, so clipping" % tries
        if normalPart < trunc_min: normalPart = trunc_min
        elif normalPart > trunc_max: normalPart = trunc_max

    uniformPart = random.uniform(trunc_min, trunc_max)

    combined = normalPart * (1.0 - flatness) + uniformPart * flatness

    return combined

def truncated_draw(func, args, trunc_min, trunc_max, tries=10):
    """ Draw a random number from the random number function "func", supplied
    with the arguments contained in the tuple "args", repeating "tries" times
    until the result lies between "trunc_min" and "trunc_max", inclusive.  If
    after "tries" times the result is still outside the given range, force by
    clipping.  Return the result. """

    triesLeft = tries
    while triesLeft > 0:
        x = func(*args)
        if x >= trunc_min and x <= trunc_max: 
            break
        triesLeft -= 1

    if triesLeft == 0:
        print "truncated_draw(): %d tries exceeded, so clipping" % tries
        if x < trunc_min: x = trunc_min
        elif x > trunc_max: x = trunc_max

    return x
