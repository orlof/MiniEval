# see http://effbot.org/zone/simple-top-down-parsing.htm

import ast
import tokenize as TOKEN
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


eval_funcs = {
    "%": lambda self: self.first.eval() % self.second.eval(),
    "//": lambda self: self.first.eval() // self.second.eval(),
    "/": lambda self: self.first.eval() / self.second.eval(),
    "*": lambda self: self.first.eval() * self.second.eval(),
    "**": lambda self: self.first.eval() ** self.second.eval(),
    ">>": lambda self: self.first.eval() >> self.second.eval(),
    "<<": lambda self: self.first.eval() << self.second.eval(),
    "&": lambda self: self.first.eval() & self.second.eval(),
    "^": lambda self: self.first.eval() ^ self.second.eval(),
    "|": lambda self: self.first.eval() | self.second.eval(),
    "<>": lambda self: self.first.eval() != self.second.eval(),
    "!=": lambda self: self.first.eval() != self.second.eval(),
    "==": lambda self: self.first.eval() == self.second.eval(),
    ">=": lambda self: self.first.eval() >= self.second.eval(),
    ">": lambda self: self.first.eval() > self.second.eval(),
    "<=": lambda self: self.first.eval() <= self.second.eval(),
    "<": lambda self: self.first.eval() < self.second.eval(),
    "or": lambda self: self.first.eval() or self.second.eval(),
    "and": lambda self: self.first.eval() and self.second.eval(),
    "not": lambda self: not self.first.eval(),
    "in": lambda self: self.first.eval() in self.second.eval(),
    "is": lambda self: self.first.eval() is self.second.eval(),
    "is not": lambda self: self.first.eval() is not self.second.eval(),
    "not in": lambda self: self.first.eval() not in self.second.eval(),
    "if": lambda self: self.first.eval() if self.second.eval() else self.third.eval(),
    "~": lambda self: ~self.first.eval(),
    "+": lambda self: +self.first.eval() if self.second is None else self.first.eval() + self.second.eval(),
    "-": lambda self: -self.first.eval() if self.second is None else self.first.eval() - self.second.eval(),
    "[": lambda self: [x.eval() for x in self.first] if self.second is None else self.first.eval()[self.second.eval()],
    "{": lambda self: {key.eval(): val.eval() for key, val in self.first},
    "(": lambda self: (x.eval() for x in self.first) if self.second is None else self.first.eval()(*[x.eval() for x in self.second]),
    ".": lambda self: self.first.eval()[self.second.value],
    "(literal)": lambda self: ast.literal_eval(self.value),
    "(name)": lambda self: names[self.value]
}


class Symbol(object):
    def __init__(self, id, lbp, expr):
        self.id = id
        self.__name__ = "symbol-" + id

        self.expr = expr
        self.lbp = lbp

        self.first = None
        self.second = None
        self.third = None

        self.value = None
        self.evaluated = False
        self.evaluated_value = None

    def nud(self):
        raise SyntaxError("Syntax error (%r)." % self.id)

    def led(self, left):
        raise SyntaxError("Unknown operator (%r)." % self.id)

    def eval(self):
        if not self.evaluated:
            self.evaluated = True
            self.evaluated_value = self._eval()
        return self.evaluated_value

    def _eval(self):
        raise SyntaxError("Evaluation error (%r)." % self.id)

    def reset(self):
        self.evaluated = False
        self.evaluated_value = None

        if self.first: self.first.reset()
        if self.second: self.second.reset()
        if self.third: self.third.reset()

    def __repr__(self):
        if self.id == "(name)" or self.id == "(literal)":
            return "(%s %s)" % (self.id[1:-1], self.value)
        out = [self.id, self.first, self.second, self.third]
        out = map(str, filter(None, out))
        return "(" + " ".join(out) + ")"


class SymbolIf(Symbol):
    def __init__(self, expr):
        super().__init__("if", 20, expr)


class SymbolElse(Symbol):
    def __init__(self, expr):
        super().__init__("else", 0, expr)


class Infix(Symbol):
    def led(self, left):
        self.first = left
        self.second = expression(self.lbp)
        return self


