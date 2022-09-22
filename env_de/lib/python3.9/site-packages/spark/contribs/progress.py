#   This library is free software; you can redistribute it and/or
#   modify it under the terms of the GNU Lesser General Public
#   License as published by the Free Software Foundation; either
#   version 2.1 of the License, or (at your option) any later version.
#
#   This library is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public
#   License along with this library; if not, write to the 
#      Free Software Foundation, Inc., 
#      59 Temple Place, Suite 330, 
#      Boston, MA  02111-1307  USA

# This file is part of urlgrabber, a high-level cross-protocol url-grabber
# Copyright 2002-2004 Michael D. Stenner, Ryan Tomayko

# $Id: progress.py,v 1.7 2005/08/19 21:59:07 mstenner Exp $

import sys
import time
import math
    
class BaseMeter:
    def __init__(self):
        self.update_period = 0.3 # seconds

        self.filename   = None
        self.url        = None
        self.basename   = None
        self.text       = None
        self.size       = None
        self.start_time = None
        self.last_amount_read = 0
        self.last_update_time = None
        self.re = RateEstimator()
        
    def start(self, filename=None, url=None, basename=None,
              size=None, now=None, text=None):
        self.filename = filename
        self.url      = url
        self.basename = basename
        self.text     = text

        #size = None #########  TESTING
        self.size = size
        if not size is None: self.fsize = format_number(size) + 'B'

        if now is None: now = time.time()
        self.start_time = now
        self.re.start(size, now)
        self.last_amount_read = 0
        self.last_update_time = now
        self._do_start(now)
        
    def _do_start(self, now=None):
        pass

    def update(self, amount_read, now=None):
        # for a real gui, you probably want to override and put a call
        # to your mainloop iteration function here
        if now is None: now = time.time()
        if (now >= self.last_update_time + self.update_period) or \
               not self.last_update_time:
            self.re.update(amount_read, now)
            self.last_amount_read = amount_read
            self.last_update_time = now
            self._do_update(amount_read, now)

    def _do_update(self, amount_read, now=None):
        pass

    def end(self, amount_read, now=None):
        if now is None: now = time.time()
        self.re.update(amount_read, now)
        self.last_amount_read = amount_read
        self.last_update_time = now
        self._do_end(amount_read, now)

    def _do_end(self, amount_read, now=None):
        pass
        
class TextMeter(BaseMeter):
    def __init__(self, fo=sys.stderr):
        BaseMeter.__init__(self)
        self.fo = fo

    def _do_update(self, amount_read, now=None):
        etime = self.re.elapsed_time()
        fetime = format_time(etime)
        fread = format_number(amount_read)
        #self.size = None
        if self.text is not None:
            text = self.text
        else:
            text = self.basename
        if self.size is None:
            out = '\r%-60.60s    %5sB %s ' % \
                  (text, fread, fetime)
        else:
            rtime = self.re.remaining_time()
            frtime = format_time(rtime)
            frac = self.re.fraction_read()
            bar = '='*int(25 * frac)

            out = '\r%-25.25s %3i%% |%-25.25s| %5sB %8s ETA ' % \
                  (text, frac*100, bar, fread, frtime)

        self.fo.write(out)
        self.fo.flush()

    def _do_end(self, amount_read, now=None):
        total_time = format_time(self.re.elapsed_time())
        total_size = format_number(amount_read)
        if self.text is not None:
            text = self.text
        else:
            text = self.basename
        if self.size is None:
            out = '\r%-60.60s    %5sB %s ' % \
                  (text, total_size, total_time)
        else:
            bar = '='*25
            out = '\r%-25.25s %3i%% |%-25.25s| %5sB %8s     ' % \
                  (text, 100, bar, total_size, total_time)
        self.fo.write(out + '\n')
        self.fo.flush()

