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
    def __init__(self, id, bp, evaluator):
        self.id = id
        self.__name__ = "symbol-" + id

        self.evaluator = evaluator
        self.led_bp = self.nud_bp = self.lbp = lbp

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


class Infix(Symbol):
    def led(self, left):
        self.first = left
        self.second = self.evaluator.expression(self.led_bp)
        return self


class InfixR(Symbol):
    def led(self, left):
        self.first = left
        self.second = self.evaluator.expression(self.led_bp - 1)
        return self


class Prefix(Symbol):
    def nud(self):
        self.first = self.evaluator.expression(self.nud_bp)
        return self


class SymbolLiteral(Symbol):
    def nud(self):
        return self

    def _eval(self):
        return ast.literal_eval(self.value)


class SymbolName(Symbol):
    def nud(self):
        return self

    def _eval(self):
        return self.evaluator.names[self.value]


class SymbolReference(Symbol):
    def __init__(self, expr):
        super(SymbolReference, self).__init__(".", 150, expr)

    def led(self, left):
        if self.evaluator.token.id != "(name)":
            SyntaxError("Expected an attribute name.")
        self.first = left
        self.second = self.evaluator.token
        self.evaluator.advance()
        return self

    def _eval(self):
        return self.first.eval()[self.second.value]


class SymbolIs(Symbol):
    def __init__(self, expr):
        super(SymbolIs, self).__init__("is", 60, expr)
        self.is_not = False
        self.nud_bp = 50

    def led(self, left):
        if self.evaluator.token.id == "not":
            self.evaluator.advance()
            self.id = "is not"
            self.is_not = True
        self.first = left
        self.second = self.evaluator.expression(60)
        return self

    def _eval(self):
        if self.is_not:
            return self.first.eval() is not self.second.eval()
        return self.first.eval() is self.second.eval()


class SymbolIf(Symbol):
    def __init__(self, expr):
        super(SymbolIf, self).__init__("if", 20, expr)

    def led(self, left):
        self.first = left
        self.second = self.evaluator.expression()
        self.evaluator.advance("else")
        self.third = self.evaluator.expression()
        return self

    def _eval(self):
        return self.first.eval() if self.second.eval() else self.third.eval()


class SymbolEnd(Symbol):
    pass


class SymbolClosingParenthesis(Symbol):
    pass


class SymbolElse(Symbol):
    pass


class SymbolBitwiseOr(Infix):
    def __init__(self, expr):
        super(SymbolBitwiseOr, self).__init__("|", 70, expr)

    def _eval(self):
        return self.first.eval() | self.second.eval()


class SymbolBitwiseXor(Infix):
    def __init__(self, expr):
        super(SymbolBitwiseXor, self).__init__("^", 80, expr)

    def _eval(self):
        return self.first.eval() ^ self.second.eval()


class SymbolBitwiseAnd(Infix):
    def __init__(self, expr):
        super(SymbolBitwiseAnd, self).__init__("&", 90, expr)

    def _eval(self):
        return self.first.eval() & self.second.eval()


class SymbolShiftLeft(Infix):
    def __init__(self, expr):
        super(SymbolShiftLeft, self).__init__("<<", 100, expr)

    def _eval(self):
        return self.first.eval() << self.second.eval()


class SymbolShiftRight(Infix):
    def __init__(self, expr):
        super(SymbolShiftRight, self).__init__(">>", 100, expr)

    def _eval(self):
        return self.first.eval() >> self.second.eval()


class SymbolMultiplication(Infix):
    def __init__(self, expr):
        super(SymbolMultiplication, self).__init__("*", 120, expr)

    def _eval(self):
        return self.first.eval() * self.second.eval()


class SymbolDivision(Infix):
    def __init__(self, expr):
        super(SymbolDivision, self).__init__("/", 120, expr)

    def _eval(self):
        return self.first.eval() / self.second.eval()


class SymbolIntegerDivision(Infix):
    def __init__(self, expr):
        super(SymbolIntegerDivision, self).__init__("//", 120, expr)

    def _eval(self):
        return self.first.eval() // self.second.eval()


class SymbolModulo(Infix):
    def __init__(self, expr):
        super(SymbolModulo, self).__init__("%", 120, expr)

    def _eval(self):
        return self.first.eval() % self.second.eval()


class SymbolOr(InfixR):
    def __init__(self, expr):
        super(SymbolOr, self).__init__("or", 30, expr)

    def _eval(self):
        return self.first.eval() or self.second.eval()


class SymbolAnd(InfixR):
    def __init__(self, expr):
        super(SymbolAnd, self).__init__("and", 40, expr)

    def _eval(self):
        return self.first.eval() and self.second.eval()


class SymbolExponent(InfixR):
    def __init__(self, expr):
        super(SymbolExponent, self).__init__("**", 140, expr)

    def _eval(self):
        return self.first.eval() and self.second.eval()


class SymbolNot(Prefix):
    def __init__(self, expr):
        super(SymbolNot, self).__init__("not", 60, expr)
        self.nud_bp = 50

    def led(self, left):
        if self.evaluator.token.id != "in":
            raise SyntaxError("Invalid syntax")
        self.evaluator.advance()
        self.id = "not in"
        self.first = left
        self.second = self.evaluator.expression(60)
        return self

    def _eval(self):
        if self.second is None:
            return not self.first.eval()
        return self.first.eval() not in self.second.eval()


class SymbolAddition(Prefix, Infix):
    def __init__(self, expr):
        super(SymbolAddition, self).__init__("+", 110, expr)

    def _eval(self):
        if self.second is None:
            return +self.first.eval()
        return self.first.eval() + self.second.eval()


