#!/usr/bin/env python

#############################################################################
##
## project :     Tango Control System
##
## $Author: Sergi Rubio Manrique, srubio@cells.es $
##
## $Revision: 2008 $
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
###########################################################################

"""
provides tango utilities for fandango, like database search methods and 
emulated Attribute Event/Value types

This module is a light-weight set of utilities for PyTango.
Classes dedicated for device management will go to fandango.device
Methods for Astor-like management will go to fandango.servers

.. contents::

.

"""

import time, re, os, traceback, threading

# pytango imports

import tango
import tango as PyTango
from tango import (
    AttrQuality,
    AttReqType,   
    AttributeProxy,
    AttrDataFormat,
    AttrWriteType,
    CmdArgType,    
    Database,
    DevError,    
    DevFailed,
    DevState,
    DeviceProxy,    
    EventType,
    TimeVal,
    LatestDeviceImpl,    
)

try:
    from tango.utils import EventCallBack
except:
    pass

#WARNING: DROPPED COMPATIBILITY WITH TANGO8
#if "LatestDeviceImpl" not in dir(PyTango):
#    try:
#        PyTango.LatestDeviceImpl = PyTango.Device_5Impl
#    except:
#        PyTango.LatestDeviceImpl = PyTango.Device_4Impl

import fandango
import fandango as fn
from fandango.functional import *

from fandango.dicts import CaselessDefaultDict, CaselessDict, Enumeration
from fandango.objects import Object, Struct, Cached
from fandango.linos import get_fqdn
from fandango.log import Logger, except2str, printf
from fandango.excepts import exc2str

global TANGO_DEBUG
TANGO_DEBUG = os.getenv("TANGO_DEBUG")

# taurus imports, here USE_TAU is defined for all fandango
global TAU, USE_TAU, TAU_LOGGER
TAU, USE_TAU = None, False


def loadTaurus():
    print("%s fandango.tango.loadTaurus()" % time.ctime())
    global TAU, USE_TAU, TAU_LOGGER
    try:
        if str(os.getenv("USE_TAU")).strip().lower() in "yes,true,1":
            import taurus

            TAU = taurus
            USE_TAU = True
            TAU_LOGGER = taurus.core.util.Logger
            """USE_TAU will be used to choose between taurus.Device 
            and PyTango.DeviceProxy"""
            print("fandango.tango: USE_TAU=True, using Taurus for proxies")
    except:
        print("fandango.tango: USE_TAU disabled")
        TAU = None
        USE_TAU = False
        TAU_LOGGER = Logger
    return bool(TAU)


global USE_FQDN
# Using FQDN hostname to avoid notifd issues
# MUST BE TRUE TO DEAL WITH NETWORK ISSUES IN TANGO9/TANGO7 MIXED SYSTEMS
USE_FQDN = str2type(os.getenv("USE_FQDN", "True"))  #'None'

TANGO_STATES = (
    "ON OFF CLOSE OPEN INSERT EXTRACT MOVING STANDBY FAULT INIT RUNNING ALARM "
    "DISABLE UNKNOWN".split()
)
TANGO_COLORS = (
    "Lime White White Lime White Lime LightBlue Yellow Red Brown LightBlue"
    " Orange Magenta Grey".split()
)

TANGO_STATE_COLORS = dict(list(zip(TANGO_STATES, TANGO_COLORS)))

ATTR_ALARM = AttrQuality.ATTR_ALARM
ATTR_WARNING = AttrQuality.ATTR_WARNING
ATTR_VALID = AttrQuality.ATTR_VALID
ATTR_INVALID = AttrQuality.ATTR_INVALID

# Regular Expressions
metachars = re.compile(r"([.][*])|([.][^*])|([$^+\-?{}\[\]|()])")

# alnum must match alphanumeric strings, including "-_.*"
alnum, no_alnum, no_quotes = re_alnum, re_no_alnum, re_no_quotes

