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

COMPILER = "C++"

if "COMPILER" in globals():

    if   COMPILER == "LLVM":
        from compiler.llvm import *

    elif COMPILER == "C++":
        from compiler.cpp import *

else:
    raise Exception ("Compiler not specified!")

import re

BRANCH_NAMES = ["Else", "ElseIf", "Then"]


def get_type(type_object):
    return Type(
                    location = type_object["location"],
                    descr     = type_object["name"]
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

    return CLASS_MAP[name](node)
    #TODO delete these after testing:

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

    elif name == "LoopExpression":
        return LoopExpression(node)

    elif name == "Init":
        return Init(node)

    elif name == "PreCondition":
        return PreCondition(node)

    elif name == "Body":
        return Body(node)

    elif name == "Returns":
        return Returns(node)

    elif name in BRANCH_NAMES:
        return Branch(node)

    elif name == "OldValue":
        return OldValue(node)

    elif name == "Reduction":
        return Reduction(node)



def parse_nodes(nodes):

    return [ parse_node(node) for node in nodes ]


def replace_operators(op):
    return op.replace("&lt", "<").replace("&le", "<=").replace("&gt", ">").replace("&ge", ">=")


def parse_json_fields(self, node):

    if ("name" in node ):         self.name          = node["name"]
    if ("location" in node ):     self.location      = node["location"]
    if ("id" in node ):           self.id            = node["id"]
    if ("functionName" in node ): self.function_name = node["functionName"]
    if ("operator" in node ):     self.operator      = replace_operators(node["operator"])
    if ("callee" in node ):       self.callee        = node["callee"]
    if ("value" in node ):        self.value         = node["value"]

    if ("edges" in node ):        self.edges         = get_edges(node["edges"])
    if ("inPorts" in node ):      self.in_ports      = get_ports(node["inPorts"] )
    if ("outPorts" in node ):     self.out_ports     = get_ports(node["outPorts"])
    if ("params" in node ):       self.params        = get_params(node["params"])

    if ("condition" in node ):    self.condition     = parse_node (node["condition"])
    if ("branches" in node ):     self.branches      = parse_nodes(node["branches"])
    if ("nodes" in node ):        self.nodes         = parse_nodes(node["nodes"])


    # Loop:

    if ("results" in node ):      self.results       = get_params(node["results"])

    for name in ["init", "preCondition", "body", "reduction"]:
        # will replace names like "preCondition" with names like "pre_condition"
        # to adhere to typical Python naming scheme:
        conv_name = re.sub("([A-Z])", lambda m: "_" + m.group(0).lower(), name)
        #
        if (name in node ): self.__dict__[conv_name] = parse_node(node[name])


class Type:

    def __init__(self, location, descr):
        self.location = location
        self.descr     = descr
        #print ("type created")

    def __repr__(self):
        return str(self.__dict__)

    def emit_llvm(self):
        type_map = {
            "integer" : ir.IntType(SYSTEM_BIT_DEPTH)
        }
        # TODO derive type from it's description
        return type_map[self.descr]

    def emit_cpp(self):
        type_map = {
            "integer" : IntegerType(32)
        }
        # TODO derive type from it's description
        return type_map[self.descr]

    def __str__(self):
        return self.descr


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

    def has_nodes(self):
        return "nodes" in self.__dict__

    # returns a list of pairs of nodes containing the result of all internal calculations
    # and edges that carry that final value:
    def get_result_nodes(self):
        return [( Node.nodes_[edge.from_], edge )
            for edge in Edge.edges_to[self.id] if Node.is_parent(edge.from_, self.id)]

    # TODO check if this is needed
    def get_parameter_nodes(self):
        return [( Node.nodes_[edge.from_], edge )
            for edge in Edge.edges_to[self.id] if Node.nodes_[edge.from_].has_nodes() and Node.is_parent(self.id, edge.from_)]

    # get all the pairs of nodes that output values to this node and corresponding edges
    def get_input_nodes(self):
        return [ (Node.nodes_[edge.from_], edge)
            for edge in Edge.edges_to[self.id]]

    def get_input_edges_simple(self):
        return  [(edge.from_, edge.to) for edge in Edge.edges_to[self.id]]

    def get_input_edges(self):
        return  Edge.edges_to[self.id]

    def is_node_parent(self, node_id):
        if not "nodes" in Node.nodes_[node_id].__dict__:
            return False

        for n in Node.nodes_[node_id].nodes:
            if n.id == self.id:
                return True
        return False

    @staticmethod
    def is_parent(node1, node2):
        for n in Node.nodes_[node2].nodes:
            if n.id == node1:
                return True
        return False

    def emit_llvm(self, scope = None):
        if scope == None and type(self) != Function:
            raise Exception(f"No scope provided for{self.name} when emitting llvm-code")

        class_name = self.__class__.__name__
        func_name = "export_" + class_name.lower() + "_to_llvm"
        if func_name in globals():
            return globals() [ func_name ](self, scope)
        else:
            raise Exception (f'compiling {class_name} not implemented')

    def emit_cpp(self, cpp_scope = None):
        if cpp_scope == None and type(self) != Function:
            raise Exception(f"No scope provided for{self.name} when emitting llvm-code")

        class_name = self.__class__.__name__
        func_name = "export_" + class_name.lower() + "_to_cpp"
        if func_name in globals():
            return globals() [ func_name ](self, cpp_scope)
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


# --------------------------------------
# Loops:

class LoopExpression(Node):
    pass


class Init(Node):
    pass

class PreCondition(Node):
    pass


class Body(Node):
    pass


class Returns(Node):
    pass


class OldValue(Node):
    pass


class Reduction(Node):
    pass


# --------------------------------------


class ArrayAccess(Node):
    pass


CLASS_MAP = {
    "Lambda" : Function,
    "If":If,
    "Else": Branch,
    "ElseIf": Branch,
    "Then": Branch,
    "Condition":Condition,
    "Binary":Binary,
    "FunctionCall":FunctionCall,
    "Literal":Literal,
    "LoopExpression":LoopExpression,
    "Init":Init,
    "PreCondition":PreCondition,
    "Body":Body,
    "Returns": Returns,
    "OldValue": OldValue,
    "Reduction": Reduction,
    "ArrayAccess": ArrayAccess,
}
