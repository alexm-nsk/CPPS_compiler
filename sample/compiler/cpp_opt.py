# for optimization experiments

import re


id_re           = "[a-zA-Z_][a-zA-z_0-9]*"
init_expr       = lambda t, n: f"\n\s*({t})\s+({n})\s*=\s*(.*?);"
assignment_expr = lambda n: f"({n})\s*=\s*(.*?);"
return_expr     = f"\n\s*return ({id_re});"

def opt_single_uses(code):

    assignments = re.finditer(init_expr(id_re, id_re), code, re.DOTALL)

    inits_to_remove = []

    for a in assignments:
        whole_line = a.group(0)
        type_      = a.group(1)
        identifier = a.group(2)
        value      = a.group(3)

        uses = list(re.finditer("[( ](" + identifier + ")[ ;)]", code))
        num_uses   = len(uses) - 1

        if num_uses == 1:
            code = code.replace(whole_line, " "*len(whole_line))
            code = code[ :uses[1].start(1)] + value + code[uses[1].end(1): ]
            inits_to_remove.append((type_, identifier))
        elif num_uses == 0:
            code = code.replace(whole_line, " "*len(whole_line))

    return re.sub("\s*\n", "\n", code)


def opt_retvals(code):
    # should be just one "return":

    return_ = list(re.finditer(return_expr, code))

    if len(return_) == 0:
        return code
    else:
        return_ = return_[0]

    return_identifier = return_.group(1)

    # ~ assignment_expr = lambda t, n: f"{t} = (.*?);"
    assignments = list(re.finditer(assignment_expr(return_identifier) , code))

    for a in assignments:
        code = code.replace(a.group(0), "return " + a.group(2))

    code = code.replace(return_.group(0),"")

    return code


def post_opt(code, pass_ = 1):

    code = opt_single_uses(code)

    if (pass_):
        return post_opt(code, pass_-1)
    else:
        # ~ code = opt_retvals(code)
        return code
