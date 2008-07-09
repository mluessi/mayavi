# Author: Ilan Schnell <ischnell@enthought.com>
# Copyright (c) 2008, Ilan Schnell, Enthought, Inc.
# License: BSD Style.

# TODO: should derive from HasTraits

import csv

# FIXME: see loadtxt.py (should really be the loadtxt from numpy)
from enthought.mayavi.tools.wizards.loadtxt import loadtxt


class Sniff(object):
    """ Sniff a CSV file and determine some of it's properties.

        The properties determined here allow an CSV of unknown format
        to be read by numpy.loadtxt, i.e. the methods and attributes
        are suitable to determine required keyword arguments for
        numpy.loadtxt

        For a usecase, see csv_sniff.loadtxt_unknown
    """
    def __init__(self, filename):
        self._lines = self._read_few_lines(filename)
        self._reallines = [line for line in self._lines if line.strip()]
        self._dialect = csv.Sniffer().sniff(self._reallines[-1])
        
        self._comment = '#'
        self._check_comment()
        
        self._usePySplit = not self._dialect.delimiter.strip()
        
        self._numcols = len(self._split(self._reallines[0]))
        
        self._datatypes = self._datatypes_of_line(self._reallines[-1])
        
    def _check_comment(self):
        line0 = self._reallines[0]
        if line0.startswith(('#', '%')):
            self._comment = line0[0]
            self._reallines[0] = self._dialect.delimiter.join(line0.split()[1:])
            for i in xrange(1, len(self._reallines)):
                self._reallines[i] = \
                    self._reallines[i].split(self._comment)[0]
    
    def _read_few_lines(self, filename):
        res = []
        for line in open(filename, 'rb'):
            line = line.strip()
            res.append(line)
            if len(res) > 10:
                break
        return res
    
    def _split(self, line):
        if self._usePySplit:
            return line.split()
        else:
            return csv.reader([line], self._dialect).next()
    
    def _names(self):
        line0 = self._reallines[0]
        if self._datatypes_of_line(line0) == self._datatypes:
            return tuple('Column %i' % (i+1) for i in xrange(self._numcols))
        else:
            return tuple(t.strip('"\' \t') for t in self._split(line0))

    def _formats(self):
        res = []
        for c, t in enumerate(self._datatypes):
            if t == str:
                items = [len(self._split(l)[c]) for l in self._reallines[1:]
                         if self._datatypes_of_line(l) == self._datatypes]
                items.append(1)
                res.append('S%i' % max(items))
                
            elif t == float:
                res.append(t)

            else:
                raise TypeError("Hmm, did not expect: %r" % t)
                
        return tuple(res)
    
    def _datatypes_of_line(self, line):

        def isFloat(s):
            try:
                float(s)
                return True
            except ValueError:
                return False
            
        res = []
        for s in self._split(line):
            if isFloat(s):
                res.append(float)
            else:
                res.append(str)
                
        return tuple(res)

    #-----------------------------------------------------------------------
    # Public API:
    #-----------------------------------------------------------------------
    
    def comments(self):
        return self._comment
    
    def delimiter(self):
        if self._usePySplit:
            return ''
        else:
            return self._dialect.delimiter
    
    def skiprows(self):
        for n, line in enumerate(self._lines):
            if self._datatypes == self._datatypes_of_line(line):
                return n
    
    def dtype(self):
        return {'names': self._names(),
                'formats': self._formats()}



def loadtxt_unknown(filename, verbose=0):
    """ Like numpy.loadtxt but more general, in the sense that it uses
        Sniff first to determine the necessary keyword arguments for loadtxt.
    """
    s = Sniff(filename)
    
    if verbose:
        print '===== Sniffed information for file %r:' % filename
        print 'delimiter = %r' % s.delimiter()
        print 'comments  = %r' % s.comments()
        print 'dtype     = %r' % s.dtype()
        print 'skiprows  = %r' % s.skiprows()

    return loadtxt(filename,
                   delimiter = s.delimiter() if s.delimiter() else None,
                   comments  = s.comments(),
                   dtype     = s.dtype(),
                   skiprows  = s.skiprows())


def array2dict(arr):
    """ Takes an array with  special names dtypes and returns a dict where
        each name is a key and the corresponding data (as a 1d array) is the
        value.
    """
    d = {}
    for k in arr.dtype.names:
        d[k] = arr[k]
        
    return d