# rehost matches simple and fqdn hostnames
#rehost = (
    #"(?:(?P<host>"
    #+ alnum
    #+ "(?:\."
    #+ alnum
    #+ ")?"
    #+ "(?:\."
    #+ alnum
    #+ ")?"
    #+ "(?:\."
    #+ alnum
    #+ ")?"
    #+ "[\:][0-9]+)(?:/))"
#)  # (?:'+alnum+':[0-9]+/)?

rehost_short = (
    r"(?P<host>" + alnum
    + r"(?:\." + alnum + ")?"
    + r"(?:\." + alnum + ")?"
    + r"(?:\." + alnum + ")?"
    + r"[\:][0-9]+)"
)  # (?:'+alnum+':[0-9]+/)?

rehost = r'(?:{}(?:/))'.format(rehost_short)

# redev matches device names
redev = r"(?P<device>" + "(?:" + "/".join([alnum] * 3) + "))"

# reattr matches attribute and extension
rewhat = r"(?:(?:\\.)(?P<what>quality|time|value|exception|history))"  # |\[[0-9+]\]))'
reattr = r"(?:/(?P<attribute>" + alnum + ")" + rewhat + "?)"

# retango matches the whole expression
retango = r"(?:tango://)?" + (rehost + r"?") + redev + (reattr + r"?") + r"(?:\$?)"

AC_PARAMS = [
    "color",
    "display_unit",
    #'writable',
    "standard_unit",
    "quality",
    "unit",
    "string",
    "label",
    "min_alarm",
    "events",
    "description",
    #'data_type',
    "format",
    "max_alarm",
    #'device',
    #'name',
    #'database',
    #'data_format',
    #'value',
    #'polling',
    #'time',
    "alarms",
    #'model',
    # ALARMS
    "delta_t",
    "max_alarm",
    "min_warning",
    #'extensions',
    "delta_val",
    "min_alarm",
    "max_warning",
    # EVENTS
    #'extensions',
    "period",
    "archive_period",
    #'extensions',
    "archive_rel_change",
    "archive_abs_change",
    "rel_change",
    #'extensions',
    "abs_change",
    "per_event",
    "ch_event",
    "arch_event",
]


###############################################################################
##@name Access Tango Devices and Database

##TangoDatabase singletone
global TangoDatabase, TangoDevice, TangoProxies
TangoDatabase, TangoDevice, TangoProxies = None, None, None
# TangoProxies to be redefined at the end of file

global KEEP_PROXIES
KEEP_PROXIES = False


def get_full_name(model, fqdn=None):
    """
    Returns full schema name as needed by HDB++ api
    """
    model = str(model).split("tango://")[-1].lower().strip()

    if fqdn is None:
        fqdn = fandango.tango.defaults.USE_FQDN

    if ":" in model:
        h, m = model.split(":", 1)
        if "." in h and not fqdn:
            h = h.split(".")[0]
        elif "." not in h and fqdn:
            try:
                h = get_fqdn(h)
            except:
                #traceback.print_exc()
                pass
        #print('get_full_name1(%s) => %s' % (model,h + ":" + m))
        model = h + ":" + m

    else:
        #nm = get_tango_host(fqdn=fqdn) + "/" + model
        #print('get_full_name2(%s) => %s' % (model,nm))
        model = get_tango_host(fqdn=fqdn) + "/" + model

    model = "tango://" + model
    return model.lower()


def get_fqdn_name(model):
    return get_full_name(model, fqdn=True)


def get_normal_name(model):
    """
    returns simple name as just domain/family/member,
    without schema/host/port, as needed by TangoDB API
    """
    model = str(model).lower().strip() if model else ''
    if ":" in model:
        model = model.split(":")[-1].split("/", 1)[-1]
    return model.split("#")[0].strip("/")


get_simple_name = get_normal_name


def get_attr_name(model, default="state"):
    """
    gets just the attribute part of a Tango URI

    set default=False to do a boolean check whether URI belongs to attribute
    """
    if not model:
        return ""
    model = get_normal_name(model)
    if model.count("/") == 3:
        return model.split("/")[-1]
    else:
        return default


