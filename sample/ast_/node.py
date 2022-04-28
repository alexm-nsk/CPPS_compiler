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
    built_ins = {
                    "size" : dict (in_ports = [ArrayType(IntegerType())], out_ports = [IntegerType()])
                }

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        Function.functions[self.function_name] = self

    def emit_json(self, parent_node, slot = 0, current_scope = None):
            return export_function_to_json(self, parent_node, slot, current_scope)

    def emit_graphml(self, parent_node):
            return export_function_to_graphml(self, parent_node)


class FunctionImport(Node):

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        Function.functions[self.function_name] = self

    def emit_json(self, parent_node, slot = 0, current_scope = None):
            return export_functionimport_to_json(self, parent_node, slot, current_scope)

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


class Loop(Node):

    def __init__(self, *args, **kwargs):
       super().__init__(**kwargs, no_id = False)
       # sub_nodes will have their own IDs so we calculate them
       for sub in ["range", "init", "returns", "while"]:
            if sub in self.__dict__:
                self.__dict__[sub + "_id"] = Node.get_node_id()
       #self.init_id = Node.get_node_id()
       #self.test_id = Node.get_node_id()
       #self.body_id = Node.get_node_id()
       #self.ret_id  = Node.get_node_id()


class Scatter(Node):
    
    pass


class Init(Node):
    
    pass
    

class Let(Node):

    def __init__(self, *args, **kwargs):
       super().__init__(**kwargs, no_id = False)
       # sub_nodes will have their own IDs so we calculate them
       self.init_id = Node.get_node_id()
       self.body_id = Node.get_node_id()


class Algebraic(Node):

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs, no_id = True)


class Identifier(Node):

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs, no_id = True)


class Literal(Node):

    pass


class Statement(Node):

    pass


class Assignment(Statement):

    def __init__(self, *args, **kwargs):
       super().__init__(**kwargs, no_id = True)

    pass


# ~ class Returns(Node):
    # ~ pass


class OldValue(Node):
    def __init__(self, *args, **kwargs):
       super().__init__(**kwargs, no_id = False)

    pass


class ArrayAccess(Node):
    pass


class Bin(Node):
    pass


class Call(Node):
    pass


class Reduction(Node):
    pass


class BuiltInCall(Node):
    pass

class Equation(Node):
    pass

# ~ class Sum(Reduction):
    # ~ pass


# ~ class ArrayOf(Reduction):
    # ~ pass
    


# ~ class Value(Reduction):
    # ~ def __init__(self, *args, **kwargs):
       # ~ super().__init__(**kwargs, no_id = False)
       # ~ # this is a placeholder for now
       # ~ self.true_literal = Literal(value = True, type = BooleanType(), location = "not applicable")
