import os
import sys

GARBAGE = "<>"
JACK_FILE = 1
KEYWORD = "keyword"
SYMBOL = "symbol"
INT_CONST = "integerConstant"
STR_CONST = "stringConstant"
IDENTIFIER = "identifier"

ALL_TOKENS = {"keyword": ["class", "constructor", "function", "method", "field", "static", "var",
                          "int", "char", "boolean", "void", "true", "false", "null", "this",
                          "let", "do", "if", "else", "while", "return"],
              "symbol": ["{", "}", "(", ")", "[", "]", ".", ",", ";", "+", "-", "*", "/", "&",
                         "|", "<", ">", "=", "~"],
              "op": ["+", "-", "*", "/", "&", "|", "<", ">", "="],
              "keyConst": ["true", "false", "null", "this"],
              "statements": ["let", "if", "while", "do", "return"],
              "unary": ["~", "-"],
              "type": ["int", "char", "boolean"],
              "subroutine": ["constructor", "function", "method"],
              "class": ["static", "field"]}
REG_TYPES = ["int", "char", "boolean"]
OS_CLASSES = ["Array", "Keyboard", "Math", "Memory", "Output", "Screen", "String", "Sys"]
INT_UPPER = 32767
INT_LOWER = 0
TYPE_POS = 0
KIND_POS = 1
INDEX_POS = 2
TYPE = 0
NAME = 1
THIS = "this"
STATIC = "static"
ARGUMENT = "argument"
FIELD = "field"
LOCAL = "local"
TRUE = "true"
FALSE = "false"
NULL = "null"
CTOR = "constructor"
METHOD = "method"
POINTER = "pointer"
CONSTANT = "constant"
TEMP = "temp"
THAT = "that"


class Token:
    def __init__(self, value, tok_type):
        self.value = value
        self.type = tok_type


class SymbolTable:
    def __init__(self):
        self.this_index = 0
        self.static_index = 0
        self.argument_index = 0
        self.local_index = 0
        self.map = dict()

    def start(self):
        self.__init__()

    def define(self, var_name, var_type, var_kind):
        index = 0
        if var_kind == FIELD:
            index = self.this_index
            var_kind = THIS
            self.this_index += 1
        elif var_kind == STATIC:
            index = self.static_index
            self.static_index += 1
        elif var_kind == ARGUMENT:
            index = self.argument_index
            self.argument_index += 1
        elif var_kind == LOCAL:
            index = self.local_index
            self.local_index += 1
        self.map[var_name] = (var_type, var_kind, index)

    def var_count(self, var_kind):
        res = 0
        for key in self.map:
            if self.map[key][KIND_POS] == var_kind:
                res += 1
        return res

    def kind_of(self, var_name):
        if var_name in self.map:
            return self.map[var_name][KIND_POS]
        return None

    def type_of(self, var_name):
        if var_name in self.map:
            return self.map[var_name][TYPE_POS]
        return None

    def index_of(self, var_name):
        if var_name in self.map:
            return self.map[var_name][INDEX_POS]
        return None


class VMWriter:
    def __init__(self, filename):
        self.file = open(filename, "w")

    def write_push(self, segment, index):
        self.file.write("push " + str(segment) + " " + str(index) + "\n")

    def write_pop(self, segment, index):
        self.file.write("pop " + str(segment) + " " + str(index) + "\n")

    def write_arithmetic(self, command):
        if command == '+':
            self.file.write("add" + "\n")
        if command == '-':
            self.file.write("sub" + "\n")
        if command == '=':
            self.file.write("eq" + "\n")
        if command == '>':
            self.file.write("gt" + "\n")
        if command == '<':
            self.file.write("lt" + "\n")
        if command == '&':
            self.file.write("and" + "\n")
        if command == '|':
            self.file.write("or" + "\n")
        if command == '*':
            self.write_call("Math.multiply", 2)
        if command == '/':
            self.write_call("Math.divide", 2)

    def write_unary(self, command):
        if command == '~':
            self.file.write("not" + "\n")
        if command == '-':
            self.file.write("neg" + "\n")

    def write_label(self, label_name):
        self.file.write("label " + label_name + "\n")

    def write_goto(self, label_name):
        self.file.write("goto " + label_name + "\n")

    def write_if(self, label_name):
        self.file.write("if-goto " + label_name + "\n")

    def write_call(self, func_name, argc):
        self.file.write("call " + func_name + " " + str(argc) + "\n")

    def write_function(self, func_name, argc):
        self.file.write("function " + func_name + " " + str(argc) + "\n")

    def write_return(self):
        self.file.write("return" + "\n")

    def close_file(self):
        self.file.close()


