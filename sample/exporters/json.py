#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  json.py
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

# Implements exporting Node and it's descendants into JSON IR

field_sub_table = dict(

    function_name = "functionName",
    node_id       = "id",
    if_           = "If",
    then          = "Then",
    else_         = "Else",
    condition     = "condition",

)

# ~ "params": [
# ~ [
  # ~ "M",
  # ~ {
    # ~ "nodeId": "node1",
    # ~ "type": {
      # ~ "location": "1:18-1:25",
      # ~ "name": "integer"
    # ~ },
    # ~ "index": 0
  # ~ }
# ~ ]
# ~ ],


def gen_params(params, nodeId = "NOT PROVIDED!"):

    ret_val = []
    for group in params:
        ret_val.extend([
            [var["name"],
                dict(
                    nodeId = nodeId, 
                    type = dict(location = var["location"], name = group["type_name"])
                )
            ]
            for var in group["var_names"]
        ])
    return ret_val

def function_make_out_ports(function):
    print ("making ports...")
    #print (function.params)

def export_function_to_json(function):
    #function_make_out_ports(self)
           
    ret_val = {}
    ret_val["params"] = gen_params( function.params , function.node_id ) if function.params else None

    for field, value in function.__dict__.items():
        IR_name          = field_sub_table[field] if field in field_sub_table else field
        ret_val[IR_name] = value

    try:
        ret_val["nodes"] = function.nodes[0].emit_json()
    except:
        print ("JSON not implemented for %s yet!" % type(function.nodes[0]))

    return ret_val


def export_if_to_json(function):

    ret_val = {}

    for field, value in function.__dict__.items():
        IR_name          = field_sub_table[field] if field in field_sub_table else field
        ret_val[IR_name] = value
        
    ret_val["name"] = field_sub_table[ret_val["name"]]
    
    # ~ print (ret_val)
    return ret_val
