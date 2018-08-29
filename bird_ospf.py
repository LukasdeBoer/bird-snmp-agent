#!/usr/bin/python
#
# Copyright (c) 2016 Travelping GmbH <copyright@travelping.com>
# by Tobias Hintze <tobias.hintze@travelping.com>
#
# This code is inspired and partially copied from 
# https://r3blog.nl/index.php/archives/2011/02/24/bgp4-mib-support-for-bird/
# That original code does not clearly declare any license.
# 
# This code also uses python-agentx library licensed under GPLv3
# (see agentx.py for details)
#
# So this code is licensed under the GPLv3 (see COPYING.GPLv3).
#

from __future__ import print_function
from adv_agentx import AgentX
from adv_agentx import SnmpGauge32, SnmpCounter32, SnmpIpAddress
import time, os
import functools

from birdagent import BirdAgent

## handle get and getnext requests
def OnSnmpRead(req, ax, axd):
    pass

# handle set requests
def OnSnmpWrite(req, ax, axd):
    pass

# handle get, getnext and set requests
def OnSnmpRequest(req, ax, axd):
    pass

## initialize any ax and axd dependant code here
def OnInit(ax, axd):
    pass

## register some variables
## this function is called when a new snmp request has been received and
## if CacheInterval has expired at that time
def OnUpdate(ax, axd, ospf_state):
    print('updated bird-ospf state: {0}'.format(time.time()))    
    
    # general info (router id etc)
    axd.RegisterVar('ospfGeneralGroup', 0)
    axd.RegisterVar("ospfRouterId.0", ospf_state["general_info"]["router_id"])
    axd.RegisterVar("ospfAdminStat.0", ospf_state["general_info"]["admin_state"])
    axd.RegisterVar("ospfVersionNumber.0", 2)    

    # register ospf areas
    axd.RegisterVar("ospfAreaEntry", 0)
    for area in ospf_state["areas"]:
        axd.RegisterVar("ospfAreaId.%s.0"%area["area_id"], SnmpIpAddress(area["area_id"]))
    
    # register ospf interfaces
    axd.RegisterVar("ospfIfEntry", 0)
    for interface in ospf_state["interfaces"]:
        axd.RegisterVar("ospfIfIpAddress.%s.0"%interface["ipaddress"], SnmpIpAddress(interface["ipaddress"]))
    for interface in ospf_state["interfaces"]:
        axd.RegisterVar("ospfIfAreaId.%s.0"%interface["ipaddress"], interface["area"])
    for interface in ospf_state["interfaces"]:
        axd.RegisterVar("ospfIfState.%s.0"%interface["ipaddress"], interface["state"])
    
    # register ospf neighbors
    axd.RegisterVar("ospfNbrEntry", 0)
    for nbrid, nbr in ospf_state['neighbors']:
        axd.RegisterVar("ospfNbrIpAddr.%s.0"%nbrid, SnmpIpAddress(nbr["rtrip"]))
    for nbrid, nbr in ospf_state['neighbors']:
        axd.RegisterVar("ospfNbrRtrId.%s.0"%nbrid, SnmpIpAddress(nbrid))
    for nbrid, nbr in ospf_state['neighbors']:
        axd.RegisterVar("ospfNbrPriority.%s.0"%nbrid, nbr["pri"])
    for nbrid, nbr in ospf_state['neighbors']:
        axd.RegisterVar("ospfNbrState.%s.0"%nbrid, nbr["state"])

    return

# main program
if __name__ == '__main__':
    print('bird-ospf AgentX starting')

    bird = BirdAgent(
            os.environ.get("BIRDCONF") or "/etc/bird/bird.conf",
            os.environ.get("BIRDCPATH") or "/usr/sbin/birdc",
            os.environ.get("SSCMD") or "ss -tan -o state established '( dport = :bgp or sport = :bgp )'")

    instance = os.environ.get("OSPF_INSTANCE") or "ospf1"

    callbacks = {
            "OnSnmpRead"    : OnSnmpRead,
            "OnSnmpWrite"   : OnSnmpWrite,
            "OnSnmpRequest" : OnSnmpRequest,
            "OnInit"        : OnInit,
            "OnUpdate"      : lambda ax, axd: OnUpdate(ax, axd, bird.getOSPFState(instance))
    }

    ## initialize agentx module and run main loop
    AgentX(
        callbacks,
        Name          = 'bird-ospf',
        MIBFile       = os.environ.get("OSPFMIBFILE") or "/usr/local/bird-snmp-agent/mibs/OSPF-MIB.txt",
        RootOID       = 'OSPF-MIB::ospf',
        CacheInterval = int(os.environ.get("AGENTCACHEINTERVAL") or "30")
    )
    
    #OnUpdate(None, None, bird.getOSPFState(instance))

    print('bird-ospf AgentX terminating')

# vim:ts=4:sw=4:noexpandtab