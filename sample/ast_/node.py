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

    def emit_obj(self):
        pass

    def emit_json(self):
        pass

    def emit_cpp(self):
        pass

    def emit_llvm(self):
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

    def emit_json(self, parent_node, slot = 0):
            return export_function_to_json(self, parent_node)

    def emit_graphml(self, parent_node):
            return export_function_to_graphml(self, parent_node)

class Bin(Node):

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

    def emit_json(self, parent_node, slot = 0):
        return (export_bin_to_json(self, parent_node, slot))


class Call(Node):

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

    def emit_json(self, parent_node, slot = 0):
        return export_call_to_json(self, parent_node, slot)


class If(Node):

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        for cond in self.condition:
            cond.node_id  = Node.get_node_id()

        for name, branch in self.branches.items():
            branch["node_id"]  = Node.get_node_id()
            for br in branch:
                pass

        self.name = "if_"

    def emit_json(self, parent_node, slot = 0):
        return (export_if_to_json(self, parent_node, slot))


class Algebraic(Node):

    def __init__(self, *args, **kwargs):

        super().__init__(**kwargs, no_id = True)

        self.name = "algebraic"

    def emit_json(self, parent_node, slot = 0):
        return (export_algebraic_to_json(self, parent_node, slot))


class Identifier(Node):

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs, no_id = True)

    def emit_json(self, parent_node, slot = 0):
        return (export_identifier_to_json(self, parent_node, slot))


class Literal(Node):

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

    def emit_json(self, parent_node, slot = 0):
        return (export_literal_to_json(self, parent_node, slot))

class ArrayAccess(Node):

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

    def emit_json(self, parent_node, slot = 0):
        return (export_array_access_to_json(self, parent_node, slot))