class InfixR(Symbol):
    def led(self, left):
        self.first = left
        self.second = expression(self.lbp - 1)
        return self


class SymbolOr(InfixR):
    def __init__(self, expr):
        super().__init__("or", 30, expr)


class SymbolAnd(InfixR):
    def __init__(self, expr):
        super().__init__("and", 40, expr)


class Prefix(Symbol):
    def nud(self):
        self.first = expression(self.lbp)
        return self


class SymbolNot(Prefix, Infix):
    def __init__(self, expr):
        super().__init__("not", 60, expr)



symbal_table = {

}

if 1:

    # symbol (token type) registry
    symbol_table = {}

    def symbol(id, bp=0):
        try:
            s = symbol_table[id]
        except KeyError:
            class s(symbol_base):
                pass
            s.__name__ = "symbol-" + id # for debugging
            s.id = id
            s.value = None
            s.lbp = bp
            symbol_table[id] = s
        else:
            s.lbp = max(bp, s.lbp)

        return s

    # helpers


    def advance(id=None):
        global token
        if id and token.id != id:
            raise SyntaxError("Expected %r" % id)
        token = next()

    def method(*args):
        # decorator
        symbols = [symbol(op) for op in args]
        assert all((issubclass(symbol, symbol_base) for symbol in symbols))

        def bind(fn):
            for symbol in symbols:
                setattr(symbol, fn.__name__, fn)
        return bind

    # python expression syntax


    symbol("if", 20); symbol("else")  # ternary form

    infix_r("or", 30)
    infix_r("and", 40)

    prefix("not", 50)

    infix("in", 60); infix("not", 60) # not in
    infix("is", 60)

    symbol("<", 60)
    symbol("<=", 60)
    symbol(">", 60)
    symbol(">=", 60)
    symbol("<>", 60)
    symbol("!=", 60)
    symbol("==", 60)

    @method("<", "<=", ">", ">=", "==", "!=", "<>")
    def led(self, left):
        self.first = left
        self.second = expression(self.lbp + 1)

        if token.id in ("<", "<=", ">", ">=", "==", "!=", "<>"):
            sym_and = symbol("and")()
            sym_and.first = self

            sym_comp = symbol(token.id)()

            advance(token.id)
            sym_and.second = sym_comp.led(self.second)

            return sym_and
        else:
            return self

    infix("|", 70)
    infix("^", 80)
    infix("&", 90)

    infix("<<", 100)
    infix(">>", 100)

    infix("+", 110)
    infix("-", 110)

    infix("*", 120)
    infix("/", 120)
    infix("//", 120)
    infix("%", 120)

    prefix("-", 130)
    prefix("+", 130)
    prefix("~", 130)

    infix_r("**", 140)

    symbol(".", 150)
    symbol("[", 150)
    symbol("(", 150)

    # additional behaviour

    symbol("(name)").nud = lambda self: self
    symbol("(literal)").nud = lambda self: self
    symbol("(end)")
    symbol(")")

    @method("(")
    def nud(self):
        # parenthesized form; replaced by tuple former below
        expr = expression()
        advance(")")
        return expr

    symbol("else")

    @method("if")
    def led(self, left):
        self.first = left
        self.second = expression()
        advance("else")
        self.third = expression()
        return self

    @method(".")
    def led(self, left):
        if token.id != "(name)":
            SyntaxError("Expected an attribute name.")
        self.first = left
        self.second = token
        advance()
        return self

    symbol("]")

    @method("[")
    def led(self, left):
        self.first = left
        self.second = expression()
        advance("]")
        return self

    symbol(")")
    symbol(",")

    @method("(")
    def led(self, left):
        self.first = left
        self.second = []
        if token.id != ")":
            while 1:
                self.second.append(expression())
                if token.id != ",":
                    break
                advance(",")
        advance(")")
        return self

    symbol(":")
    symbol("=")

    def argument_list(list):
        while 1:
            if token.id != "(name)":
                SyntaxError("Expected an argument name.")
            list.append(token)
            advance()
            if token.id == "=":
                advance()
                list.append(expression())
            else:
                list.append(None)
            if token.id != ",":
                break
            advance(",")

    # constants

    def constant(id):
        @method(id)
        def nud(self):
            self.id = "(literal)"
            self.value = id
            return self

    constant("None")
    constant("True")
    constant("False")

    # multitoken operators

    @method("not")
    def led(self, left):
        if token.id != "in":
            raise SyntaxError("Invalid syntax")
        advance()
        self.id = "not in"
        self.first = left
        self.second = expression(60)
        return self

    @method("is")
    def led(self, left):
        if token.id == "not":
            advance()
            self.id = "is not"
        self.first = left
        self.second = expression(60)
        return self

    # displays

    @method("(")
    def nud(self):
        self.first = []
        comma = False
        if token.id != ")":
            while 1:
                if token.id == ")":
                    break
                self.first.append(expression())
                if token.id != ",":
                    break
                comma = True
                advance(",")
        advance(")")
        if not self.first or comma:
            return self # tuple
        else:
            return self.first[0]

    symbol("]")

    @method("[")
    def nud(self):
        self.first = []
        if token.id != "]":
            while 1:
                if token.id == "]":
                    break
                self.first.append(expression())
                if token.id != ",":
                    break
                advance(",")
        advance("]")
        return self

    symbol("}")

    @method("{")
    def nud(self):
        self.first = []
        if token.id != "}":
            while 1:
                if token.id == "}":
                    break
                key = expression()
                advance(":")
                val = expression()
                self.first.append((key, val))
                if token.id != ",":
                    break
                advance(",")
        advance("}")
        return self

    # python tokenizer

    # parser engine

    def expression(rbp=0):
        global token
        t = token
        token = next()
        left = t.nud()
        while rbp < token.lbp:
            t = token
            token = next()
            left = t.led(left)
        return left

    def parse(program):
        global token, next
        next = tokenize(program).next
        token = next()
        return expression()

    def test(program):
        print(">>>", program)
        parsed = parse(program)
        print(parsed)
        return parsed

    def eval(program):
        symbol = test(program)
        print(symbol.eval())


