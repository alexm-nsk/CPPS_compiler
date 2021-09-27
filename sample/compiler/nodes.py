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


BRANCH_NAMES = ["Else", "ElseIf", "Then"]


def get_type(type_object):

    return Type(
                    location = type_object["location"],
                    name     = type_object["name"]
                )


def get_ports(ports):

    return [
                Port(
                 node_id = p["nodeId"],
                 type    = get_type(p["type"]),
                 index   = p["index"]
                )
                for p in ports
            ]


def get_edges(edges):

    for e in edges:
        from_, to = e
        return Edge(from_["nodeId"],            to["nodeId"],
                    get_type ( from_["type"] ), get_type ( to["type"] ),
                    from_["index"],             to["index"])


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

    elif name == "Condition":
        return Condition(node)

    elif name == "Binary":
        return Binary(node)

    elif name == "FunctionCall":
        return FunctionCall(node)

    elif name == "Literal":
        return Literal(node)

    elif name in BRANCH_NAMES:
        return Branch(node)


def parse_nodes(nodes):

    return [ parse_node(node) for node in nodes ]


def parse_json_fields(self, node):

    if ("name" in node ):         self.name          = node["name"]
    if ("location" in node ):     self.location      = node["location"]
    if ("id" in node ):           self.id            = node["id"]
    if ("nodes" in node ):        self.nodes         = parse_nodes(node["nodes"])
    if ("edges" in node ):        self.edges         = get_edges(node["edges"])
    if ("inPorts" in node ):      self.in_ports      = get_ports(node["inPorts"] )
    if ("outPorts" in node ):     self.out_ports     = get_ports(node["outPorts"])
    if ("params" in node ):       self.params        = get_params(node["params"])
    if ("condition" in node ):    self.condition     = parse_node (node["condition"])
    if ("branches" in node ):     self.branches      = parse_nodes(node["branches"])
    if ("functionName" in node ): self.function_name = node["functionName"]
    if ("operator" in node ):     self.operator      = node["operator"]
    if ("callee" in node ):       self.callee        = node["callee"]
    if ("value" in node ):        self.value         = node["value"]


class Type:

    def __init__(self, location, name):
        self.location = location
        self.name     = name

    def __repr__(self):
        return str(self.__dict__)


class Edge:

    edges = []
    edges_from = {}
    edges_to   = {}

    def __init__(self, from_, to, from_type, to_type, from_index, to_index):
        
        print ("edge found!")
        self.from_      = from_
        self.to         = to
        self.from_type  = from_type
        self.to_type    = to_type
        self.from_index = from_index
        self.to_index   = to_index

        Edge.edges.append(self)
        if not from_ in Edge.edges_from: Edge.edges_from[from_] = []
        if not to    in Edge.edges_to  : Edge.edges_to  [to   ] = []
        Edge.edges_from[from_].append(self)
        Edge.edges_to  [to   ].append(self)

    def __repr__(self):
        return str(self.__dict__)


class Port:

    def __init__(self, node_id, type, index):
        self.node_id = node_id
        self.type    = type
        self.index   = index

    def __repr__(self):
        return str(self.__dict__)

class Node:

    nodes = {}

    def __init__(self, node):
        Node.nodes[node["id"]] = self
        parse_json_fields (self, node)

    def __repr__(self):
        return str(self.__dict__)


class Condition(Node):
    pass


class Branch(Node):
    pass


class If(Node):
    pass


class Function(Node):
    pass


class Binary(Node):
    pass


class FunctionCall(Node):
    pass
    
class Literal(Node):
    pass