class SymbolSubstraction(Prefix, Infix):
    def __init__(self, expr):
        super(SymbolSubstraction, self).__init__("-", 110, expr)

    def _eval(self):
        if self.second is None:
            return -self.first.eval()
        return self.first.eval() - self.second.eval()


class SymbolStartingParenthesis(Prefix, Infix):
    def __init__(self, expr):
        super(SymbolStartingParenthesis, self).__init__("(", 150, expr)

    def led(self, left):
        self.first = left
        self.second = []
        if self.evaluator.token.id != ")":
            while 1:
                self.second.append(self.evaluator.expression())
                if self.evaluator.token.id != ",":
                    break
                self.evaluator.advance(",")
        self.evaluator.advance(")")
        return self

    def nud(self):
        self.first = []
        comma = False
        if self.evaluator.token.id != ")":
            while 1:
                if self.evaluator.token.id == ")":
                    break
                self.first.append(self.evaluator.expression())
                if self.evaluator.token.id != ",":
                    break
                comma = True
                self.evaluator.advance(",")
        self.evaluator.advance(")")
        if not self.first or comma:
            return self # tuple
        else:
            return self.first[0]

    def _eval(self):
        if self.second is None:
            return (x.eval() for x in self.first)
        return self.first.eval()(*[x.eval() for x in self.second])


class SymbolBitwiseNegate(Prefix):
    def __init__(self, expr):
        super(SymbolBitwiseNegate, self).__init__("~", 130, expr)


class SymbolIn(Infix):
    def __init__(self, expr):
        super(SymbolIn, self).__init__("in", 60, expr)

    def _eval(self):
        return self.first.eval() in self.second.eval()


class SymbolChained(Symbol):
    def led(self, left):
        self.first = left
        self.second = self.evaluator.expression(self.lbp + 1)

        if self.evaluator.token.id in ("<", "<=", ">", ">=", "==", "!=", "<>"):
            sym_and = symbol("and")()
            sym_and.first = self

            sym_comp = symbol(self.evaluator.token.id)()

            self.evaluator.advance(self.evaluator.token.id)
            sym_and.second = sym_comp.led(self.second)

            return sym_and
        else:
            return self


class SymbolLessThan(SymbolChained):
    def __init__(self, expr):
        super(SymbolLessThan, self).__init__("<", 60, expr)

    def _eval(self):
        return self.first.eval() < self.second.eval()


class SymbolLessThanOrEqual(SymbolChained):
    def __init__(self, expr):
        super(SymbolLessThanOrEqual, self).__init__("<=", 60, expr)

    def _eval(self):
        return self.first.eval() <= self.second.eval()


class SymbolGreaterThan(SymbolChained):
    def __init__(self, expr):
        super(SymbolGreaterThan, self).__init__(">", 60, expr)

    def _eval(self):
        return self.first.eval() > self.second.eval()


class SymbolGreaterThanOrEqual(SymbolChained):
    def __init__(self, expr):
        super(SymbolGreaterThanOrEqual, self).__init__(">=", 60, expr)

    def _eval(self):
        return self.first.eval() >= self.second.eval()


class SymbolEqual(SymbolChained):
    def __init__(self, expr):
        super(SymbolEqual, self).__init__("==", 60, expr)

    def _eval(self):
        return self.first.eval() == self.second.eval()


class SymbolNotEqual(SymbolChained):
    def __init__(self, expr):
        super(SymbolNotEqual, self).__init__("==", 60, expr)

    def _eval(self):
        return self.first.eval() != self.second.eval()


# symbol (token type) registry
symbol_table = {
    "%": SymbolModulo,
    "//": SymbolIntegerDivision,
    "/": SymbolDivision,
    "*": SymbolMultiplication,
    "**": SymbolExponent,
    ">>": SymbolShiftRight,
    "<<": SymbolShiftLeft,
    "&": SymbolBitwiseAnd,
    "^": SymbolBitwiseXor,
    "|": SymbolBitwiseOr,
    "~": SymbolBitwiseNegate,
    "<>": SymbolNotEqual,
    "!=": SymbolNotEqual,
    "==": SymbolEqual,
    "<": SymbolLessThan,
    "=<": SymbolLessThanOrEqual,
    ">": SymbolGreaterThan,
    ">=": SymbolGreaterThanOrEqual,
    "or": SymbolOr,
    "and": SymbolAnd,
    "(": SymbolStartingParenthesis,

    "not": SymbolNot,
    "in": SymbolIn,
    "is": SymbolIs,
    "if": SymbolIf,
    "~": SymbolBitwiseNegate,
    "+": SymbolAddition,
    "-": SymbolSubstraction,
    "[": lambda self: [x.eval() for x in self.first] if self.second is None else self.first.eval()[self.second.eval()],
    "{": lambda self: {key.eval(): val.eval() for key, val in self.first},
    "(": SymbolStartingParenthesis,

    ".": SymbolReference,
    "(literal)": SymbolLiteral,
    "(name)": SymbolName

}

    infix("in", 60); infix("not", 60) # not in
    infix("is", 60)


    symbol("[", 150)

    # additional behaviour



    symbol("else")


    symbol("]")

    @method("[")
    def led(self, left):
        self.first = left
        self.second = expression()
        advance("]")
        return self

    symbol(")")
    symbol(",")

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

    # displays

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

    def advance(self, id=None):
        if id and self.token.id != id:
            raise SyntaxError("Expected %r" % id)
        self.token = next(self.token_iter)




def mini_eval(expr, ext=None):
    evaluator = Evaluator()
    evaluator.parse(expr)
    return evaluator.eval(ext)


