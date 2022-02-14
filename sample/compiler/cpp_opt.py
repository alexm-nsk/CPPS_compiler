import re

def post_opt(code):

    id_re = "[a-zA-Z_][a-z0-9A-z]"
    expr = f"{id_re}\s*({id_re})\s*=\s*(.*?);"
    assignments = re.finditer(expr, str(code))
    
    for a in assignments:
        print (a)
    
    
    return code
