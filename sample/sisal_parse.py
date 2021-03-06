#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  parse.py
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

import json

import sys


from parser.parse_file import parse_file


def parse(input_text):
    return parse_file(input_text)


def main(args):

    if (len(args) < 2):
        print("usage: python sisal_parse.py source_code.sis")
    else:

        input_file_name = args[1]
        try:
            file_contents = open(input_file_name, "r").read()
        except Exception as e:
            # TODO make sure to isolate I/O error from malformed commandline parameters
            print ("error reading %s" % input_file_name)
            print (str(e))
            return 1

        try:

            if "--debug" in args:
                from IPython.core import ultratb
                # ~ sys.excepthook = ultratb.FormattedTB(mode='Verbose', color_scheme='Linux', call_pdb=False)
                sys.excepthook = ultratb.ColorTB()

            if "--color" in args:
                from pygments.styles import get_all_styles
                from pygments import highlight, lexers, formatters
                styles = list(get_all_styles())
                color_style = styles[14] if len(styles) > 15 else styles[0]

            output = parse(file_contents)

            if "--graph" in args:
                from exporters.graphml import make_document
                graphs = "\n".join([o.emit_graphml(None) for o in output])
                graphml_text = make_document(graphs)

                if "--color" in args:
                    colored_graphml = highlight(graphml_text, lexers.XmlLexer(), formatters.Terminal256Formatter(style=color_style))
                    print(colored_graphml)
                else:
                    print (graphml_text)
            else:

                formatted = json.dumps(
                                        dict(
                                             functions = [o.emit_json(None) for o in output],
                                             declarations = {}
                                            ),
                                       indent = 2)
                if "--color" in args:
                    colored_json = highlight(formatted, lexers.JsonLexer(), formatters.Terminal256Formatter(style=color_style))
                    print(colored_json)
                else:
                    print( formatted )

        except Exception as e:
            if "--debug" in args:
                raise e
            else:
                print (str(e))

    return 0


if __name__ == '__main__':

    import sys
    sys.exit(main(sys.argv))
