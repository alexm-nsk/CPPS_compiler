#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  nodes.py
#
#  Copyright 2021 alexm
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#


from compiler.json_parser import *


class Type:
    
    def __init__(self, location, name):
        self.location = location
        self.name     = name

    def __repr__(self):
        return str(self.__dict__)


def get_type(type_object):
    
    return Type(
                    location = type_object["location"],
                    name     = type_object["name"]
                )


def get_ports(ports):

    return [
            dict(
                 node_id = p["nodeId"],
                 type    = get_type(p["type"])
                )
                for p in ports
            ]


def get_edges(edges):

    for e in edges:
        from_, to = e
        #return Edge(from_["nodeId"], to["nodeId"]


def get_params(params):

    ret_params = {}
    for p in params:
        name, data = p
        ret_params[name] = dict(
                                type  = get_type(data["type"]),
                                index = data["index"]
                                )

    return ret_params


def parse_node(node):
    
    name = node["name"]
    if name == "Lambda":
        return Function(node)
    elif name == "If":
        return If(node)


class Edge:

    edges = []

    def __init__(self, from_, to, from_type, to_type):
        self.from_     = from_
        self.to        = to
        self.from_type = from_type
        self.to_type   = to_type


class Port:

    def __init__(self, port_data):
        pass


class Node:
    nodes = {}
    def __init__(self, node):
        Node.nodes[node["id"]] = self
    
    def __repr__(self):
        return str(self.__dict__)
    

class If(Node):

    def __init__(self, node):
        super().__init__(node)
        self.in_ports  = get_ports(node["inPorts"] )
        self.out_ports = get_ports(node["outPorts"])
        self.name      = node["name"]
        self.location  = node["location"]
        self.id        = node["id"]
        self.edges     = get_edges(node["edges"])
        self.params    = get_params(node["params"])
        self.nodes     = [ parse_node(n) for n in node["nodes"] ]

    
class Function(Node):

    def __init__(self, node):
        super().__init__(node)
        self.in_ports      = get_ports(node["inPorts"] )
        self.out_ports     = get_ports(node["outPorts"])
        self.function_name = node["functionName"]
        self.name          = node["name"]
        self.location      = node["location"]
        self.id            = node["id"]
        self.edges         = get_edges(node["edges"])
        self.params        = get_params(node["params"])
        self.nodes         = [ parse_node(n) for n in node["nodes"] ]
