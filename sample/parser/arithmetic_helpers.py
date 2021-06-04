#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  arithmetic_helpers.py
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


def set_priorities(expression, callback):
    
    high = ["*", "/"]
    low  = ["+", "-"]

    def split (expression):
        
        if len(expression) == 1:
            return expression[0]
            
        # gets a low priority binary operation (like "+") closest  to
        # the beginning of input, or input length if there are none left
        index = min ([expression.index(o) if o in expression 
                      else len(expression) 
                      for o in low])
        
        if (index >= len(expression)):            
            return callback(expression)

        op = expression[index]
        
        if not op in expression: return expression
        
        left  = split(expression[:index])
        right = split(expression[index+1:])
        
        return callback([left,op, right])
    
    return split(expression)