class RateEstimator:
    def __init__(self, timescale=5.0):
        self.timescale = timescale

    def start(self, total=None, now=None):
        if now is None: now = time.time()
        self.total = total
        self.start_time = now
        self.last_update_time = now
        self.last_amount_read = 0
        self.ave_rate = None
        
    def update(self, amount_read, now=None):
        if now is None: now = time.time()
        if amount_read == 0:
            # if we just started this file, all bets are off
            self.last_update_time = now
            self.last_amount_read = 0
            self.ave_rate = None
            return

        #print 'times', now, self.last_update_time
        time_diff = now         - self.last_update_time
        read_diff = amount_read - self.last_amount_read
        self.last_update_time = now
        self.last_amount_read = amount_read
        self.ave_rate = self._temporal_rolling_ave(\
            time_diff, read_diff, self.ave_rate, self.timescale)
        #print 'results', time_diff, read_diff, self.ave_rate
        
    #####################################################################
    # result methods
    def average_rate(self):
        "get the average transfer rate (in bytes/second)"
        return self.ave_rate

    def elapsed_time(self):
        "the time between the start of the transfer and the most recent update"
        return self.last_update_time - self.start_time

    def remaining_time(self):
        "estimated time remaining"
        if not self.ave_rate or not self.total: return None
        return (self.total - self.last_amount_read) / self.ave_rate

    def fraction_read(self):
        """the fraction of the data that has been read
        (can be None for unknown transfer size)"""
        if self.total is None: return None
        elif self.total == 0: return 1.0
        else: return float(self.last_amount_read)/self.total

    #########################################################################
    # support methods
    def _temporal_rolling_ave(self, time_diff, read_diff, last_ave, timescale):
        """a temporal rolling average performs smooth averaging even when
        updates come at irregular intervals.  This is performed by scaling
        the "epsilon" according to the time since the last update.
        Specifically, epsilon = time_diff / timescale

        As a general rule, the average will take on a completely new value
        after 'timescale' seconds."""
        epsilon = time_diff / timescale
        if epsilon > 1: epsilon = 1.0
        return self._rolling_ave(time_diff, read_diff, last_ave, epsilon)
    
    def _rolling_ave(self, time_diff, read_diff, last_ave, epsilon):
        """perform a "rolling average" iteration
        a rolling average "folds" new data into an existing average with
        some weight, epsilon.  epsilon must be between 0.0 and 1.0 (inclusive)
        a value of 0.0 means only the old value (initial value) counts,
        and a value of 1.0 means only the newest value is considered."""
        
        try:
            recent_rate = read_diff / time_diff
        except ZeroDivisionError:
            recent_rate = None
        if last_ave is None: return recent_rate
        elif recent_rate is None: return last_ave

        # at this point, both last_ave and recent_rate are numbers
        return epsilon * recent_rate  +  (1 - epsilon) * last_ave

    def _round_remaining_time(self, rt, start_time=15.0):
        """round the remaining time, depending on its size
        If rt is between n*start_time and (n+1)*start_time round downward
        to the nearest multiple of n (for any counting number n).
        If rt < start_time, round down to the nearest 1.
        For example (for start_time = 15.0):
         2.7  -> 2.0
         25.2 -> 25.0
         26.4 -> 26.0
         35.3 -> 34.0
         63.6 -> 60.0
        """

        if rt < 0: return 0.0
        shift = int(math.log(rt/start_time)/math.log(2))
        rt = int(rt)
        if shift <= 0: return rt
        return float(int(rt) >> shift << shift)
        

def format_time(seconds, use_hours=0):
    if seconds is None or seconds < 0:
        if use_hours: return '--:--:--'
        else:         return '--:--'
    else:
        seconds = int(seconds)
        minutes = seconds / 60
        seconds = seconds % 60
        if use_hours:
            hours = minutes / 60
            minutes = minutes % 60
            return '%02i:%02i:%02i' % (hours, minutes, seconds)
        else:
            return '%02i:%02i' % (minutes, seconds)
            
def format_number(number, SI=0, space=' '):
    """Turn numbers into human-readable metric-like numbers"""
    symbols = ['',  # (none)
               'k', # kilo
               'M', # mega
               'G', # giga
               'T', # tera
               'P', # peta
               'E', # exa
               'Z', # zetta
               'Y'] # yotta
    
    if SI: step = 1000.0
    else: step = 1024.0

    thresh = 999
    depth = 0
    max_depth = len(symbols) - 1
    
    # we want numbers between 0 and thresh, but don't exceed the length
    # of our list.  In that event, the formatting will be screwed up,
    # but it'll still show the right number.
    while number > thresh and depth < max_depth:
        depth  = depth + 1
        number = number / step

    if type(number) == type(1) or type(number) == type(1L):
        # it's an int or a long, which means it didn't get divided,
        # which means it's already short enough
        format = '%i%s%s'
    elif number < 9.95:
        # must use 9.95 for proper sizing.  For example, 9.99 will be
        # rounded to 10.0 with the .1f format string (which is too long)
        format = '%.1f%s%s'
    else:
        format = '%.0f%s%s'
        
    return(format % (float(number or 0), space, symbols[depth]))
