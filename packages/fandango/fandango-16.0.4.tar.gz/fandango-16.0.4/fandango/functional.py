#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
#############################################################################
##
## project :     Functional tools for Tango Control System
##
## $Author:      Sergi Rubio Manrique, srubio@cells.es $
##
## $Revision:    2008 $
##
## copyleft :    ALBA Synchrotron Controls Section, CELLS
##               Bellaterra
##               Spain
##
#############################################################################
##
## This file is part of Tango Control System
##
## Tango Control System is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as published
## by the Free Software Foundation; either version 3 of the License, or
## (at your option) any later version.
##
## Tango Control System is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <http://www.gnu.org/licenses/>.
####################################################################@########
"""

from .futurize import (division, print_function, hex, chr,
    filter, next, zip, map, range, basestring, unicode, old_div)

__doc__ = """
fandango.functional::
    contains functional programming methods for python, it should use only python main library methods and not be dependent of any other module
    
.. contents::

"""

import re
import random
import math
import time, datetime
import sys
import pickle
import traceback
import builtins

py3 = sys.version_info.major >= 3
if py3:
    long = int

try:
    #python3
    from collections.abc import Iterable, Hashable, Sequence, Container, Sized
except:
    #python2  # do not import more types from it, too ambiguous
    from collections import Iterable, Hashable

from functools import partial
from itertools import count, cycle, repeat, chain, groupby, islice, starmap
from itertools import dropwhile, takewhile, filterfalse

try:
    from itertools import combinations, permutations, product
except:
    pass

__test__ = {}

# Load all by default
# __all__ = [
#'partial','first','last','anyone','everyone',
#'notNone','isTrue','join','splitList','contains',
#'matchAll','matchAny','matchMap','matchTuples','inCl','matchCl','searchCl',
#'toRegexp','isString','isRegexp','isNumber','isSequence','isDictionary','isIterable','isMapping',
#'list2str','char2int','int2char','int2hex','int2bin','hex2int',
#'bin2unsigned','signedint2bin',
# ]

########################################################################
## Some miscellaneous logic methods
########################################################################

def first(seq, default=Exception):
    """Returns first element of sequence"""
    try:
        seq = getcallable(seq,'keys',seq)
        if hasattr(seq,'__getitem__'):
            return seq[0]
        elif not hasattr(seq,'__next__'):
            seq = iter(seq)
        return next(iter(seq))
    except Exception as e:
        if default is not Exception:
            return default
        else:
            raise e

def last(seq, MAX=50000, default=Exception):
    """
    Returns last element of sequence

    default value controls what happens if end is not reached
    default = exception, raises error if seq is a generator longer than MAX
    default = None, returns last value read, or None with empty list
    else, will return default if MAX is reached
    """
    try:
        return seq[-1]
    except Exception as e:
        try:
            n = next(seq)
        except:
            if default is not Exception:
                return default
            else:
                raise e
        try:
            for i in range(1, MAX + 1):
                n = next(seq)  # will except when reaching the end
            if i > (MAX - 1):
                if default is Exception:
                    raise IndexError("MAX index reached")
                elif default is None:
                    return n
                else:
                    return default
        except StopIteration as e:  # It catches generators end
            return n
    return


max = max
min = min

def next_power_of_2(x):  
    return int(1 if x == 0 else 2**int(x - 1).bit_length())

def avg(seq):
    """returns the average value of the sequence"""
    a, l = 0, 0
    for v in seq:
        if v is not None:
            a, l = a + float(v), l + 1
    return (a/l) if l else 0


def peak(seq):
    """
    given a sequence, it returns the value that differs most from average
    it can be either max or min
    """
    a, l = 0, 0
    m, n = -float('inf'), float('inf')
    for v in seq:
        if v is not None:
            m = v if not l or v > m else m
            n = v if not l or v < n else n
            a, l = a + float(v), l + 1
    a = float(a) / l
    return m if abs(m - a) > abs(n - a) else n


def rms(seq):
    """returns the rms value (sqrt of the squares average)"""
    seq = [float(s) ** 2 for s in seq if s is not None]
    if not bool(seq) or not len(seq):
        return 0
    return math.sqrt(sum(seq) / float(len(seq)))


def meandev(seq):
    """mean deviation of a list"""
    a = avg(seq)
    return sum(abs(v - a) for v in seq) / float(len(seq))


def stdev(seq):
    """standard deviation of a list"""
    a = avg(seq)
    return math.sqrt(sum(abs(v - a) ** 2 for v in seq) / float(len(seq)))


def floor(x, unit=1):
    """Returns greatest multiple of 'unit' below 'x'"""
    return unit * int(old_div(x, unit))


def xor(A, B):
    """
    Returns (A and not B) or (not A and B);
    the difference with A^B is that it works also with different types
    and returns one of the two objects..
    If both objects are True, False is returned
    """
    v = (A and not B) or (not A and B)
    if v is True and (A and not B):
        return A
    else:
        return v


def reldiff(x, y, floor=None):
    """
    Checks relative (%) difference <floor between x and y
    floor would be a decimal value, e.g. 0.05
    """
    d = x - y
    if not d:
        return 0
    ref = x or y
    d = float(d) / ref
    return d if not floor else (0, d)[abs(d) >= floor]
    # return 0 if x*(1-r)<y<x*(1+r) else -1


def absdiff(x, y, floor=0):
    """
    Checks absolute difference between x and y
    If diff < floor, 0 is returned
    floor would be a decimal value, e.g. 0.05
    """
    d = abs(x - y)
    if floor and d < floor:
        d = 0
    return d


def seqdiff(x, y, method=reldiff, floor=None):
    """
    Being x and y two arrays it checks (method) difference
    smaller than  floor between the elements of them.

    floor would be a decimal value, e.g. 0.05
    """
    if not floor:
        d = any(method(v, w) for v, w in zip(x, y))
    else:
        d = any(method(v, w, floor) for v, w in zip(x, y))
    return d


def join(*seqs):
    """It returns a list containing the objects of all given sequences."""
    if len(seqs) == 1 and isSequence(seqs[0]):
        seqs = seqs[0]
    result = []
    for seq in seqs:
        if isSequence(seq):
            result.extend(seq)
        else:
            result.append(seq)
    #    result += list(seq)
    return result

flatten = join

def djoin(a, b):
    """This method merges dictionaries and/or lists"""
    if not any(map(isDictionary, (a, b))):
        return join(a, b)
    other, dct = sorted((a, b), key=isDictionary)
    dct = dict(dct)
    if not isDictionary(other):
        other = dict.fromkeys(
            other
            if isSequence(other)
            else [
                other,
            ]
        )
    for k, v in list(other.items()):
        dct[k] = v if not k in dct else djoin(dct[k], v)
    return dct

def ksorted(sequence):
    """
    safe key sorting preventing TypeError, but unefficient in memory/time
    """
    try:
        if isGenerator(sequence):
            sequence = list(sequence)
        return sorted(sequence)
    except TypeError:
        return sorted(sequence,key=str)

def kmap(method, keys, values=None, sort=True, kwargs={}):
    """
    Given a method and a list of keys, this method will return a list
    of (key,method(key)) values.

    @param values: list of values to pass as argument instead of keys
    @param sort: return values sorted by key

    """
    g = (
        (k, method(k if not values else values[i], **kwargs))
        for i, k in enumerate(keys)
    )
    return ksorted(g) if sort else list(g)

def lmap(method, keys):
    """
    return map(method,keys) as a list
    """
    return list(map(method,keys))

def forever(seq):
    """iterates a sequence in an infinite loop"""
    while True:
        for i in seq:
            yield i

def randomize(seq):
    """returns a randomized version of the list"""
    if isGenerator(seq):
        seq = list(seq)
    done, result = list(range(len(seq))), []
    while done:
        result.append(seq[done.pop(random.randrange(len(done)))])
    return result


def randpop(seq):
    """removes and returns a random item from the sequence"""
    return seq.pop(random.randrange(len(seq)))


def unpack(seqs, index=None):
    """
    extract given indexes from a sequence

    unpack([(a,b,c),(d,e,f),(g,h,i)],(0,2)) => ((a,c),(d,f),(g,i))
    """
    if isinstance(index, int):
        return (s[index] for s in seqs)
    else:
        # return (tuple(s[i] for i in index) for s in seqs)
        return ((s[i] for i in index) for s in seqs)


def unzip(seqs, index=None):
    """
    reverse zip operation between sequences, allowing to choose index

    unzip([(a,b,c),(d,e,f),(g,h,i)],(0,2)) => ((a,d,g),(c,f,i))
    """
    if index is None:
        return list(zip(*seqs))
    elif isinstance(index, int):
        return (s[index] for s in seqs)
    else:
        # return (tuple(s[i] for i in index) for s in seqs)
        return ((s[i] for s in seqs) for i in index)


# __test__['kmap'] = [
# {'args':[lowstr,'BCA','YZX',False],'result':[('A', 'x'), ('B', 'y'), ('C', 'z')]}
# ]


def splitList(seq, split):
    """splits a list in lists of 'split' size"""
    # return [seq[split*i:split*(i+1)] for i in range(1+len(seq)/split)]
    return [seq[i : i + split] for i in range(len(seq))[::split]]


def contains(a, b, regexp=True):
    """
    Returns a in b;
    using a as regular expression if wanted
    """
    if a in b:
        return True
    elif regexp:
        return inCl(a, b, regexp)


def anyone(seq, method=bool):
    """
    Like any(), but returns first that is true or last that is false
    """
    if not seq:
        return False
    s = None
    for s in seq:
        if method(s):
            return s
    return s if not s else None


def everyone(seq, method=bool):
    """Returns last that is true or first that is false"""
    if not seq:
        return False
    for s in seq:
        if not method(s):
            return s if not s else None
    return seq[-1]


# Dictionary methods


def setitem(seq, key, value, default=Exception):
    # easy override of list/dict setitem methods
    try:
        seq[key] = value
    except Exception as e:
        if default is Exception:
            raise e
        if isinstance(seq, (tuple, set)):
            seq = list(seq)
        if isinstance(seq, list) and key >= len(seq):
            while len(seq) <= key:
                seq.append(default)
        seq[key] = value
    return seq


def getitem(seq, key, default=Exception):
    # override of list/dict getitem methods to pass a default value
    # useful to get values from list when index > length
    # also useful as a defaultdict in-place replacement
    try:
        return seq[key]
    except Exception as e:
        if default is Exception:
            raise e
        else:
            return default

def getcallable(obj, key, default=Exception, args=(), kwargs={}):
    """ This method tries to get object attribute and execute it
    """
    try:
        v = getattr(obj,key)
        if isCallable(v):
            v = v(*args,**kwargs)
        return v
    except Exception as e:
        if default is Exception:
            raise e
        else:
            return default    

########################################################################
## Regular expressions
########################################################################

re_int = r"[0-9]+"
re_float = r"[0-9]+(\.[0-9]+)?([eE][+-]?[0-9]+)?"
reint, refloat = re_int, re_float  # backwards compatibility

WILDCARDS = r"^$*+?{\|"  # r'[]()

re_alnum = r"[\w\-\*\.]+"
# alnum matching valid filenames without path, followed by "+"
re_name = r"(?:[\w\-\*\.][\w\-\*\.\+]*)"
re_no_alnum = r"[^a-zA-Z0-9-_]"
re_no_quotes = r"(?:^|$|[^\"\'])"

def matchAll(exprs, seq):
    """
    Returns strings in seq that are matched by all expression in exprs
    """
    exprs, seq = toSequence(exprs), toSequence(seq)
    if anyone(isRegexp(e) for e in exprs):
        return [s for s in seq if all(matchCl(e, s, terminate=True) for e in exprs)]
    else:
        exprs = [lowstr(e) for e in exprs]
        #return [s for s in seq if any(e in lowstr(s) for e in exprs)]  # lowstr(s)
        return [s for s in seq if all(e in lowstr(s) for e in exprs)]  # lowstr(s)


def matchAny(exprs, seq):
    """
    Returns seq if any of the expressions in exp is matched, if not it returns None
    """
    exprs = toSequence(exprs)
    for exp in exprs:
        if matchCl(exp, seq, terminate=True):
            # print '===============>   matchAny(): %s matched by %s' % (seq,exp)
            return seq
    return None


def matchMap(mapping, key, regexp=True, default=Exception):
    """from a mapping type (dict or tuples list) with strings as keys it returns the value from the matched key or raises KeyError exception"""
    if not mapping:
        if default is not Exception:
            return default
        raise ValueError("mapping")
    if hasattr(mapping, "items"):
        mapping = list(mapping.items())
    if not isSequence(mapping) or not isSequence(mapping[0]):
        raise TypeError("dict or tuplelist required")
    if not isString(key):
        key = str(key)

    for tag, value in mapping:
        if matchCl(tag, key) if regexp else (key in tag):
            return value
    if default is not Exception:
        return default
    raise KeyError(key)


def matchTuples(mapping, key, value):
    """mapping is a (regexp,[regexp]) tuple list where it is verified that value matches any from the matched key"""
    for k, regexps in mapping:
        if re.match(k, key):
            if any(re.match(e, value) for e in regexps):
                return True
            else:
                return False
    return True


def inCl(exp, seq, regexp=True):
    """
    it returns True if exp is contained by seq
    seq may be an string or a list of strings
    all comparisons are done caseless
    """
    if isString(seq):
        return (
            searchCl(exp, seq)
            if (regexp and isRegexp(exp))
            else lowstr(exp) in lowstr(seq)
        )
    elif seq is not None and len(seq):
        if not isSequence(seq):
            seq = toList(seq)
        for s in seq:
            s = str(s)
            #m = matchCl(exp, s, terminate=True) if regexp else lowstr(exp) == lowstr(s)
            m = matchCl(exp, s) if regexp else lowstr(exp) == lowstr(s)
            if m:
                return m
    else:
        return None


def matchCl(exp, seq, terminate=False, extend=False):
    """Returns a caseless match between expression and given string"""
    try:
        exp, seq = str(exp), lowstr(seq)
        if extend:
            if "&" in exp:
                return all(
                    matchCl(e.strip(), seq, terminate=False, extend=True)
                    for e in exp.split("&")
                )
            if re.match("^[!~]", exp):
                return not matchCl(exp[1:], seq, terminate, extend=True)
        return re.match(toRegexp(exp.lower(), terminate=terminate), seq)
    except:
        # print('matchCl(%s,%s,%s,%s) failed'%(exp,seq,terminate,extend))
        traceback.print_exc()
        raise


clmatch = matchCl  # For backward compatibility


def searchCl(exp, seq, terminate=False, extend=False):
    """Returns a caseless regular expression search between
    expression and given string"""
    try:
        exp, seq = str(exp), lowstr(seq)
        if extend:
            if "&" in exp:
                return all(
                    searchCl(e.strip(), seq, terminate=False, extend=True)
                    for e in exp.split("&")
                )
            if re.match("^[!~]", exp):
                return not searchCl(exp[1:], seq, terminate, extend=True)
        return re.search(toRegexp(exp.lower(), terminate=terminate), seq)
    except:
        # print('searchCl(%s,%s,%s,%s) failed'%(exp,seq,terminate,extend))
        traceback.print_exc()
        raise


clsearch = searchCl  # For backward compatibility


def replaceCl(exp, repl, seq, regexp=True, lower=False):
    """
    Replaces caseless expression exp by repl in string seq
    repl can be string or callable(matchobj) ; to reuse matchobj.group(x) if needed in the replacement string
    lower argument controls whether replaced string should be always lower case or not
    """
    if lower and hasattr(repl, "lower"):
        repl = repl.lower()
    if regexp:
        r, s = "", 1
        while s:
            s = searchCl(exp, seq)
            if s:
                sub = repl(s.group()) if isCallable(repl) else repl
                r += seq[: s.start()] + (str(sub).lower() if lower else str(sub))
                seq = seq[s.end() :]
        return r + seq
    else:
        return seq.lower().replace(exp.lower(), repl)


clsub = replaceCl


def splitCl(exp, seq, inclusive=False):
    """
    Split an string by occurences of exp
    """
    s, e = seq.lower(), exp.lower()
    matches = re.finditer(e, s)
    if not matches:
        r = [seq]
    else:
        i, r = 0, []
        for m in matches:
            l = seq[i : m.end() if inclusive else m.start()]
            if l:
                r.append(l)
            i = m.end()
        if i < len(seq):
            r.append(seq[i:])
    return r


clsplit = splitCl


def sortedRe(iterator, order):
    """Returns a list sorted using regular expressions.
    order = list of regular expressions to match ('[a-z]','[0-9].*','.*')
    """
    if ".*" not in order:
        order = list(order) + [".*"]
    rorder = [re.compile(c) for c in order]

    def sorter(k, ks=rorder):
        k = str(k[0] if isinstance(k, tuple) else k).lower()
        return str(next((i for i, r in enumerate(ks) if r.match(k)))) + k

    for i in sorted(iterator, key=sorter):
        print("%s:%s" % (i, sorter(i)))
    return sorted(iterator, key=sorter)


def toCl(exp, terminate=False, wildcards=("*", " "), lower=True):
    """
    Converts to caseless and replaces wildcards
    
    wildcards: replaces * by .* and ? by . in the given expression.
    """
    ## @PROTECTED: DO NOT MODIFY THIS METHOD, MANY, MANY APPS DEPEND ON IT
    exp = str(exp).strip()
    if lower:
        exp = exp.lower()
    if not any(s in exp for s in (".*", r"\*", "]*")):
        for w in wildcards:
            exp = exp.replace(w, ".*")
    if terminate and not exp.strip().endswith("$"):
        exp += "$"
    exp = exp.replace("(?p<", "(?P<")  # Preventing missing P<name> clausses
    return exp


def toRegexp(exp, terminate=False, lower=False, wildcards=("*",)):
    """Case sensitive version of the previous one, for backwards compatibility"""
    return toCl(exp, terminate, wildcards=wildcards, lower=lower)


def filtersmart(seq, filters, default_prefix='?',
                wildcards=("*"," "), separator='[,;]'):
    """
    filtersmart(sequence,filters=['any_filter','+all_filter','!neg_filter'])

    appies a list of filters to a sequence of strings,

    behavior of filters depends on first filter character:
        '[a-zA-Z0-9]' : individual filters, behave like AND or OR depending on default argument.

        '?' : optional matches, matching any of them is enough
        '&' or '+': required, requires all those filters to be matched
        '!' or '-' : negate, discards all matching values
        '^' : matches string since the beginning (startswith instead of contains)
        '$' : matches the end of strings
        ',' or ';': will be used as filter separator if a single string is provided

    """
    if isString(seq):
        seq = str2list(seq,separator,True)
    if isString(filters):
        filters = str2list(filters,separator,True)

    filters = [default_prefix+f if f[0] not in '&+!-?' else f
               for f in filters]

    opt = [toRegexp(f[1:],wildcards=wildcards) for f in filters if f[0] in '?']
    req = [toRegexp(f[1:],wildcards=wildcards) for f in filters if f[0] in "&+"]
    neg = [toRegexp(f[1:],wildcards=wildcards) for f in filters if f[0] in "!-"]

    req = req or ['.*']
    return [
        s
        for s in seq
        if (not any(searchCl(n, s) for n in neg))
        and (not opt or any(searchCl(o, s) for o in opt))
        and all(searchCl(r, s) for r in req)
    ]


##############################################################################

FalseStrings = ("no", "false", "", "0", "none")
NoneStrings = ("none", "null", "nan", "")
TrueStrings = ("true", "yes")
NaN = float("nan")
inf = float("inf")


def fbool(x):
    """
    Instead of just considering sequences as True, it evaluates contents
    Returns all(x) if sequence and not empty else bool(x)
    """
    if isSequence(x):
        if not len(x):
            return False
        elif isSequence(x[0]):
            return all(fbool(y) for y in x)
        return all(x)
    else:
        return bool(x)


def notNone(arg, default=None):
    """
    Returns arg if not None, else returns default.
    """
    return [arg, default][arg is None]


def isTrue(arg):
    """
    This method allows to evaluate strings and numpy arrays as booleans
    """
    if type(arg) not in (int, bool, float):
        if isSequence(arg) or isMapping(arg):
            arg = len(arg)
        elif isString(arg):
            arg = lowstr(arg) not in FalseStrings
    return bool(arg)


def isNaN(arg):
    return (
        isinstance(arg, float)
        and math.isnan(arg)
        or (isString(arg) and lowstr(arg) == "nan")
    )


def isNone(arg):
    return arg is None or (isString(arg) and lowstr(arg) in NoneStrings)


def isFalse(arg):
    # considers strings as boolean representations
    # 0/1 and none/nan are not considered as booleans
    if isSequence(arg) or isMapping(arg):
        arg = len(arg)
    return not arg or lowstr(arg) in FalseStrings


def isBool(arg, is_zero=True):
    """
    Input may be an string, but not an integer
    True/yes/false/no are considered valid boolean strings
    """
    codes = ["true", "yes", "false", "no"]
    if is_zero:
        codes += ["0", "1"]
    if arg in (True, False):
        return True
    elif isString(arg):
        # none/nan will not be considered boolean
        return lowstr(arg) in codes
    else:
        return False


##############################################################################

########################################################################
## Methods for identifying types
########################################################################
""" Note of the author:
 This methods are not intended to be universal, are just practical for general Tango application purposes.
