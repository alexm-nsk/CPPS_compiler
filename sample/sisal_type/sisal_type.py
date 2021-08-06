#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  sisal_type.py
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

from llvmlite import ir, binding

built_in_types = ["integer", "real"]

    # ~ {
          # ~ "nodeId": "node1",
          # ~ "type": {
            # ~ "location": "1:26-1:30",
            # ~ "name": "real"
          # ~ },
          # ~ "index": 0
        # ~ }



         # ~ {
            # ~ "nodeId": "node1",
            # ~ "type": {
              # ~ "location": "1:17-1:31",
              # ~ "element": {
                # ~ "location": "1:26-1:30",
                # ~ "name": "real"
              # ~ }
            # ~ },
            # ~ "index": 0
          # ~ }

#-------------------------------------------------------------------------------------------
class BaseType:
    pass

class NumberType(BaseType):
    pass
    
class IntegerType(NumberType):

    def __init__(self, location = "not applicable"):
        self.location = location

    def emit_json(self):
        return dict(location = self.location , name = "integer")
    
    def emit_llvm(self):
        return ir.IntType(32)
        
class VoidType(BaseType):

    def __init__(self, location = "not applicable"):
        self.location = location

    def emit_json(self):
        return dict(location = self.location , name = "void")
    
    def emit_llvm(self):
        return ir.VoidType()

class RealType(NumberType):

    def __init__(self, location = "not applicable"):
        self.location = location

    def emit_json(self):
        return dict(location = self.location , name = "real")

class BooleanType(NumberType):

    def __init__(self, location = "not applicable"):
        self.location = location

    def emit_json(self):
        return dict(location = self.location , name = "boolean")

class ArrayType(BaseType):

    def __init__(self, element_type, location = "not applicable"):
        self.element_type = element_type
        self.location = location

    def emit_json(self):
        return dict(location = self.location , element = self.element_type.emit_json())

class CustomType:

    def __init__(self, location):
        self.location = location

    def emit_json():
        return dict(location = self.location)

#-------------------------------------------------------------------------------------------

def emit_type_object(node_id, type_description, index, location = None):

    type_   = type_description.emit_json()
    
    if location: type_["location"] = location
    
    return dict(
                    nodeId = str(node_id),
                    type   = type_,
                    index  = index,
                )

#-------------------------------------------------------------------------------------------

if __name__ == "__main__":
    #code for trying things out, won't run when this module is imported
    import json
    arr = emit_type_object(1,
                    ArrayType(IntegerType("loc"), "loc")
                    ,1)
    integer = emit_type_object(1, IntegerType("loc"),1)
    print (json.dumps(integer,indent = 2))
    print (json.dumps(arr, indent = 2))
    print (issubclass(ArrayType, NumberType))