def is_keyword(token):
    return token in ALL_TOKENS["keyword"]


def is_symbol(token):
    return token in ALL_TOKENS["symbol"]


def is_integer_constant(token):
    int_st = ""
    for char in token:
        if "0" <= char <= "9":
            int_st += char
        else:
            return False
    return INT_LOWER <= int(int_st) <= INT_UPPER


def is_string_constant(token):
    for char in token[1:-1]:
        if char == "\"" or char == "\n":
            return False
    return token[0] == "\"" and token[-1] == "\""


def is_identifier(token):
    for char in token:
        if "0" <= char <= "9" or "A" <= char <= "Z" or "a" <= char <= "z" or char == "_":
            continue
        else:
            return False
    return True


def make_jack_st(lines):
    lines = first_pass(lines)
    return create_st(lines)


def rid_of_spaces(st):
    new_st = ""
    add_space = False
    for sym in ALL_TOKENS["symbol"]:
        if sym in st:
            st = st.replace(sym, " " + sym + " ")
    # get rid of all spaces
    i = 0
    while i < len(st):
        if st[i] == "\"":
            if add_space is True:
                new_st += " "
                add_space = False
            index = st[i + 1:].index("\"")
            new_st += st[i:i + index + 2].replace(" ", GARBAGE)
            i += index + 2
            continue
        if st[i] == " " or st[i] == "\t" or st[i] == "\n" or st[i] == "\r":
            add_space = True
            i += 1
            continue
        if add_space is True:
            new_st += " "
            add_space = False
        new_st += st[i]
        i += 1
    if len(new_st) > 0 and new_st[-1] != " ":
        new_st += " "
    return new_st


def first_pass(lines):
    i = 0
    while i < len(lines):
        if "//" in lines[i]:
            lines[i] = lines[i][:lines[i].index("//")]
        elif "/**" in lines[i]:
            while "*/" not in lines[i]:
                lines[i] = ""
                i += 1
            lines[i] = ""
        elif "/*" in lines[i]:
            lines[i] = lines[i][:lines[i].index("/*")]
        lines[i] = rid_of_spaces(lines[i])
        i += 1
    return lines


def create_st(lines):
    st = ""
    for i in range(len(lines)):
        if lines[i]:
            st = st + str(lines[i])
    return st


class JackTokenizer:

    def __init__(self, string_list):
        self.index = 0
        self.string_list = string_list
        st = make_jack_st(string_list)
        self.string_list = st.split()

    def has_more_tokens(self):
        if self.index < len(self.string_list):
            return True
        return False

    def get_next_token(self):
        if is_keyword(self.string_list[self.index]):
            token = Token(self.string_list[self.index], KEYWORD)
        elif is_symbol(self.string_list[self.index]):
            token = Token(self.string_list[self.index], SYMBOL)
        elif is_integer_constant(self.string_list[self.index]):
            token = Token(self.string_list[self.index], INT_CONST)
        elif is_string_constant(self.string_list[self.index]):
            token = Token(self.string_list[self.index].replace("<>", " "), STR_CONST)
        elif is_identifier(self.string_list[self.index]):
            token = Token(self.string_list[self.index], IDENTIFIER)
        self.index += 1
        return token

    def go_back(self):
        self.index -= 1


def is_term(token):
    return token.type == IDENTIFIER or token.type == INT_CONST or token.type == STR_CONST \
           or token.value in ALL_TOKENS["keyConst"] or token.value == "(" \
           or token.value in ALL_TOKENS["unary"]


def is_statement(token):
    return token.value in ALL_TOKENS["statements"]