get_attribute_name = get_attr_name


def get_dev_name(model, full=True, fqdn=None):
    """
    gets just the device part of a Tango URI
    """
    norm = get_normal_name(model)
    if norm.count("/") > 2:
        model = model.strip().rsplit("/", 1)[0]
    if not full:
        return get_normal_name(model)
    else:
        return get_full_name(model, fqdn=fqdn)


get_device_name = get_dev_name

class TangoNamesDict(fn.dicts.CustomDict):
    
    #def get_key(self,key):
        #if key in self.keys():
            #return key
        #else:
            #for k in self.keys():
                #k,key = k.lower(),key.lower()
                #if (k == key or
                    #get_normal_name(k) == get_normal_name(key) or
                    #get_full_name(k,fqdn=False) == get_full_name(key,fqdn=False) or
                    #get_full_name(k,fqdn=True) == key) == get_full_name(key,fqdn=True)
                    #)
                    #return k
        #return None
    
    customkey = staticmethod(get_fqdn_name)
    
    
    def customdict(self, key):
        return get_full_name(key,fqdn=True)

    def __init__(self,other=None):
        self._normal_keys = fn.dicts.CaselessDict
        self._nofqdn_keys = fn.dicts.CaselessDict
        CustomDict.__init__(self,other)

    def __getitem__(self, key):
        return defaultdict_fromkey.__getitem__(self, self.customkey(key))
    
    def __setitem__(self, key):
        
        CustomDict.__setitem__(self,key,value)
        
    def __getitem__(self, key):
        return super(CustomDict,self).__getitem__(self.customkey(key))
    
    def get(self, key, def_val = None):
        # this is NOT equivalent to __getitem__
        return super(CustomDict,self).get(self.customkey(key), def_val)
    
    getitem = get
    
        

@Cached(depth=100, expire=60)
def get_tango_host(dev_name="", use_db=False, fqdn=None):
    """
    If device is a tango model, it will extract the host from the model URL
    If devices is none, then environment variable or PyTango.Database are used
    to extract the host
    If use_db is True, then it will get the host from Db before environment
    If false, it tries TANGO_HOST environment first and then the Db.
    """
    if fqdn is None:
        global USE_FQDN
        fqdn = USE_FQDN

    try:
        if dev_name:

            if isString(dev_name):
                dev_name = str(dev_name).replace("tango://", "")
                m = matchCl(rehost, dev_name)
            else:
                m, use_db = None, dev_name

            if not m:
                return get_tango_host(use_db=use_db, fqdn=fqdn)
            else:
                host, port = m.groups()[0].split(":")

        else:
            tango_host = os.getenv("TANGO_HOST")
            if use_db or not tango_host:
                use_db = (use_db if hasattr(use_db, "get_db_host") 
                    else get_database(use_env=bool(tango_host)))
                host, port = use_db.get_db_host(), int(use_db.get_db_port())
            else:
                host, port = tango_host.split(":", 1)

        if fqdn:
            try:
                if host.count(".") < 2:
                    host = get_fqdn(host)
            except:
                traceback.print_exc()
                pass

        elif (matchCl(".*[a-z].*", host)): #Wtf?
            # Remove domain name
            host = host.strip().split(".")[0]

        #if '.' not in host:
            #print('get_tango_host(%s,%s,%s)' % (dev_name, use_db, fqdn))
            #print('>'*80 + ' WTF? ' + host)
        return "%s:%d" % (host, int(port))

    except:
        print("ERROR: get_tango_host(): " + traceback.format_exc())
        return "localhost:10000"