"""


def isString(seq):
    """
    Returns True if seq type can be considered as string

    @TODO: repleace by this code:
      import types;isinstance(seq,types.StringTypes)
    """
    if isinstance(seq, (basestring,str,bytes,bytearray,unicode)):
        return True  # It matches most python str-like classes
    if any(
        s in str(type(seq)).lower()
        for s in (
            "vector",
            "array",
            "list",
        )
    ):
        return False
    if "qstring" == str(type(seq)).lower():
        return True  # It matches QString
    return False


def isRegexp(seq, wildcards=WILDCARDS):
    """This function is just a hint, use it with care."""
    return anyone(c in wildcards for c in seq)


def isNumber(seq):
    # return operator.isNumberType(seq)
    if isinstance(seq, bool):
        return False
    try:
        float(seq)
        return True
    except:
        return False

def isDate(seq, cad=""):
    try:
        seq and str2time(seq, cad=cad)
    except:
        return False
    else:
        return bool(seq)
    
def isCallable(obj):
    return callable(obj)

def isGenerator(seq):
    from types import GeneratorType
    # A generator check must be added to the rest of methods in this module!
    return isinstance(seq, GeneratorType)

def isSequence(seq, iterators=True, **kwargs):
    """
    It excludes Strings, dictionaries but includes generators
    unless iterators=False is set as argument,
    otherwise only fixed-length objects are accepted
    """
    if isinstance(seq, (list, set, tuple)):
        return True
    if isString(seq):
        return False
    if hasattr(seq, "items"):
        return False
    if iterators:
        if hasattr(seq, "__iter__"):
            return True
    elif hasattr(seq, "__len__"):
        return True
    return False


def isDictionary(seq, strict=True):
    """
    It includes dict-like and also nested lists if strict is False
    """
    if isinstance(seq, dict):
        return True
    if hasattr(seq, "items") or hasattr(seq, "iteritems"):
        return True
    if strict:
        return False
    try:
        if seq and isSequence(seq) and isSequence(seq[0]):
            # First element of tuple must be key-like
            if seq[0] and len(seq[0])==2: #seq[0] and not isIterable(seq[0][0]):
                return True
    except:
        pass
    return False


isMapping = isDictionary


def isHashable(seq):
    if not isinstance(seq, Hashable):
        return False
    elif isSequence(seq):
        return all(isHashable(s) for s in seq)
    else:
        return True


def isIterable(seq):
    """It includes dicts and listlikes but not strings"""
    return hasattr(seq, "__iter__") and not isString(seq)


def isNested(seq, strict=False):
    if not isIterable(seq) or not len(seq):
        return False
    child = seq[0] if isSequence(seq) else list(seq.values())[0]
    if not strict and isIterable(child):
        return True
    if any(all(map(f, (seq, child))) for f in (isSequence, isDictionary)):
        return True
    return False


def shape(seq):
    """
    Returns the N dimensions of a python sequence
    """
    if not isSequence(seq):
        return []
    else:
        d = [len(seq)]
    if isNested(seq):
        d.extend(shape(seq[0]))
    return d

def any2type(obj, types=None):
    import pickle
    if types in ('pickle','pck',pickle):
        try:
            pickle.dumps(obj)
            return obj
        except:
            pass
    else:
        if not types:
            types = (int,float,str,bytes)
        if isinstance(obj,tuple(types)):
            return obj
        
    # only not-type gets to here
    if isSequence(obj):
        return [any2type(a,types) for a in obj]
    elif isMapping(obj):
        return {any2type(k,types):any2type(v,types) for k,v in obj.items()}
    else:
        return str(obj)


###############################################################################


def str2int(seq):
    """It returns the first integer encountered in the string"""
    try:
        return int(re.search(reint, seq).group())
    except:
        return None


def str2float(seq, default=None):
    """It returns the first float (x.ye-z) encountered in the string"""
    try:
        return float(re.search(refloat, seq).group())
    except:
        return default


def str2bool(seq):
    """It parses true/yes/no/false/1/0 as booleans"""
    return lowstr(seq) not in ("false", "0", "none", "no")


def str2bytes(seq):
    """
    Converts an string to a list of integers
    
    @TODO!: this method may trigger issues regarding python3 bytes type!
    """
    print('DEPRECATED: fandango.functional.str2bytes(...)')
    return list(map(ord, str(seq)))


def str2type(seq, use_eval=True, sep_exp=r"[,;\ ]+"):
    """
    Tries to convert string to an standard python type.
    If use_eval is True, then it tries to evaluate as code.
    Lines separated by sep_exp will be automatically split
    """
    seq = str(seq).strip()
    # Parsing a date
    if clmatch("[P]?[0-9]+[-]", seq) and str2time(seq, throw=False) is not None:
        return seq
    # Parsing a list of elements
    m = sep_exp and (seq[0] not in "{[(") and re.search(sep_exp, seq)
    if m:
        return [str2type(s, use_eval) for s in str2list(seq, m.group())]
    # Bool
    elif isBool(seq, is_zero=False):
        return str2bool(seq)
    # Python expression
    elif use_eval:
        try:
            return eval(seq)
        except:
            return seq
    # Number
    elif isNumber(seq):
        return str2float(seq)
    # Regular string
    else:
        return seq


def doc2str(obj):
    return obj.__name__ + "\n\n" + obj.__doc__


def rtf2plain(t, e="[<][^>]*[>]"):
    t = re.sub(e, "", t)
    if re.search(e, t):
        return rtf2plain(t, e)
    else:
        return t


def html2text(txt):
    return rtf2plain(txt)


def unicode2str(obj):
    """
    Converts an unpacked unicode object (json) to
    nested python primitives (map,list,str)
    """
    if isMapping(obj, strict=True):
        n = dict(unicode2str(t) for t in list(obj.items()))
    elif isSequence(obj):
        n = list(unicode2str(t) for t in obj)
    elif isString(obj):
        n = str(obj)
    else:
        n = obj
    return n


def toList(val, default=[], check=isSequence):
    if val is None:
        return default
    else:
        hlen = hasattr(val, "__len__")
        ch = check(val)

        if hlen:  # list,string,dictionary
            if len(val) == 0:
                # To prevent exceptions due to non evaluable numpy arrays
                return default
            elif hasattr(val, "keys"):
                # dictionary
                return list(val)
            elif not ch:
                # string? iterable not sequence
                return [val]
            else:
                # already a valid sequence
                return val
        elif ch:
            # sequence with no len, generator?
            # It forces the return type to have a fixed length
            return list(val)
        else:
            # scalar?
            return [val]

toSequence = toList


def toString(val,encoding='ascii'):
    """ 
    helper to deal with Qt/py2/py3 strings
    """
    if isinstance(val,str):
        return val
    elif py3 and isinstance(val,bytes):
        return val.decode(encoding)
    elif not py3 and isinstance(val,unicode):
        return val.encode(encoding)
    elif hasattr(val, "text"): #QStrings
        try:
            return val.text()
        except:
            return val.text(0)
    return str(val) #repr() triggers mem leak!!
        
x2s = toString

def toStringList(seq):
    return list(map(toString, seq))


def str2list(s, separator="", regexp=False, sep_offset=0):
    """
    Convert a single string into a list of strings

    Arguments allow to split by regexp and to keep or not the separator character
    sep_offset = 0 : do not keep
    sep_offset = -1 : keep with posterior
    sep_offset = 1 : keep with precedent
    """
    if not regexp:
        return list(t.strip() for t in (s.split(separator) 
            if separator else s.split())
            )
    elif not sep_offset:
        return list(t.strip() for t in (re.split(separator, s) 
            if separator else re.split(r"[\ \\n]", s))
            )
    else:
        r, seps, m = [], [], 1
        while m:
            m = clsearch(separator, s)
            if m:
                r.append(s[: m.start()])
                seps.append(s[m.start() : m.end()])
                s = s[m.end() :]
        r.append(s)
        for i, p in enumerate(seps):
            if sep_offset < 0:
                r[i] += p
            else:
                r[i + 1] = p + r[i + 1]
        return r


def code2atoms(code):
    """
    Obtain individual elements of a python code
    """
    begin = r"[\[\(\{]"
    end = r"[\]\)\}]"
    # ops = '[,]'
    l0 = str2list(code, begin, 1, 1)
    l0 = list(filter(bool, list(l.strip() for l in l0)))
    l1 = [a for l in l0 for a in str2list(l, end, 1, -1)]
    l1 = list(filter(bool, list(l.strip() for l in l1)))
    # l2 = [a for l in l1 for a in str2list(l,ops,1,-1)]
    return l1


def lowstr(s, strip=True):
    """converts anything to str(s).lower().strip()"""
    s = toString(s).lower()
    return s.strip() if strip else s


def shortstr(s, max_len=144, replace={"\n": ";"}):
    """Obtain a shorter string"""
    s = str(s)
    for k, v in list(replace.items()):
        s = s.replace(k, v)
    if max_len > 0 and len(s) > max_len:
        s = s[: max_len - 4] + " ..."
    return s


def text2list(s, separator="\n"):
    """Return only non empty words of a text"""
    return list(filter(bool, str2list(s, separator)))


def str2lines(s, length=80, joiner="\n"):
    """Convert string into a multiline text of the same length"""
    return joiner.join(s[i : i + length] for i in range(0, len(s), length))


def list2lines(s, multiline="\\", joiner="\n", comment="#"):
    """
    Joins every element of the list ending in multiline character,
    if joiner, returns the result as a single string.
    if comment, it will escape the comments until the end of the line
    """
    if not isSequence(s):
        return s
    nl = []
    for l in s:
        if comment:
            l = l.split(comment)[0]
        l = l.strip()
        if nl and nl[-1].endswith(multiline):
            nl[-1] = nl[-1][:-1] + l
        else:
            nl.append(l)

    if joiner:
        nl = joiner.join(nl)
    return nl


def list2str(s, separator="\t", MAX_LENGTH=0):
    s = str(separator).join(str(t) for t in s)
    if MAX_LENGTH > 0 and separator not in ("\n", "\r"):
        s = shortstr(s, MAX_LENGTH)
    return s


def text2tuples(s, separator="\t"):
    return [str2list(t, separator) for t in text2list(s)]


def tuples2text(s, separator="\t", lineseparator="\n"):
    return list2str([list2str(t, separator) for t in s], lineseparator)


def dict2str(s, sep=":\t", linesep="\n", listsep="\n\t"):
    return linesep.join(
        sorted(
            sep.join((str(k), list2str(toList(v), listsep, 0)))
            for k, v in list(s.items())
        )
    )


def str2dict(s, ksep="", vsep=""):
    """
    convert "name'ksep'value'vsep',..." to {name:value,...}
    argument may be string or sequence of strings
    if s is a mapping type it will be returned
    """
    if isMapping(s, strict=True):
        return s

    if isString(s):
        vsep = vsep or (
            "\n" if "\n" in s else ("," if s.count(",") >= s.count(";") else ";")
        )
        s = str2list(s, vsep)

    if s:
        ksep = ksep or (":" if s[0].count(":") >= s[0].count("=") else "=")

    return dict(str2list(t, ksep) for t in s)


def obj2str(obj, sep=",", linesep="\n", MAX_LENGTH=0):
    if isMapping(obj, strict=True):
        s = dict2str(obj, sep, linesep)
    elif isSequence(obj):
        s = list2str(obj, sep)
    else:
        s = toString(obj)
    s = shortstr(s, MAX_LENGTH, replace={})
    return s


########################################################################
## Number conversion
########################################################################


def negbin(old):
    """Given a binary number as an string, it returns all bits negated"""
    return "".join(("0", "1")[x == "0"] for x in old)


def char2int(c):
    """ord(c)"""
    return ord(c)


def int2char(n):
    """unichr(n)"""
    return chr(n)

def int2hex(n):
    return hex(n)

def int2bin(n, length=16):
    bstr = bin(n)
    bstr = bstr.replace("0b", "")
    if len(bstr) < length:
        bstr = "0" * (length - len(bstr)) + bstr
    return "0b" + bstr[-length:]    

def hex2int(c):
    return int(c, 16)


def bin2unsigned(c):
    return int(c, 2)


def signedint2bin(x, N=16):
    """It converts an integer to an string with its binary representation"""
    if x >= 0:
        bStr = bin(int(x))
    else:
        bStr = bin(int(x) % 2 ** 16)
    bStr = bStr.replace("0b", "")
    if len(bStr) < N:
        bStr = "0" * (N - len(bStr)) + bStr
    return bStr[-N:]


def bin2signedint(x, N=16):
    """Converts an string with a binary number into a signed integer"""
    i = int(x, 2)
    if i >= 2 ** (N - 1):
        i = i - 2 ** N
    return i


def int2flags(dec, N=16):
    """Converts an integer to a binary represented as a boolean array"""
    result, dec = [], int(dec)
    for i in range(N):
        result.append(bool(dec % 2))
        dec = dec >> 1
    return result

def int2bool(*args,**kwargs):
    #@DEPRECATED
    print('int2bool is misleading and deprecated, use int2flags instead')
    return int2flags(*args,**kwargs)

def bool2int(seq):
    """Converts a boolean array to an unsigned integer"""
    return bin2unsigned("".join(map(str, list(map(int, reversed(seq))))))

def toNumber(f, cast = float, default = 1e-18):
    """
    defaults not-float to 1e-18 (smallest non zero)
    it equals to fandango.trial(float,args=(f,),excepts=0.0)
    """
    try: 
        return cast(f)
    except: 
        return default

toFloat = x2f = x2n = toNumber

def asBool(o, forward=True):
    """
    helper to evaluate length of sizeable objects as bool
    """
    try:
        v = bool(o)
    except:
        if isinstance(o, Sized):
            v = len(o)
            o = [] if not v else o
        else:
            v = o
    return o if forward else v

x2b = asBool



########################################################################
## Time conversion
########################################################################

END_OF_TIME = 1024 * 1024 * 1024 * 2 - 1  # Jan 19 04:14:07 2038
END_OF_TIME_64 = 4294967295 # equivalent to 2106-02-07 06:28:15
TIME_UNITS = {
    "ns": 1e-9,
    "us": 1e-6,
    "ms": 1e-3,
    "": 1,
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86.4e3,
    "w": 604.8e3,
    "M": 30 * 86.4e3,
    "y": 31.536e6,
}
TIME_UNITS.update((k.upper(), v) for k, v in list(TIME_UNITS.items()) if k != "m")

# RAW_TIME should be capable to parse durations as of ISO 8601
RAW_TIME = r"^(?:P)?([+-]?[0-9]+[.]?(?:[0-9]+)?)(?: )?(%s)$" % ("|").join(
    TIME_UNITS
)  # e.g. 3600.5 s

re_date = r"[-]".join((reint, reint, reint))
rehour = r"%s[:]%s" % (reint, reint) + "(?:[:]%s)?" % refloat
re_date += r"(?:[ T]%s)?" % rehour  # as of ISO 8601
redate = re_date  # backwards compatibility

MYSQL_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
ISO_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"

global DEFAULT_TIME_FORMAT
DEFAULT_TIME_FORMAT = MYSQL_TIME_FORMAT

ALT_TIME_FORMATS = [
    ("%s%s%s" % (date.replace("-", dash), separator if hour else "", hour))
    for date in ("%Y-%m-%d", "%y-%m-%d", "%d-%m-%Y", "%d-%m-%y", "%m-%d-%Y", "%m-%d-%y")
    for dash in ("-", "/")
    for separator in (" ", "T", "_")
    for hour in ("%H:%M", "%H:%M:%S", "%H:%M:%S.%f", "%H", "")
]


def set_default_time_format(dtf, test=True):
    """
    Usages:

        fandango.set_default_time_format('%Y-%m-%d %H:%M:%S')

        or

        fandango.set_default_time_format(fandango.ISO_TIME_FORMAT)

    """
    if test:
        str2time(time2str(cad=dtf), cad=dtf)
    global DEFAULT_TIME_FORMAT
    DEFAULT_TIME_FORMAT = dtf


def now():
    return time.time()


def time2tuple(epoch=None, utc=False):
    if epoch is None:
        epoch = now()
    elif epoch < 0:
        epoch = now() - epoch
    if utc:
        return time.gmtime(epoch)
    else:
        return time.localtime(epoch)


def tuple2time(tup):
    """
    WARNING!!! as this method is based on localtime, it takes daylight save
    into account, so it is INVALID to convert gmt/utc times!
    """
    return time.mktime(tup)


def date2time(date, us=True):
    """
    This method would accept both timetuple and timedelta
    in order to deal with times coming from different
    api's with a single method
    """
    try:
        t = int(tuple2time(date.timetuple()))
        us = us and getattr(date, "microsecond", 0)
        if us:
            t = float(t) + us * 1e-6
        return t
    except Exception as e:
        try:
            return date.total_seconds()
        except:
            raise e


def date2str(date, cad="", us=False):
    # return time.ctime(date2time(date))
    global DEFAULT_TIME_FORMAT
    cad = cad or DEFAULT_TIME_FORMAT
    t = time.strftime(cad, time2tuple(date2time(date)))
    us = us and getattr(date, "microsecond", 0)
    if us:
        t += ".%06d" % us
    return t


def time2date(epoch=None):
    if epoch is None:
        epoch = now()
    elif epoch < 0:
        epoch = now() - epoch
    return datetime.datetime.fromtimestamp(epoch)


def utcdiff(t=None):
    return now() - date2time(datetime.datetime.utcnow())


def time2str(epoch=None, cad="", us=False, bt=True, utc=False, iso=False):
    """
    cad: introduce your own custom format (see below)
    use DEFAULT_TIME_FORMAT to set a default one
    us=False; True to introduce ms precission
    bt=True; negative epochs are considered relative from now
    utc=False; if True it converts to UTC
    iso=False; if True, 'T' will be used to separate date and time

    cad accepts the following formats (amongs others):
        (see https://strftime.org/
        https://docs.python.org/3/library/datetime.html#format-codes)

    %a 	Locale’s abbreviated weekday name.
    %A 	Locale’s full weekday name.
    %b 	Locale’s abbreviated month name.
    %B 	Locale’s full month name.
    %c 	Locale’s appropriate date and time representation.
    %d 	Day of the month as a decimal number [01,31].
    %H 	Hour (24-hour clock) as a decimal number [00,23].
    %I 	Hour (12-hour clock) as a decimal number [01,12].
    %j 	Day of the year as a decimal number [001,366].
    %m 	Month as a decimal number [01,12].
    %M 	Minute as a decimal number [00,59].
    %p 	Locale’s equivalent of either AM or PM. 	(1)
    %S 	Second as a decimal number [00,61]. 	(2)
    %U 	Week number of the year (Sunday as the first day of the week) as a decimal number [00,53].
    All days in a new year preceding the first Sunday are considered to be in week 0. 	(3)
    %w 	Weekday as a decimal number [0(Sunday),6].
    %W 	Week number of the year (Monday as the first day of the week) as a decimal number [00,53].
    All days in a new year preceding the first Monday are considered to be in week 0. 	(3)
    %x 	Locale’s appropriate date representation.
    %X 	Locale’s appropriate time representation.
    %y 	Year without century as a decimal number [00,99].
    %Y 	Year with century as a decimal number.
    %Z 	Time zone name (no characters if no time zone exists).
    %% 	A literal '%' character.
    """
    global DEFAULT_TIME_FORMAT

    if epoch is None:
        epoch = now()
    elif not isinstance(epoch,(int,float)):
        raise Exception('WrongTimeType')
    elif bt and epoch < 0:
        epoch = now() + epoch
    if cad:
        cad = "T".join(cad.split(" ", 1)) if iso else cad
    else:
        cad = ISO_TIME_FORMAT if iso else DEFAULT_TIME_FORMAT

    t = time.strftime(cad, time2tuple(epoch, utc=utc))
    if us:
        # parsing microseconds resolution
        v = '.%06d'%(1e6 * (epoch % 1))
        if isinstance(us,int):
            v = v[:-(6-us)]
        t += v

    return t

epoch2str = time2str


def str2time(seq="", cad="", throw=True, relative=False):
    """
    :param seq: Date must be in ((Y-m-d|d/m/Y) (H:M[:S]?)) format or -N [d/m/y/s/h]

    See RAW_TIME and TIME_UNITS to see the units used for pattern matching.

    The conversion itself is done by time.strptime method.

    :param cad: You can pass a custom time format
    :param relative: negative times will be converted to now()-time
    :param throw: if False, None is returned instead of exception
    """
    try:
        ms = 0
        if seq in (None, ""):
            return time.time()
        if "NOW-" in seq:
            seq, relative = seq.replace("NOW", ""), True
        elif seq == "NOW":
            return now()

        t, seq = None, str(seq).strip()
        if not cad:
            m = re.match(RAW_TIME, seq)
            if m:
                # Converting from a time(unit) format
                value, unit = m.groups()
                t = float(value) * TIME_UNITS[unit]
                return t  # must return here

        # Converting from a date format
        if "." in seq:
            ms = re.match(r".*(\.[0-9]+)$", seq)  # Splitting the decimal part
            if ms:
                ms, seq = float(ms.groups()[0]), seq.replace(ms.groups()[0], "")
        elif seq.count(":") > 2:
            seq, ms = seq.rsplit(":", 1)
            ms = 1e-3 * float(ms)
            print((seq, ms))
        else:
            ms = 0

        if t is None:
            # tf=None will try default system format
            global DEFAULT_TIME_FORMAT
            time_fmts = [cad] if cad else [DEFAULT_TIME_FORMAT, None] + ALT_TIME_FORMATS
            for tf in time_fmts:
                try:
                    tf = (tf,) if tf else ()
                    t = time.strptime(seq, *tf)
                    break
                except:
                    pass

        v = time.mktime(t) + (ms or 0)
        if relative and v < 0:
            v = now() - v
        if v % 1 < 1e-6:
            v = int(v)
        return v
    except:
        if throw:
            raise Exception("PARAMS_ERROR", "unknown time format: %s" % seq)
        else:
            return None


str2epoch = str2time


def time2utc(epoch=None):
    if epoch is None:
        epoch = now()
    # return tuple2time(time.gmtime(epoch))
    d = datetime.datetime.utcfromtimestamp(epoch)
    return date2time(d)


time2gmt = time2utc


def timezone():
    t = now()
    return old_div(int(t - time2gmt(t)), 3600)


# Auxiliary methods:
def ctime2time(time_struct):
    try:
        t = int(time_struct.tv_sec)
        if time_struct.tv_usec:
            t += 1e-6 * float(time_struct.tv_usec)
        return t
    except:
        return -1
    
def ctime2str(time_struct):
    return time2str(ctime2time(time_struct))


def mysql2time(mysql_time, us=True):
    try:
        return date2time(mysql_time, us=us)
        # t = time.mktime(mysql_time.timetuple())
    except:
        return -1


########################################################################
## Extended eval
########################################################################


def iif(condition, truepart, falsepart=None, forward=False):
    """
    if condition is boolean return (falsepart,truepart)[condition]
    if condition is callable returns truepart if condition(tp) else falsepart
    if forward is True condition(truepart) is returned instead of truepart
    if forward is callable, forward(truepart) is returned instead
    
    so:
    iif(isNumber, self.forced, self.DefaultPolling, float)
    equals to:
    float(self.forced) if isNumber(self.forced) else self.DefaultPolling
    """
    if isCallable(condition):
        v = condition(truepart)
        if not v:
            return falsepart
    elif not condition:
        return falsepart

    if isCallable(forward):
        return forward(truepart)
    elif forward:
        return v
    else:
        return truepart


def ifThen(condition, callback, falsables=tuple()):
    """
    This function allows to execute a callable on an object only if it
    has a valid value. ifThen(value,callable) will return callable(value)
    only if value is not in falsables.

    It is a List-like method, it can be combined with fandango.excepts.trial
    """
    if condition not in falsables:
        if not isSequence(callback):
            return callback(condition)
        else:
            return ifThen(callback[0](condition), callback[1:], falsables)
    else:
        return condition


# def call(args=None, kwargs=None, _locals=None, debug=False, map_types=True):
def call(*args, **kwargs):
    """
    Calls a method from local scope parsing a pipe-like argument list:
       a b=2 c='test'

    arguments like str=str will be converted to keyword arguments

    an argument like pickle=filename will export the result to a file
    
    keyword arguments:
      _locals
      debug = False
      map_types = True
    """
    if not args:
        import sys
        args = sys.argv[1:] or ['help']
        
    if args:
        main = args[0]
        args = args[1:]

    if 'kwargs' in kwargs: #backwards compat
        kw = kwargs.pop('kwargs') or {}
        kwargs.update(kw)
    _locals = kwargs.get('_locals', 
        kwargs.get('locals_', None) or {} #backwards compat
        )
    debug =  kwargs.get(' debug', False)
    map_types = kwargs.get('map_types', True)
    export = kwargs.get('export', None)

    # args = map(str.strip,args)
    if not main:
        main, args = args[0], args[1:]

    if all(isString(a) for a in args):
        #print('parsing options from %s' % str(args))
        opts = [a for a in args if a.startswith('-')] #"=" in a]
        args = [str2type(a) for a in args if a not in opts]
        opts = {t[0].lstrip('-'):t[-1] for t in [k.split('=',1) for k in opts]}
        if map_types:
            opts = {k:str2type(v) for k,v in opts.items()}
        kwargs.update(opts)
    export = kwargs.pop("pickle", "")

    print('fandango.call(%s,%s,%s,%s)' % (main, args, kwargs, main in _locals))

    if not isCallable(main):
        _locals = _locals or globals()
        from fandango.objects import getCode

        if main in ("help",'--help','-?') and 'help' not in _locals:
            if args and args[0] in _locals:
                n, o = args[0], _locals[args[0]]
                # if hasattr(o,'func_code'):
                # n = n+str(o.func_code.co_varnames)
                n = getCode(o).header
                return "%s:\n%s" % (n, o.__doc__)
            else:
                lines = []
                _locals["__doc__"] and lines.append(_locals["__doc__"])
                lines.append("\nAvailable functions in '%s':\n" % sys.argv[0])
                lines.append(
                    "\n\n".join(
                        sorted(
                            "\t" + getCode(v).header + '\n\t\t' + str(v.__doc__ or '')
                            for v in filter(isCallable, list(_locals.values()))
                        )
                    )
                )
                lines.append("")
                return "\n".join(map(str,lines))
                # m = [k for k,v in _locals.items() if isCallable(v)]
                # return ('\n'.join(sorted(m,key=lowstr)))

        main = _locals.get(main, None)

    if debug:
        print("%s(* %s,** %s)" % (main, args, kwargs))

    r = main(*args, **kwargs)
    if export:
        import pickle

        pickle.dump(r, open(export, "w"))
        return export

    return r


def retry(callable, retries=3, pause=0, args=[], kwargs={}):
    r = None
    for i in range(retries):
        try:
            r = callable(*args, **kwargs)
            break
        except Exception as e:
            if i == (retries - 1):
                raise e
            elif pause:
                time.sleep(pause)
    return r


def retried(retries=3, pause=0):
    """
    @decorator
    Returns a function decorator to execute any method in retried mode
    """

    def retrier(f):
        def retried_f(*args, **kwargs):
            return retry(f, retries=retries, pause=pause, args=args, kwargs=kwargs)

        return retried_f

    return retrier


def evalF(formula):
    """
    Returns a compiled function that executes the formula passed as argument.
    The formula should use x,y,z as predefined arguments, or use args[..] array instead

    e.g.:
    map(evalF("x>2"),range(5)) : [False, False, False, True, True]

    It is optimized to be efficient (but still 50% slower than a pure lambda)
    """
    # return (lambda *args: eval(formula,locals={'args':args,'x':args[0],'y':args[1],'z':args[2]}))
    # returning a lambda that evals a compiled code makes the method 500% faster
    c = compile(formula, formula, "eval")
    return lambda *args: eval(
        c,
        {
            "args": args,
            "x": args and args[0],
            "y": len(args) > 1 and args[1],
            "z": len(args) > 2 and args[2],
        },
    )


def testF(f, args=[], t=5.0):
    """
    it returns how many times f(*args) can be executed in t seconds
    """
    args = toSequence(args)
    ct, t0 = 0, time.time()
    while time.time() < t0 + t:
        f(*args)
        ct += 1
    return ct


def evalX(
    target,
    _locals=None,
    modules=None,
    instances=None,
    _trace=False,
    _exception=Exception,
):
    """
    evalX is an enhanced eval function capable of evaluating multiple types
    and import modules if needed.

    The _locals/modules/instances dictionaries WILL BE UPDATED with the result
    of the code! (if '=' or import are used)

    It is used by some fandango classes to send python code to remote threads;
    that will evaluate and return the values as pickle objects.

    target may be:
         - dictionary of built-in types (pickable):
                {'__target__':callable or method_name,
                '__args__':[],'__class_':'',
                '__module':'','__class_args__':[]}
         - string to eval: eval('import $MODULE' or '$VAR=code()' or 'code()')
         - list if list[0] is callable: value = list[0](*list[1:])
         - callable: value = callable()
    """

    # Only if immutable types are passed as arguments these dictionaries will
    # be preserved.
    _locals = notNone(_locals, {})
    modules = notNone(modules, {})
    instances = notNone(instances, {})

    def import_module(module, reload=False):
        # This method is re-implemented in objects module for avoiding
        # inter-dependency between modules
        module = module.strip()
        alias = module.split(" as ", 1)[-1] if " as " in module else module
        module = module.split("import ", 1)[-1].split()[0]
        if reload or alias not in modules:
            from fandango.objects import find_module, load_module
            # if "." not in module:
            #     modules[module] = imp.load_module(module, *imp.find_module(module))
            # else:
            #     parent, child = module.rsplit(".", 1)
            #     mparent = import_module(parent)
            #     setattr(
            #         mparent,
            #         child,
            #         imp.load_module(module, *imp.find_module(child, mparent.__path__)),
            #     )
            #     modules[module] = getattr(mparent, child)
            modules[module] = load_module(module)
            if alias:
                modules[alias] = modules[module]
                _locals[alias] = modules[alias]
        if _trace:
            print("evalX:%s(%s) : %s" % (alias, module, modules[alias]))

        return modules[module]

    def get_instance(_module, _klass, _klass_args):
        if (_module, _klass, _klass_args) not in instances:
            instances[(_module, _klass, _klass_args)] = getattr(
                import_module(_module), klass
            )(*klass_args)
        return instances[(_module, _klass, _klass_args)]

    if "import_module" not in _locals:
        _locals["import_module"] = lambda m: import_module(m, reload=True)

    if isDictionary(target):
        model = target
        keywords = [
            "__args__",
            "__target__",
            "__class__",
            "__module__",
            "__class_args__",
        ]
        args = (
            model["__args__"]
            if "__args__" in model
            else dict((k, v) for k, v in list(model.items()) if k not in keywords)
        )
        target = model.get("__target__", None)
        module = model.get("__module__", None)
        klass = model.get("__class__", None)
        klass_args = model.get("__class_args__", tuple())

        if isCallable(target):
            target = model["__target__"]

        elif isString(target):
            if module:
                # module,subs = module.split('.',1)
                if klass:
                    if _trace:
                        print(
                            "evalX: %s.%s(%s).%s(%s)"
                            % (module, klass, klass_args, target, args)
                        )
                    target = getattr(get_instance(module, klass, klass_args), target)
                else:
                    if _trace:
                        print("evalX: %s.%s(%s)" % (module, target, args))
                    target = getattr(import_module(module), target)


            elif klass and klass in dir(builtins):
                if _trace:
                    print("evalX: %s(%s).%s(%s)" % (klass, klass_args, target, args))
                instance = getattr(builtins, klass)(*klass_args)
                target = getattr(instance, target)

            elif target in dir(builtins):
                if _trace:
                    print("evalX: %s(%s)" % (target, args))
                target = getattr(builtins, target)

            else:
                raise _exception("%s()_MethodNotFound" % target)
        else:
            raise _exception("%s()_NotCallable" % target)

        value = target(**args) if isDictionary(args) else target(*args)
        if _trace:
            print("%s: %s" % (model, value))

        return value
    else:
        # Parse: method[0](*method[1:])
        if isIterable(target) and isCallable(target[0]):
            value = target[0](*target[1:])

        # Parse: method()
        elif isCallable(target):
            value = target()

        elif isString(target):
            if _trace:
                print('evalX("%s")' % target)

            # Parse: import $MODULE
            if target.startswith("import ") or " import " in target:
                # Modules dictionary is updated here
                value = import_module(target)
                # value = target

            # Parse: $VAR = #code
            elif (
                "=" in target
                and "=" != target.split("=", 1)[1][0]
                and re.match(
                    r"[A-Za-z\._]+[A-Za-z0-9\._]*$", target.split("=", 1)[0].strip()
                )
            ):
                if _trace:
                    print('evalX: eval(%s)' % target)
                var = target.split("=", 1)[0].strip()
                formula = target.split("=", 1)[1].strip()
                _locals[var] = eval(formula, modules, _locals)
                value = var
            # Parse: #code
            else:
                if _trace:
                    print('evalX: locals[{}]: {}'.format(
                        len(_locals), list(_locals.keys())))
                    atoms = code2atoms(target)
                    print('evalX: atoms: {}'.format(atoms))
                    print('evalX: missing: {}'.format(list(a for a in atoms if a not in _locals)))
                    print('evalX: eval(%s)' % target)

                value = eval(target, modules, _locals)
        else:
            raise _exception(
                "targetMustBeCallable, not %s(%s)" % (type(target), target)
            )

        if _trace:
            print("Out of evalX(%s): %s" % (target, value))
    return value

###############################################################################
# Python 2to3 wrappers/helpers
try:
    from .futurize import raw_input
    raw_input = raw_input
except:
    def raw_input(*args, **kwargs):
        return input(*args, **kwargs)

###############################################################################

try:
    from . import doc

    __doc__ = doc.get_fn_autodoc(__name__, vars(), module_vars=["END_OF_TIME"])
except:
    pass

if __name__ == "__main__":
    print(call())
