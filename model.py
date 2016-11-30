import operator
import pytest


class Scope(object):

    def __init__(self, parent=None):
        self.dict = dict()
        self.parent = parent

    def __getitem__(self, item):
        if item in self.dict:
            return self.dict[item]
        if self.parent:
            return self.parent[item]
        else:
            raise Exception

    def __setitem__(self, key, value):
        self.dict[key] = value


class Number:

    def __init__(self, value):
        self.value = int(value)

    def evaluate(self, scope):
        return self


class Reference:

    def __init__(self, name):
        self.name = name

    def evaluate(self, scope):
        return scope[self.name]


class UnaryOperation:
    ops = {"-": operator.neg,
           "!": operator.not_}

    def __init__(self, op, expr):
        self.op = op
        self.expr = expr

    def evaluate(self, scope):
        a = self.expr.evaluate(scope).value
        return Number(self.ops[self.op](a))


class BinaryOperation:
    ops = {"+": operator.add,
           "-": operator.sub,
           "*": operator.mul,
           "/": operator.floordiv,
           "%": operator.mod,
           "==": operator.eq,
           "!=": operator.ne,
           "<": operator.lt,
           ">": operator.gt,
           "<=": operator.le,
           ">=": operator.ge,
           "&&": lambda x, y: bool(x and y),
           "||": lambda x, y: bool(x or y)}

    def __init__(self, lhs, op, rhs):
        self.lhs = lhs
        self.rhs = rhs
        self.op = op

    def evaluate(self, scope):
        l = self.lhs.evaluate(scope).value
        r = self.rhs.evaluate(scope).value
        return Number(self.ops[self.op](l, r))


class Function:

    def __init__(self, args, body):
        self.body = body
        self.args = args

    def evaluate(self, scope):
        last = Number(0)
        for x in self.body:
            last = x.evaluate(scope)
        return last


class FunctionDefinition:

    def __init__(self, name, function):
        self.name = name
        self.func = function

    def evaluate(self, scope):
        scope[self.name] = self.func
        return self.func


class FunctionCall:

    def __init__(self, fun_expr, args):
        self.args = args
        self.fun_expr = fun_expr

    def evaluate(self, scope):
        func = self.fun_expr.evaluate(scope)
        call_scope = Scope(scope)
        results = [x.evaluate(scope) for x in self.args]
        for i, x in enumerate(func.args):
            call_scope[x] = results[i]
        return func.evaluate(call_scope)


class Conditional:

    def __init__(self, condition, if_true, if_false=None):
        self.condition = condition
        self.if_true = if_true
        self.if_false = if_false

    def evaluate(self, scope):
        val = self.condition.evaluate(scope).value
        if val and self.if_true:
            body = self.if_true
        elif self.if_false:
            body = self.if_false
        else:
            body = []
        res = None
        for stmt in body:
            res = stmt.evaluate(scope)
        return res


class Print:

    def __init__(self, expr):
        self.expr = expr

    def evaluate(self, scope):
        a = self.expr.evaluate(scope)
        print(a.value)
        return a


class Read:

    def __init__(self, name):
        self.name = name

    def evaluate(self, scope):
        a = int(input())
        scope[self.name] = Number(a)
        return Number(a)


@pytest.fixture(scope="function")
def scope():
    return Scope()


def test_scope(scope):
    scope["bar"] = Number(10)
    child = Scope(scope)
    assert child["bar"].value == 10
    child["bar"] = Number(20)
    assert child["bar"].value == 20
    assert type(child["bar"]) == Number


def test_scope_missing(scope):
    with pytest.raises(Exception):
        scope['missing']


def test_function_call(scope):
    scope["foo"] = Function(('hello', 'world'),
                            [Print(BinaryOperation(Reference('hello'),
                                                   '+',
                                                   Reference('world')))])
    body = [Number(5), UnaryOperation('-', Number(3))]
    assert isinstance(FunctionCall(FunctionDefinition('foo', scope['foo']),
                                   body).evaluate(scope), Number)


def test_binary_operation(scope):
    assert BinaryOperation(Number(5), "&&", Number(0)
                           ).evaluate(scope).value == 0
    assert BinaryOperation(Number(5), "&&", Number(-2)
                           ).evaluate(scope).value == 1


def test_unary_operation(scope):
    assert UnaryOperation("!", Number(5)).evaluate(scope).value == 0