def set_tango_host(tango_host):
    """Sets TANGO_HOST environment variable, cleans up caches"""

    global TangoDatabase, TangoDevice, TangoProxies
    TangoDatabase, TangoDevice, TangoProxies = None, None, None
    TangoProxies = ProxiesDict()
    import fandango.tango

    for k in dir(fandango.tango):
        f = getattr(fandango.tango, k)
        if hasattr(f, "cache"):
            try:
                f.cache.clear()
            except:
                pass
    os.environ["TANGO_HOST"] = tango_host
    return tango_host


@Cached(depth=10, expire=60)
def get_database(host="", port="", use_env=True):
    """
    Method to get a singleton instance of the Tango Database
    host/port can be a host,port tuple; a 'host:port' string or a taurus model.
    @TODO: host/port is checked only at first creation, once initialized
    you can't change HOST
    """
    global TangoDatabase
    if host in (True, False):
        # For backwards compatibility
        host, port = host, "", ""

    elif host:
        if "/" in host:
            # Parsing a taurus model
            host = get_tango_host(host)
        if ":" in host:
            # Parsing a host:port string
            host, port = host.split(":")

    elif use_env: 
        # Don't call get_tango_host here to avoid recursive calls
        # TANGO_HOST env will take precedence over /etc/tangorc
        host = os.getenv("TANGO_HOST") or ":"
        host, port = host.split(":", 1)

    args = [host, int(port)] if host and port else []
    try:
        db = Database(*args)
        if not args:
            TangoDatabase = db
        return db
    except:
        print(traceback.format_exc())
    return


def get_proxy(argin, keep=False):
    """
    Returns attribute or device proxy depending on argin syntax
    """
    if argin.count("/") > (2 + (":" in argin)):
        return AttributeProxy(argin)
    else:
        return get_device(argin, keep)


def get_device(dev, keep=None, proxy=None, trace=False):
    try:
        r, cached = None, False
        if keep is None:
            global KEEP_PROXIES
            keep = KEEP_PROXIES

        if isString(dev):
            if dev.count("/") == 1:
                dev = "dserver/" + dev
            m = clmatch(retango, dev)
            if m and m.groupdict()["attribute"]:
                dev = dev.strip().rsplit("/", 1)[0]

            # To ensure keep working
            # Using get_dev_name instead of full_name to remove attr names
            dev = get_dev_name(dev, full=True, fqdn=True).lower()

            global TangoProxies
            if TangoProxies is None:
                TangoProxies = ProxiesDict()

            # Key names managed by ProxiesDict
            cached = dev in TangoProxies
            if cached or keep:
                if proxy:  # and dev not in TangoProxies:
                    TangoProxies[dev] = proxy
                if not cached and TANGO_DEBUG:
                    print(">>>> get_device(%s): TangoProxies.new()" % dev)
                r = TangoProxies[dev]
            else:
                if TANGO_DEBUG:
                    print(">>>> get_device(%s): creating new proxy" % dev)
                r = DeviceProxy(dev)

        elif isinstance(dev, DeviceProxy):
            r = dev
        else:
            r = None

        if trace and not cached:
            h = time2str()
            h += " %s" % trace if isString(trace) else ""
            print("%s %s(%s,keep=%s,cached=%s)" % (h, type(r), dev, keep, cached))

        return r

    except Exception as e:
        if trace:
            print("get_device(%s,keep=%s,cached=%s)" % (dev, keep, cached))
            traceback.print_exc()
        raise e


def get_device_cached(dev):
    return get_device(dev, keep=True)


def get_database_device(db=None):
    global TangoDevice
    td = TangoDevice
    # print('get_database_device(%s,db=%s)'%(td,db))
    if db is None and td is not None:
        return td
    else:
        try:
            dev_name = (db or get_database()).dev_name()
            if db:
                #dev_name = get_tango_host(use_db=db) + "/" + dev_name if db else dev_name
                 dev_name = get_full_name(dev_name,fqdn=True)
            td = get_device(dev_name)
        except:
            print("get_database_device(%s,db=%s)" % (dev_name, db))
            traceback.print_exc()
        if db is None:
            TangoDevice = td
    return td


###############################################################################
## A useful fake attribute value and event class


