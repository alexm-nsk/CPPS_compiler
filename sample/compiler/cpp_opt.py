# for optimization experiments

import re

def post_opt(code):

    id_re = "[a-zA-Z_][a-z0-9A-z]*"
    expr = f"\n\s*{id_re}\s+({id_re})\s*=\s*(.*?);"

    assignments = re.finditer(expr, str(code), re.DOTALL)

    for a in assignments:

        whole_line = a.group(0)
        identifier = a.group(1)
        value      = a.group(2)

        uses = list(re.finditer("[( ](" + identifier + ")[ ;)]", code))
        num_uses   = len(uses) - 1

        if num_uses == 1:
            code = code[ :uses[1].start(1)] + value + code[uses[1].end(1): ]
            code = code.replace(whole_line, "")
            # ~ print (1)

        # ~ print (identifier, num_uses)

    return code
