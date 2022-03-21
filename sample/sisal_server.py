#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  sisal_server.py
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

#---------------------------------------------------------------------------------------------

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from wsgiref.simple_server import make_server
import json
import subprocess
import os
import time

from parser.parse_file import parse_file


def parse(input_text):
    return parse_file(input_text)


def compile_sisal(code):
    t = time.time()
    parsed = parse_file(code)
    formatted = json.dumps(
                        dict(
                             functions = [o.emit_json(None) for o in parsed],
                             declarations = {}
                            ),
                            indent = 1)
    # ~ print (formatted)
    print ("finished in ", round((time.time() - t),3))
    return formatted#.decode()


def service(environment, responce):

    body= ''
    def resp(status, output):
        headers =  [('Content-type','application/json; charset=utf-8' )]
        responce(status, headers)
        return  [output.encode()]

    try:
        length = int(environment.get('CONTENT_LENGTH', '0'))
        if length > 0:
            body= environment['wsgi.input'].read(length)
            data = json.loads(body, strict=False)
            if(type(data["code"])!=list):
                inputCode = [data["code"]]
            else:
                inputCode = data["code"]

    except ValueError:
        return resp("400 ERROR","error in request")

    try:
        output_codes = []

        print (str(len(inputCode)) + " modules received, compiling...")

        for c in inputCode:
               output_codes.append(compile_sisal(c))

        print("done")
        return resp("200 OK",json.dumps(outputCodes))

    except Exception as e:
        print (str(e))
        return resp("400 ERROR",json.dumps(["error compiling"]))


def main(args):
    server =make_server('', 12345, service)
    print ("serving...")
    server.serve_forever()
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