class fakeAttributeValue(object):
    """
    This type simulates a modifiable AttributeValue object
        (not available in PyTango)
    It is the type used to read values from Dev4Tango devices
        (valves, pseudos, composer, etc ...)
    It also has a read(cache) method to be used as a TaurusAttribute
        or AttributeProxy (but it returns self if cache is not used)
    The cache is controlled by keeptime variable (milliseconds)
    :param parent: Apart of common Attribute arguments,
        parent will be used to keep a proxy to the parent object (a DeviceProxy or DeviceImpl)
    """

    def __init__(
        self,
        name,
        value=None,
        time_=0.0,
        quality=AttrQuality.ATTR_VALID,
        dim_x=1,
        dim_y=1,
        parent=None,
        device="",
        error=False,
        keeptime=0,
    ):
        if TANGO_DEBUG:
            print("new fakeAttributeValue(%s)" % name)
        self.full_name = name
        self.name = name.strip().rsplit("/", 1)[-1]
        self.device = (
            device or (name.strip().rsplit("/", 1)[0]) if "/" in name else (parent or "")
        )
        self.set_value(value, dim_x, dim_y)
        self.set_date(time_ or time.time())
        self.write_value = self.wvalue = None
        self.quality = quality
        self.parent = parent
        self.error = self.err = error
        self.keeptime = keeptime * 1e3 if keeptime < 10.0 else keeptime
        self.lastread = 0
        self.type = type(value)

    def __repr__(self):
        return "fakeAttributeValue(%s,%s,%s,%s,error=%s)" % (
            self.name,
            fandango.log.shortstr(self.value),
            time.ctime(self.get_time()),
            self.quality,
            self.error,
        )

    __str__ = __repr__

    def get_name(self):
        return self.name

    def get_full_name(self):
        return self.full_name

    def get_device(self):
        return self.device

    def get_value(self):
        return self.value

    def get_date(self):
        return self.time

    def get_time(self):
        return self.time.totime()

    def get_quality(self):
        return self.quality

    def read(self, cache=True):
        if TANGO_DEBUG:
            print("fakeAttributeValue.read(%s,%s)" % (self.name, self.parent))
        # Method to emulate AttributeProxy returning an AttributeValue
        if not self.parent:
            self.parent = get_device(self.device, keep=True)
        if not cache or 0 < self.keeptime < (time.time() - self.lastread):
            # it's important to pass self as argument so values will be kept
            import fandango.tango.methods as fmt
            return fmt.read_internal_attribute(self.parent, self)
        return self

    def throw_exception(self, msg=""):
        self.err = self.error = msg or traceback.format_exc()
        # print("fakeAttributeValue(%s).throw_exception(%s)" % (self.name, self.error))
        # event_type = fakeEventType.lookup['Error']
        self.set_value(None)
        self.set_quality(AttrQuality.ATTR_INVALID)
        raise Exception(self.error)

    def set_value(self, value, dim_x=1, dim_y=1, err=False):
        self.value = self.rvalue = value
        self.err = err or isinstance(self.value, (DevFailed, DevError))

        if (dim_x, dim_y) == (1, 1):
            if isSequence(value):
                dim_x = len(value)
                if len(value) > 1 and isSequence(value[0]):
                    dim_y = len(value[0])

        self.dim_x = dim_x
        self.dim_y = dim_y
        self.set_date(time.time())
        self.lastread = time.time()

    def set_date(self, timestamp):
        if not isinstance(timestamp, TimeVal):
            timestamp = TimeVal(timestamp)
        self.time = timestamp

    def set_quality(self, quality):
        self.quality = quality

    def set_value_date(self, value, date):
        self.set_value(value)
        self.set_date(date)

    def set_value_date_quality(self, value, date, quality):
        self.set_value_date(value, date)
        self.set_quality(quality)

    def set_write_value(self, value):
        self.write_value = self.wvalue = value

    def get_write_value(self, data=None):
        if data is None:
            data = []
        if isSequence(self.write_value):
            [data.append(v) for v in self.write_value]
        else:
            data.append(self.write_value)
        return data


