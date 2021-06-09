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

class SisalType:
    pass
    
# ~ class Integer(SisalType):
    
    # ~ def __init__(self):
        # ~ pass
        
    # ~ def __repr__(self):
        # ~ return "Integer"

class SisalArray:
    
    def __init__(self, sisal_type):
        self.item_type = sisal_type

    def __repr__(self):
        return "Array[%s]" % self.item_type