type_map = {
    TOKEN.NUMBER: "(literal)",
    TOKEN.STRING: "(literal)",
    TOKEN.OP: "(operator)",
    TOKEN.NAME: "(name)",
}


def tokenize_python(program):
    for t in TOKEN.generate_tokens(StringIO(program).readline):
        try:
            yield type_map[t[0]], t[1]
        except KeyError:
            if t[0] == TOKEN.NL:
                continue
            if t[0] == TOKEN.ENDMARKER:
                break
            else:
                raise SyntaxError("Syntax error")

    yield "(end)", "(end)"


class Evaluator(object):
    def __init__(self):
        self.expr = None
        self.ext = None

        self.token_iter = None
        self.token = None

        self.ast = None

    def parse(self, expr):
        self.expr = expr

        self.token_iter = self.tokenize(expr)
        self.token = next(self.token_iter)
        self.ast = self.expression()

        return self.ast

    def eval(self, ext=None):
        if ext is None:
            ext = {}
        self.ext = ext

    def expression(self, rbp=0):
        t = self.token
        self.token = next(self.token_iter)

        left = t.nud()
        while rbp < self.token.lbp:
            t = self.token
            self.token = next(self.token_iter)
            left = t.led(left)
        return left

    def tokenize(self, program):
        if isinstance(program, list):
            source = program
        else:
            source = tokenize_python(program)

        for op, value in source:
            if op == "(literal)":
                symbol = symbol_table[op]
                s = symbol()
                s.value = value
            else:
                # name or operator
                symbol = symbol_table.get(value)
                if symbol:
                    s = symbol()
                elif op == "(name)":
                    symbol = symbol_table[op]
                    s = symbol()
                    s.value = value
                else:
                    raise SyntaxError("Unknown operator (%r)" % op)
            yield s




def mini_eval(expr, ext=None):
    evaluator = Evaluator()
    evaluator.parse(expr)
    return evaluator.eval(ext)