fakeEventType = Enumeration("fakeEventType", ("Change", "Config", "Periodic", "Error"))


class fakeEvent(object):
    def __init__(self, device, attr_name, attr_value, err, errors):
        self.device = device
        self.attr_name = attr_name
        self.attr_value = attr_value
        self.err = err
        self.errors = errors


class EventCallback(object):
    def __init__(self, device, hook=None):
        self.proxy = get_device(device)
        self.eid = None
        self.hook = None

    def subscribe(
        self,
        attribute="State",
        event_type=EventType.CHANGE_EVENT,
        filters=[],
        stateless=False,
    ):
        self.eid = self.proxy.subscribe_event(
            attribute, event_type, self, filters, stateless
        )
        return self

    def push_event(self, *args, **kwargs):
        # Reimplement this method in subclasses
        try:
            if self.hook is not None:
                return self.hook(self, *args, **kwargs)
        except:
            print("EventCallback.hook(%s) failed!" % (self.hook))
            traceback.print_exc()


###############################################################################
## The ProxiesDict class, to manage DeviceProxy pools


class ProxiesDict(CaselessDefaultDict, Object):
    """
    Dictionary that stores PyTango.DeviceProxies/AttributeProxies

    It is like a normal dictionary but creates a new proxy each time
        that the "get" method is called

    All keys translated to full tango URIs (fqdn=True by default)

    An earlier version is used in PyTangoArchiving.utils module

    Taurus3+ support is not tested
    """

    def __init__(self, tango_host=""):
        self.log = Logger("ProxiesDict")
        self.log.setLogLevel("INFO")
        self.tango_host = tango_host
        self.call__init__(CaselessDefaultDict, self.__default_factory__)

    def translate(self, dev):
        try:
            attr = get_attr_name(dev, False)
            if self.tango_host and ":" not in dev:
                dev = self.tango_host + "/" + dev
            dev = get_dev_name(dev, full=True, fqdn=True).lower()
        except:
            dev = get_dev_name(dev, full=True, fqdn=False).lower()
        if attr:
            dev += "/" + attr
        return dev

    def __default_factory__(self, dev_name):
        """
        Called by defaultdict_fromkey.__missing__ method
        If a key doesn't exists this method is called and
        returns a proxy for a given device.
        If the proxy caused an exception (usually because device
        doesn't exists) a None value is returned
        """

        dev_name = self.translate(dev_name)

        if dev_name not in list(self.keys()):
            self.log.debug("Getting a Proxy for %s" % dev_name)

            try:
                devklass, attrklass = (DeviceProxy, AttributeProxy)
                klass = (devklass, attrklass)[get_attr_name(dev_name, False)]
                dev = klass(dev_name)

            except Exception as e:
                print("ProxiesDict: %s doesnt exist!" % dev_name)
                dev = None
        return dev

    def __setitem__(self, key, value):
        key = self.translate(key)
        return CaselessDefaultDict.__setitem__(self, key, value)

    def __getitem__(self, key):
        key = self.translate(key)
        return CaselessDefaultDict.__getitem__(self, key)

    def get(self, dev_name):
        return self[dev_name]

    def get_admin(self, dev_name):
        """Adds to the dictionary the admin device for a given device name
        and returns a proxy to it."""
        dev = self[dev_name]
        class_ = dev.info().dev_class
        admin = dev.info().server_id
        return self["dserver/" + admin]

    def pop(self, dev_name):
        """Removes a device from the dict"""
        dev_name = self.translate(dev_name)
        if dev_name not in list(self.keys()):
            return
        self.log.debug("Deleting the Proxy for %s" % dev_name)
        return CaselessDefaultDict.pop(self, dev_name)


# DO NOT CHANGE THIS LINE!, NEEDED HERE FOR PERSISTANCE
TangoProxies = ProxiesDict()

