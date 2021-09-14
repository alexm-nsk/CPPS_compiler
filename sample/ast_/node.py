#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  node.py
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


from exporters.json    import *
from exporters.graphml import *
from exporters.cpp import *
from exporters.llvm import *


class Node:

    nodes = {}
    node_counter = 0

    def get_node_id():

        Node.node_counter += 1
        return "node" + str(Node.node_counter)

    def __init__(self, *args, **kwargs):

        if not ( "no_id" in kwargs and kwargs["no_id"]):
            self.node_id = Node.get_node_id()
            Node.nodes[self.node_id] = self

        if "no_id" in kwargs: kwargs.pop("no_id")

        # TODO consider list of allowed props (https://stackoverflow.com/questions/8187082/how-can-you-set-class-attributes-from-variable-arguments-kwargs-in-python)
        self.__dict__.update(kwargs)

    def emit_llvm(self, scope = None):
        if not getattr(type(self),"__emit_llvm__", None):
            class_name = self.__class__.__name__
            type(self).__emit_llvm__ = globals() [ "export_" + class_name.lower() + "_to_llvm"];
        return type(self).__emit_llvm__(self, scope)

    def emit_json(self, parent_node, slot, current_scope):
        if not getattr(type(self),"__emit_json__", None):
            class_name = self.__class__.__name__
            type(self).__emit_json__ = globals() [ "export_" + class_name.lower() + "_to_json"];
        return type(self).__emit_json__(self, parent_node, slot, current_scope)

    def emit_cpp(self):
        pass

    def __repr__(self):
        return (str(self.__dict__))

    def __str__(self):
        return (str(self.__dict__))


class Function(Node):

    #static field storing name - function node pairs
    functions = {}

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        Function.functions[self.function_name] = self

    def emit_json(self, parent_node, slot = 0, current_scope = None):
            return export_function_to_json(self, parent_node,slot, current_scope)

    def emit_graphml(self, parent_node):
            return export_function_to_graphml(self, parent_node)


class If(Node):

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        
        # give the conditions and branches ids:
        
        for n, elseif in enumerate(self.elseif_nodes):
            self.elseif_nodes[n] = dict(id = Node.get_node_id(), nodes = elseif)
        
        self.conditions = dict(id = Node.get_node_id(), nodes = self.conditions)
        self.then_nodes = dict(id = Node.get_node_id(), nodes = self.then_nodes)
        self.else_nodes = dict(id = Node.get_node_id(), nodes = self.else_nodes)
        

class Algebraic(Node):

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs, no_id = True)


class Identifier(Node):

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs, no_id = True)


class Literal(Node):

    pass
    
class OldValue(Node):
    
    # ~ def __init__(self, *args, **kwargs):
        # ~ super().__init__(**kwargs)
        # ~ print (self.emit_json(0,0,0))
         
    pass

class ArrayAccess(Node):

    pass


class Bin(Node):

    pass


class Call(Node):

    pass
