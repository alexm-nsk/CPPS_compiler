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
from compiler.llvm import *


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
    ret_edges = []
    for e in edges:
        from_, to = e
        ret_edges.append( Edge(from_["nodeId"],            to["nodeId"],
                      get_type ( from_["type"] ), get_type ( to["type"] ),
                      from_["index"],             to["index"]) )
    return ret_edges


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
    if ("functionName" in node ): self.function_name = node["functionName"]
    if ("operator" in node ):     self.operator      = node["operator"]
    if ("callee" in node ):       self.callee        = node["callee"]
    if ("value" in node ):        self.value         = node["value"]
    
    if ("edges" in node ):        self.edges         = get_edges(node["edges"])
    if ("inPorts" in node ):      self.in_ports      = get_ports(node["inPorts"] )
    if ("outPorts" in node ):     self.out_ports     = get_ports(node["outPorts"])
    if ("params" in node ):       self.params        = get_params(node["params"])
    
    if ("condition" in node ):    self.condition     = parse_node (node["condition"])
    if ("branches" in node ):     self.branches      = parse_nodes(node["branches"])
    if ("nodes" in node ):        self.nodes         = parse_nodes(node["nodes"])


class Type:

    def __init__(self, location, name):
        self.location = location
        self.name     = name

    def __repr__(self):
        return str(self.__dict__)

    def emit_llvm(self):
        # TODO derive type from it's description
        return ir.IntType(32)


class Edge:

    edges = []
    edges_from = {}
    edges_to   = {}

    def __init__(self, from_, to, from_type, to_type, from_index, to_index):

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

    nodes_ = {}

    def __init__(self, node):
        Node.nodes_[node["id"]] = self
        parse_json_fields (self, node)

    def __repr__(self):
        return str(self.__dict__)

    def get_result_nodes(self):
        return [( edge.from_, edge )
            for edge in Edge.edges_to[self.id] if Node.is_parent(edge.from_, self.id)]
    
    def get_input_nodes(self):
        return [ (Node.nodes_[edge.from_], edge)
            for edge in Edge.edges_to[self.id]]
            
    def get_input_edges_simple(self):        
        return  [(edge.from_, edge.to) for edge in Edge.edges_to[self.id]]

    def get_input_edges(self):        
        return  Edge.edges_to[self.id]
            
    @staticmethod
    def is_parent(node1, node2):
        for n in Node.nodes_[node2].nodes:
            if n.id == node1:
                return True
        return False
        
    def emit_llvm(self, scope = None):                
        class_name = self.__class__.__name__
        func_name = "export_" + class_name.lower() + "_to_llvm"
        if func_name in globals():
            return globals() [ func_name ](self, scope)
        else:
            raise Exception (f'compiling {class_name} not implemented')


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