class CompilationEngine:
    def __init__(self, jk, vmw):
        self.jk = jk
        self.vmw = vmw
        self.current_token = jk.get_next_token()
        self.class_name = ""
        self.func_name = ""
        self.call_name = ""
        self.class_st = SymbolTable()
        self.func_st = SymbolTable()
        self.is_void = False
        self.is_method = False
        self.is_ctor = False
        self.argc = 1
        self.add_arg = 0
        self.label_index = 1
        self.first_is_array = False
        self.second_is_array = False

    def compile_all(self):
        self.compile_class()

    # def write_token(self):
    #     self.out_file.write("\t" * self.tabs + "<" + self.current_token.type + "> " +
    #                         self.current_token.value + " </" + self.current_token.type + ">\n")

    def compile_class(self):
        self.class_st.start()
        # 'class'
        self.current_token = self.jk.get_next_token()
        # class name
        self.class_name = self.current_token.value
        self.current_token = self.jk.get_next_token()
        # {
        self.current_token = self.jk.get_next_token()
        while self.current_token.value in ALL_TOKENS["class"]\
                or self.current_token.value in ALL_TOKENS["subroutine"]:
            if self.current_token.value in ALL_TOKENS["class"]:
                self.compile_class_var_dec()
                self.current_token = self.jk.get_next_token()
            elif self.current_token.value in ALL_TOKENS["subroutine"]:
                self.compile_subroutine_dec()
                self.current_token = self.jk.get_next_token()
        # }

    def compile_class_var_dec(self):
        # ('static'|'field')
        static_or_field = self.current_token.value
        self.current_token = self.jk.get_next_token()
        # type
        var_type = self.current_token.value
        self.current_token = self.jk.get_next_token()
        # var name
        self.class_st.define(self.current_token.value, var_type, static_or_field)
        self.current_token = self.jk.get_next_token()
        while self.current_token.value == ",":
            # ','
            self.current_token = self.jk.get_next_token()
            # var name
            self.class_st.define(self.current_token.value, var_type, static_or_field)
            self.current_token = self.jk.get_next_token()
        # ';'

    def compile_subroutine_body(self):
        # {
        self.current_token = self.jk.get_next_token()
        while self.current_token.value == "var":
            self.compile_var_dec()
            self.current_token = self.jk.get_next_token()
        self.vmw.write_function(self.class_name + "." + self.func_name, self.func_st.var_count(LOCAL))
        if self.is_method is True:
            self.vmw.write_push(ARGUMENT, 0)
            self.vmw.write_pop(POINTER, 0)
        elif self.is_ctor is True:
            self.vmw.write_push(CONSTANT, self.class_st.var_count(THIS))
            self.vmw.write_call("Memory.alloc", 1)
            self.vmw.write_pop(POINTER, 0)
        self.compile_statements()
        self.current_token = self.jk.get_next_token()
        # }

    def compile_subroutine_dec(self):
        self.func_st.start()
        # (constructor|function|method)
        self.is_ctor, self.is_method = False, False
        if self.current_token.value == METHOD:
            self.func_st.define(THIS, self.class_name, ARGUMENT)
            self.is_method = True
        elif self.current_token.value == CTOR:
            self.is_ctor = True
        self.current_token = self.jk.get_next_token()
        # (void|type)
        if self.current_token.value == "void":
            self.is_void = True
        else:
            self.is_void = False
        self.current_token = self.jk.get_next_token()
        # subroutine name
        self.func_name = self.current_token.value
        self.current_token = self.jk.get_next_token()
        # (
        self.current_token = self.jk.get_next_token()
        self.compile_parameter_list()
        self.current_token = self.jk.get_next_token()
        # )
        self.current_token = self.jk.get_next_token()
        self.compile_subroutine_body()

    def compile_parameter_list(self):
        if self.current_token.value in ALL_TOKENS["type"]:
            # type
            var_type = self.current_token.value
            self.current_token = self.jk.get_next_token()
            # var name
            self.func_st.define(self.current_token.value, var_type, ARGUMENT)
            self.current_token = self.jk.get_next_token()
            if self.current_token.value == ",":
                while self.current_token.value == ",":
                    # ,
                    self.current_token = self.jk.get_next_token()
                    # type
                    var_type = self.current_token.value
                    self.current_token = self.jk.get_next_token()
                    # var name
                    self.func_st.define(self.current_token.value, var_type, ARGUMENT)
                    self.current_token = self.jk.get_next_token()
                self.jk.go_back()
            else:
                self.jk.go_back()
        else:
            self.jk.go_back()

    def compile_var_dec(self):
        # 'var'
        self.current_token = self.jk.get_next_token()
        # type
        var_type = self.current_token.value
        self.current_token = self.jk.get_next_token()
        # var name
        self.func_st.define(self.current_token.value, var_type, "local")
        self.current_token = self.jk.get_next_token()
        while self.current_token.value == ",":
            # ,
            self.current_token = self.jk.get_next_token()
            # var name
            self.func_st.define(self.current_token.value, var_type, "local")
            self.current_token = self.jk.get_next_token()
        # ;

    def compile_statements(self):
        if is_statement(self.current_token):
            while is_statement(self.current_token):
                self.argc = 1
                self.add_arg = 0
                self.call_name = ""
                if self.current_token.value == "let":
                    self.compile_let()
                    self.current_token = self.jk.get_next_token()
                elif self.current_token.value == "if":
                    self.compile_if()
                    self.current_token = self.jk.get_next_token()
                elif self.current_token.value == "while":
                    self.compile_while()
                    self.current_token = self.jk.get_next_token()
                elif self.current_token.value == "do":
                    self.compile_do()
                    self.vmw.write_pop("temp", 0)
                    self.current_token = self.jk.get_next_token()
                elif self.current_token.value == "return":
                    self.compile_return()
                    self.current_token = self.jk.get_next_token()
            self.jk.go_back()
        else:
            self.jk.go_back()

    def compile_do(self):
        # do
        self.current_token = self.jk.get_next_token()
        # subroutine identifier
        if self.current_token.value in self.func_st.map:
            self.call_name = self.func_st.type_of(self.current_token.value)
            self.vmw.write_push(self.func_st.kind_of(self.current_token.value),
                                self.func_st.index_of(self.current_token.value))
            self.add_arg = 1
        elif self.current_token.value in self.class_st.map:
            self.call_name = self.class_st.type_of(self.current_token.value)
            self.vmw.write_push(self.class_st.kind_of(self.current_token.value),
                                self.class_st.index_of(self.current_token.value))
            self.add_arg = 1
        else:
            # class name
            if 'A' <= self.current_token.value[0] <= 'Z':
                self.call_name = self.current_token.value
            else:
            # subroutine name
                self.call_name = self.current_token.value
                self.vmw.write_push(POINTER, 0)
                self.add_arg = 1
        self.current_token = self.jk.get_next_token()
        self.compile_subroutine_call()
        self.current_token = self.jk.get_next_token()
        # ;

    def compile_let(self):
        self.first_is_array = False
        self.second_is_array = False
        # let
        self.current_token = self.jk.get_next_token()
        # some var name
        var_name = self.current_token.value
        self.current_token = self.jk.get_next_token()
        if self.current_token.value == "[":
            # [
            self.first_is_array = True
            if var_name in self.func_st.map:
                self.vmw.write_push(self.func_st.kind_of(var_name), self.func_st.index_of(var_name))
            elif var_name in self.class_st.map:
                self.vmw.write_push(self.class_st.kind_of(var_name), self.class_st.index_of(var_name))
            self.current_token = self.jk.get_next_token()
            self.compile_expression()
            self.current_token = self.jk.get_next_token()
            # ]
            self.vmw.write_arithmetic("+")
            self.current_token = self.jk.get_next_token()
        self.argc = 1
        self.call_name = ""
        self.add_arg = 0
        # =
        self.current_token = self.jk.get_next_token()
        self.compile_expression()
        if self.first_is_array is True:
            if self.second_is_array is True:
                self.vmw.write_pop(TEMP, 0)
                self.vmw.write_pop(POINTER, 1)
                self.vmw.write_push(TEMP, 0)
                self.vmw.write_pop(THAT, 0)
            else:
                # only first is array
                self.vmw.write_pop(TEMP, 0)
                self.vmw.write_pop(POINTER, 1)
                self.vmw.write_push(TEMP, 0)
                self.vmw.write_pop(THAT, 0)
        else:
            if var_name in self.func_st.map:
                self.vmw.write_pop(self.func_st.kind_of(var_name), self.func_st.index_of(var_name))
            elif var_name in self.class_st.map:
                self.vmw.write_pop(self.class_st.kind_of(var_name), self.class_st.index_of(var_name))
            else:
                raise Exception("wow such code very bad")
        self.current_token = self.jk.get_next_token()
        # ;

    def compile_while(self):
        # while
        start_label = self.label_index
        self.vmw.write_label("L" + str(start_label))
        self.label_index += 2
        self.current_token = self.jk.get_next_token()
        # (
        self.current_token = self.jk.get_next_token()
        self.compile_expression()
        self.vmw.write_unary("~")
        self.current_token = self.jk.get_next_token()
        # )
        self.vmw.write_if("L" + str(start_label + 1))
        self.current_token = self.jk.get_next_token()
        # {
        self.current_token = self.jk.get_next_token()
        self.compile_statements()
        self.vmw.write_goto("L" + str(start_label))
        self.current_token = self.jk.get_next_token()
        # }
        self.vmw.write_label("L" + str(start_label + 1))
        self.label_index += 1

    def compile_return(self):
        # 'return'
        self.current_token = self.jk.get_next_token()
        if self.is_ctor is True:
            self.vmw.write_push(POINTER, 0)
            self.current_token = self.jk.get_next_token()
        elif self.current_token.value != ";":
            self.compile_expression()
            self.current_token = self.jk.get_next_token()
        if self.is_void is True:
            self.vmw.write_push("constant", 0)
        self.vmw.write_return()

    def compile_if(self):
        # if
        self.current_token = self.jk.get_next_token()
        # (
        self.current_token = self.jk.get_next_token()
        self.compile_expression()
        self.vmw.write_unary("~")
        start_label = self.label_index
        self.vmw.write_if("L" + str(start_label))
        self.label_index += 2
        self.current_token = self.jk.get_next_token()
        # )
        self.current_token = self.jk.get_next_token()
        # {
        self.current_token = self.jk.get_next_token()
        self.compile_statements()
        self.vmw.write_goto("L" + str(start_label + 1))
        self.vmw.write_label("L" + str(start_label))
        self.current_token = self.jk.get_next_token()
        # }
        self.current_token = self.jk.get_next_token()
        if self.current_token.value == "else":
            # else
            self.current_token = self.jk.get_next_token()
            # {
            # self.write_token()
            self.current_token = self.jk.get_next_token()
            self.compile_statements()
            self.current_token = self.jk.get_next_token()
            # }
        else:
            self.jk.go_back()
        self.vmw.write_label("L" + str(start_label + 1))

    def compile_expression(self):
        self.compile_term()
        if self.jk.has_more_tokens():
            self.current_token = self.jk.get_next_token()
            if self.current_token.value in ALL_TOKENS["op"]:
                saved_op = self.current_token.value
                self.current_token = self.jk.get_next_token()
                self.compile_term()
                self.vmw.write_arithmetic(saved_op)
            else:
                self.jk.go_back()

    def compile_term(self):
        # (expression)
        if self.current_token.value == "(":
            # (
            self.current_token = self.jk.get_next_token()
            self.compile_expression()
            self.current_token = self.jk.get_next_token()
            # )
        # unaryOp term
        elif self.current_token.value in ALL_TOKENS["unary"]:
            # some unary op
            save_un = self.current_token.value
            self.current_token = self.jk.get_next_token()
            self.compile_term()
            self.vmw.write_unary(save_un)
        # all the others start with int constant or string constant or identifier
        else:
            # int constant or string constant or identifier
            if is_integer_constant(self.current_token.value):
                self.vmw.write_push("constant", self.current_token.value)
            elif is_string_constant(self.current_token.value):
                self.vmw.write_push(CONSTANT, len(self.current_token.value) - 2)
                self.vmw.write_call("String.new", 1)
                for char in self.current_token.value[1:-1]:
                    self.vmw.write_push(CONSTANT, ord(char))
                    self.vmw.write_call("String.appendChar", 2)
            elif is_identifier(self.current_token.value):
                if self.current_token.value == TRUE:
                    self.vmw.write_push("constant", 1)
                    self.vmw.write_unary("-")
                elif self.current_token.value == NULL or self.current_token.value == FALSE:
                    self.vmw.write_push("constant", 0)
                elif self.current_token.value in self.func_st.map:
                    self.vmw.write_push(self.func_st.kind_of(self.current_token.value),
                                        self.func_st.index_of(self.current_token.value))
                    if self.func_st.type_of(self.current_token.value) not in REG_TYPES\
                            and self.current_token.value != THIS and \
                            self.func_st.type_of(self.current_token.value) not in OS_CLASSES:
                        self.add_arg = 1
                    if self.call_name == "":
                        self.call_name = self.func_st.type_of(self.current_token.value)
                elif self.current_token.value in self.class_st.map:
                    self.vmw.write_push(self.class_st.kind_of(self.current_token.value),
                                        self.class_st.index_of(self.current_token.value))
                    if self.class_st.type_of(self.current_token.value) not in REG_TYPES \
                            and self.func_st.type_of(self.current_token.value) not in OS_CLASSES:
                        self.add_arg = 1
                    if self.call_name == "":
                        self.call_name = self.class_st.type_of(self.current_token.value)
                else:
                    self.call_name = self.current_token.value
                    self.add_arg = 0

            self.current_token = self.jk.get_next_token()
            # var name [expression]
            if self.current_token.value == "[":
                # [
                self.current_token = self.jk.get_next_token()
                self.compile_expression()
                self.current_token = self.jk.get_next_token()
                # ]
                self.vmw.write_arithmetic("+")
                self.vmw.write_pop(POINTER, 1)
                self.vmw.write_push(THAT, 0)
            elif self.current_token.value == "(" or self.current_token.value == ".":
                self.compile_subroutine_call()
            else:
                self.jk.go_back()

    def compile_expression_list(self):
        if is_term(self.current_token):
            while is_term(self.current_token):
                self.compile_expression()
                self.current_token = self.jk.get_next_token()
                if self.current_token.value == ",":
                    self.argc += 1
                    # ','
                    self.current_token = self.jk.get_next_token()
                else:
                    self.jk.go_back()
                    break
        else:
            self.argc = 0
            self.jk.go_back()

    def compile_subroutine_call(self):
        if self.current_token.value == "(":
            # (
            self.current_token = self.jk.get_next_token()
            self.compile_expression_list()
            self.current_token = self.jk.get_next_token()
            # )
            self.vmw.write_call(self.class_name + "." + self.call_name, self.argc + self.add_arg)
        elif self.current_token.value == ".":
            # .
            self.current_token = self.jk.get_next_token()
            # subroutine name
            self.call_name += "." + self.current_token.value
            self.current_token = self.jk.get_next_token()
            # (
            self.current_token = self.jk.get_next_token()
            self.compile_expression_list()
            self.current_token = self.jk.get_next_token()
            self.vmw.write_call(self.call_name, self.argc + self.add_arg)
            # )


def read_file(file_name):
    with open(file_name, "r") as file:
        lines = list()
        for line in file:
            lines.append(line)
    return lines


def main():
    list_of_files = list()
    # check if the path is a directory and fills list_of_files with all the files names
    st = sys.argv[JACK_FILE]
    if os.path.isdir(st):
        for filename in os.listdir(st):
            if filename.endswith(".jack"):
                list_of_files.append(
                    os.path.join(os.path.normpath(st), filename))
    else:
        list_of_files.append(os.path.join(st))

    for file_name in list_of_files:
        jack_lines = read_file(file_name)
        tokenizer = JackTokenizer(jack_lines)
        pre, ext = os.path.splitext(file_name)
        new_file = pre + ".vm"
        vmw = VMWriter(new_file)
        compiler = CompilationEngine(tokenizer, vmw)
        compiler.compile_all()

    # for file_name in list_of_files:
    #     jack_lines = read_file(file_name)
    #     tokenizer = JackTokenizer(jack_lines)
    #     pre, ext = os.path.splitext(file_name)
    #     new_file = pre + ".xml"
    #     with open(new_file, "w") as this_file:
    #         compiler = CompilationEngine(tokenizer, this_file)
    #         compiler.compile_all()


if __name__ == '__main__':
    main()