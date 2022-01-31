CPP_INDENT = " " * 4

class CppScope:
    def __init__(self, vars_, builder = None):
        self.builder = builder
        self.vars = vars_
        pass

class Type:

    def __init__(self):
        pass


class IntegerType(Type):

    def __init__(self, bit_depth = 64):
        self.bit_depth = bit_depth

    def __str__(self):
        return "int"


class StringType(Type):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class VoidType(Type):
    
    def __str__(self):
        return "void"


class Argument:

    def __init__(self, name, type_, index):
        print ("arg added")
        self.name = name
        self.type = type_
        self.index = index

    def __str__(self):
        return f"{self.type} {self.name}"


class Statement:

    def __init__(self):
        return 0

    def __str__(self):
        return 0


class Assignment(Statement):
    pass


class Return(Statement):

    def __init__(self, object_):
        self.object = object_

    def __str__(self):
        return "return " + str(self.object)


class Expression():

    num_identifiers = 0

    def get_new_name(self):
        Expression.num_identifiers += 1
        return "id" + str(Expression.num_identifiers)

    def __init__(self, name):
        if not name:
            self.name = self.get_new_name()
        else:
            self.name = name

    def __str__(self):
        return self.name


class Variable(Expression):

    def __init__(self, type_, value = None, name = None):
        super().__init__(name)
        self.type = type_
        self.init_code = str(value)


class Constant(Expression):

    def __init__(self, value, name = None):
        super().__init__(name)
        self.value = value

    def __str__(self):
        return str(self.value)


class Call(Expression):

    def __init__(self, function, args : "a list of c++ identifiers", name = None):
        super().__init__(name)
        self.function = function
        self.args = args
        self.type = function.return_type
        self.init_code = self.function.name + "(" + ",".join((str(s) for s in self.args)) + ")"


class If(Expression):

    def __init__(self, cond, indent_level, name = None):
        super().__init__(name)
        self.cond  = cond
        self.then  = Block(1)
        self.else_ = Block(1)
        self.indent_level = indent_level

    def get_then(self):
        return self.then

    def get_else(self):
        return self.else_

    def __str__(self):
        ind = self.indent_level * CPP_INDENT
        return f"if({self.cond})\n" + ind +  "{" + ind +  str(self.then) +"\n"+ ind +"}\n"+ ind +"else\n" + ind + "{" + str(self.else_) +"\n"+ ind + "}"


class CppCode(Expression):

    def __init__(self, code, name = None):
        super().__init__(name)
        self.code = code

    def __str__(self):
        return self.code


class Binary(Expression):

    def __init__(self, left, right, operator, name = None):
        super().__init__(name)
        self.left     = left
        self.right    = right
        self.operator = operator
        self.type = IntegerType(32)
        self.init_code = f"{str(self.left)} {self.operator} {str(self.right)}"

    #def __str__(self):
        #return f"{str(self.left)} {self.operator} {str(self.right)}"


class WhileLoop(Expression):

    def __init__(self, init, precond, body, name = None):
        super().__init__(name)
        self.init = init
        self.precond = precond
        self.body = body
        self.body_block = Block(name = "loop")


class VarReference(Expression):

    def __init__(self, var_name):
        self.var_name = var_name

    def __str__(self):
        return self.var_name

class Function:

    def __init__(self, name, return_type, arguments: "list of (name, type) - tuples", main = False):
        self.name = name
        self.return_type = return_type
        self.arguments = []
        self.statements = []
        self.entry_block = Block(name = "entry")
        self.is_main = main

        if not main:
            for index, (name, type_) in enumerate(arguments):
                argument = Variable (name = name,type_ =  type_)
                self.arguments.append(argument)
        else:
            self.arguments = []

    def get_entry_block(self):
        return self.entry_block

    def get_argument_by_name(self, name):
        return list(filter(lambda x: x.name == name, self.arguments))[0]

    def get_argument_by_index(self, index):
        return self.arguments[index]

    def get_arguments(self):
        return self.arguments

    def __str__(self):
        text = ""
        footer = ""

        if self.is_main:
            arg_text = "int argc, char **argv"
            footer = "\n" + CPP_INDENT + "return 0;\n"
        else:
            arg_text = ", ".join([str (a.type) +" "+ str(a) for a in self.arguments])

        text += f"{self.return_type} {self.name}({arg_text})\n"
        text += "{\n" + f"{self.entry_block}"  + footer + "}"
        return text


class Block:

    def __init__(self, indent_offset = 1, name = None):
        self.inits = []
        self.statements = []
        self.indent_level = indent_offset
        self.name = name

    def add_expression(self, exp, name = None):
        self.statements.append(exp)
        if type (exp) == Variable:
            inits.append(exp)

    def add_init(self, identifier):
        self.inits.append(identifier)

    def __str__(self):
        # ~ value_init = "= " +
        label = "\n" if self.name == None else CPP_INDENT * self.indent_level + f"// {self.name}:"  + "\n"
        inits = "".join(  CPP_INDENT * self.indent_level +
                            str(s.type) + " "  +
                            str(s.name) + " = " +
                            str(s.init_code) +
                            ";\n"
                            for s in self.inits)
        body = "".join( CPP_INDENT * self.indent_level +
                            str(s) + (";" if type(s) != If else "\n") for s in self.statements)
        return label + inits + body

    def add_ret(self, object_):
        self.statements.append(Return(object_))

    def add_if(self, if_):
        self.statements.append(if_)

    def add_bin(self, bin_):
        self.statements.append(bin_)

    def add_var_reference(self, vr):
        self.statements.append(vr)


class Builder:

    def __init__(self, block):
        self.block = block

    def call(self, function, args, name = None):
        call = Call(function, args, name)
        self.block.add_init(call)
        return call

    def define(self, type_, value = None, name = None):
        identifier = Variable(type_, value, name)
        self.block.add_init(identifier)
        return identifier

    def ret(self, object_):
        self.block.add_ret(object_)

    def printf(self, object_):
        code = f'printf("%d", {object_})'
        self.block.add_expression(CppCode(code))

    def if_(self, cond):
        if_ = If(cond, self.block.indent_level)
        self.block.add_if(if_)
        return if_

    def binary(self, left, right, op):
        bin_ = Binary(left, right, op)
        self.block.add_init(bin_)
        return bin_

    def constant(self, value):
        c = Constant(value)
        return c

    def while_(self, init, precond, body):

        return None

    def var_ref(self, name):
        vr = VarReference(name)
        self.block.add_var_reference(vr)
        return vr


class Module:

    def __init__(self, name):
        self.name = name
        self.functions = {}
        Module.printf = Function("printf", IntegerType(32), [("number", IntegerType(32))])

    def add_function(self, function):
        self.functions[function.name] = function
        function.containing_module = self

    def __str__(self):
        text = "//" +  self.name + "\n"
        text += "#include <stdio.h>\n\n"
        for name, f in self.functions.items():
            text += str(f) + "\n\n"
        return text
