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


class IntegerType:
    def __init__(self, location):
        pass
        
    def emit_json():
        return dict(location = self.location , name = "integer")

class RealType:
    def __init__(self, location):
        pass
        
    def emit_json():
        return dict(location = self.location , name = "real")

class ArrayType:
    def __init__(self, location, element_type):
        self.element_type = element_type
        self.location = location
        
    def emit_json():
        return dict(location = self.location , name = "real")

class TypeDescription:
    def __init__(self, location, type_):
        pass

    def emit_json():
        return {
                    "location" : self.location,
                    type_.name : type.emit_json()
                }

class SisalType:
    def __init__(self, node_id, type_descriprion, index):
        self.node_id          = node_is
        self.type_description = type_descriprion
        self.index            = index


    def emit_json():
        return dict(
                        nodeId = self.node_id,
                        type   = type_descritpion.emit_json(),
                        index  = index,
                    )
