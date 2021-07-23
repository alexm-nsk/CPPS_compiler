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

class IntegerType:

    def __init__(self, location = "not applicable"):
        self.location = location

    def emit_json(self):
        return dict(location = self.location , name = "integer")

class RealType:

    def __init__(self, location = "not applicable"):
        self.location = location

    def emit_json(self):
        return dict(location = self.location , name = "real")

class ArrayType:

    def __init__(self, element_type, location = "not applicable"):
        self.element_type = element_type
        self.location = location

    def emit_json(self):
        return dict(location = self.location , element = self.element_type.emit_json())

# ~ class CustomType:

    # ~ def __init__(self, location):
        # ~ self.location = location

    # ~ def emit_json():
        # ~ return dict(location = self.location)
        
#-------------------------------------------------------------------------------------------

# ~ class TypeDescription:
    # ~ def __init__(self, location, type_):
        # ~ pass

    # ~ def emit_json():
        # ~ return {
                    # ~ "location" : self.location,
                    # ~ type_.name : type.emit_json()
                # ~ }

#-------------------------------------------------------------------------------------------

class SisalType:

    def __init__(self, node_id, type_descriprion, index):

        self.node_id          = node_id
        self.type_description = type_descriprion
        self.index            = index


    def emit_json(self):

        return dict(
                        nodeId = "node" + str(self.node_id),
                        type   = self.type_description.emit_json(),
                        index  = self.index,
                    )

#-------------------------------------------------------------------------------------------

if __name__ == "__main__":
    #code for trying things out, won't run when this module is imported
    import json
    arr = SisalType(1,
                    ArrayType(IntegerType("loc"), "loc")
                    ,1)
    integer = SisalType(1, IntegerType("loc"),1)
    print (json.dumps(integer.emit_json(),indent = 2))
    print (json.dumps(arr.emit_json(), indent = 2))
