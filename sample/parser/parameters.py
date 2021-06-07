#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  parameters.py
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

# This module is dedicated to converting parameters in simplified form
# used in parser tree to parameters in IR-form


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
