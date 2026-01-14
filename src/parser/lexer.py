"""
Simple SQL lexer/tokenizer
"""
import re
from typing import List, Tuple

class Token:
    """Represents a SQL token"""
    def __init__(self, type: str, value: str):
        self.type = type
        self.value = value
    
    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)})"

class Lexer:
    """Simple lexer for SQL"""
    
    # Token patterns
    patterns = [
        ('NUMBER', r'\d+(\.\d*)?'),
        ('STRING', r"'[^']*'"),
        ('IDENTIFIER', r'[a-zA-Z_][a-zA-Z0-9_]*'),
        ('PAREN_OPEN', r'\('),
        ('PAREN_CLOSE', r'\)'),
        ('COMMA', r','),
        ('SEMICOLON', r';'),
        ('OPERATOR', r'[=<>!]+'),
        ('WHITESPACE', r'\s+'),
    ]
    
    def __init__(self):
        self.pattern = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in self.patterns)
    
    def tokenize(self, text: str) -> List[Token]:
        """Convert SQL string to tokens"""
        tokens = []
        for match in re.finditer(self.pattern, text):
            kind = match.lastgroup
            value = match.group()
            
            if kind == 'WHITESPACE':
                continue
            elif kind == 'STRING':
                value = value[1:-1]  # Remove quotes
            
            tokens.append(Token(kind, value))
        
        return tokens