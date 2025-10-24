#!/usr/bin/env python3
"""
SalLangDev Interpreter v1.0
Author: Salman Fareed Chishty
Extension: .salangdev

Keywords:
  set [name] [type] = expression
    digit       -> integer
    one_letter  -> single character
    letters     -> string
  outcome expr -> print output

Usage:
  set a digit = 5
  set name letters = "Salman"
  outcome name
"""

import re
import sys

# ---------- TOKENIZER ----------
TOKEN_SPEC = [
    ('NUMBER',   r'\d+(?:\.\d+)?'),
    ('STRING',   r'"([^"\\]|\\.)*"'),
    ('SET',      r'\bset\b'),
    ('DIGIT',    r'\bdigit\b'),
    ('ONE_LETTER', r'\bone_letter\b'),
    ('LETTERS',  r'\bletters\b'),
    ('OUTCOME',  r'\boutcome\b'),
    ('ID',       r'[A-Za-z_][A-Za-z0-9_]*'),
    ('ASSIGN',   r'='),
    ('PLUS',     r'\+'),
    ('MINUS',    r'-'),
    ('MUL',      r'\*'),
    ('DIV',      r'/'),
    ('LPAREN',   r'\('),
    ('RPAREN',   r'\)'),
    ('NEWLINE',  r'\n'),
    ('SKIP',     r'[ \t]+'),
    ('COMMENT',  r'//.*'),
]

TOKEN_REGEX = re.compile('|'.join(f'(?P<{n}>{p})' for n, p in TOKEN_SPEC))

def tokenize(code):
    tokens = []
    for m in TOKEN_REGEX.finditer(code):
        kind = m.lastgroup
        value = m.group()
        if kind == 'SKIP' or kind == 'COMMENT':
            continue
        if kind == 'NUMBER':
            value = int(value) if value.isdigit() else float(value)
        elif kind == 'STRING':
            value = bytes(value[1:-1], "utf-8").decode("unicode_escape")
        tokens.append((kind, value))
    tokens.append(('EOF', None))
    return tokens


# ---------- PARSER ----------
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos][0]

    def eat(self, expected=None):
        token = self.tokens[self.pos]
        if expected and token[0] != expected:
            raise SyntaxError(f"Expected {expected}, got {token}")
        self.pos += 1
        return token

    def parse(self):
        statements = []
        while self.peek() != 'EOF':
            if self.peek() == 'NEWLINE':
                self.eat('NEWLINE')
                continue
            statements.append(self.statement())
        return ('PROGRAM', statements)

    def statement(self):
        tok = self.peek()
        if tok == 'SET':
            return self.set_statement()
        elif tok == 'OUTCOME':
            self.eat('OUTCOME')
            expr = self.expression()
            return ('OUTCOME', expr)
        elif tok == 'ID':
            name = self.eat('ID')[1]
            self.eat('ASSIGN')
            expr = self.expression()
            return ('ASSIGN', name, expr)
        else:
            raise SyntaxError(f"Unexpected token {tok}")

    def set_statement(self):
        self.eat('SET')
        name = self.eat('ID')[1]
        var_type = None
        if self.peek() in ('DIGIT', 'ONE_LETTER', 'LETTERS'):
            var_type = self.eat()[0]
        self.eat('ASSIGN')
        expr = self.expression()
        return ('SET', name, var_type, expr)

    def expression(self):
        node = self.term()
        while self.peek() in ('PLUS', 'MINUS'):
            op = self.eat()[0]
            right = self.term()
            node = (op, node, right)
        return node

    def term(self):
        node = self.factor()
        while self.peek() in ('MUL', 'DIV'):
            op = self.eat()[0]
            right = self.factor()
            node = (op, node, right)
        return node

    def factor(self):
        tok = self.peek()
        if tok == 'NUMBER':
            return ('NUMBER', self.eat('NUMBER')[1])
        elif tok == 'STRING':
            return ('STRING', self.eat('STRING')[1])
        elif tok == 'ID':
            return ('VAR', self.eat('ID')[1])
        elif tok == 'LPAREN':
            self.eat('LPAREN')
            expr = self.expression()
            self.eat('RPAREN')
            return expr
        else:
            raise SyntaxError(f"Unexpected token {tok}")


# ---------- INTERPRETER ----------
class Interpreter:
    def __init__(self):
        self.env = {}

    def cast(self, value, vtype):
        if vtype == 'DIGIT':
            return int(value)
        elif vtype == 'ONE_LETTER':
            if isinstance(value, str) and len(value) == 1:
                return value
            raise ValueError("Expected a single character")
        elif vtype == 'LETTERS':
            return str(value)
        return value

    def eval(self, node):
        t = node[0]

        if t == 'PROGRAM':
            for stmt in node[1]:
                self.eval(stmt)

        elif t == 'SET':
            name, vtype, expr = node[1], node[2], node[3]
            value = self.eval(expr)
            if vtype:
                value = self.cast(value, vtype)
            self.env[name] = value

        elif t == 'ASSIGN':
            name, expr = node[1], node[2]
            value = self.eval(expr)
            self.env[name] = value

        elif t == 'OUTCOME':
            val = self.eval(node[1])
            print(val)

        elif t == 'NUMBER' or t == 'STRING':
            return node[1]

        elif t == 'VAR':
            name = node[1]
            if name not in self.env:
                raise NameError(f"Variable '{name}' not defined")
            return self.env[name]

        elif t == 'PLUS':
            return self.eval(node[1]) + self.eval(node[2])
        elif t == 'MINUS':
            return self.eval(node[1]) - self.eval(node[2])
        elif t == 'MUL':
            return self.eval(node[1]) * self.eval(node[2])
        elif t == 'DIV':
            return self.eval(node[1]) / self.eval(node[2])

        else:
            raise RuntimeError(f"Unknown node: {t}")


# ---------- RUNTIME ----------
def run_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        code = f.read()
    tokens = tokenize(code)
    parser = Parser(tokens)
    ast = parser.parse()
    interpreter = Interpreter()
    interpreter.eval(ast)

def main():
    if len(sys.argv) < 2:
        print("Usage: salangdev <file.salangdev>")
        sys.exit(1)
    run_file(sys.argv[1])

if __name__ == "__main__":
    main()