"""
Tests for SQL parser
"""
import pytest
from src.parser.parser import SimpleParser

def test_parse_create_table():
    """Test CREATE TABLE parsing"""
    parser = SimpleParser()
    
    sql = "CREATE TABLE users (id INT, name VARCHAR(255), age INT)"
    parsed = parser.parse(sql)
    
    assert parsed['command'] == 'CREATE_TABLE'
    assert parsed['table'] == 'users'
    assert len(parsed['columns']) == 3
    assert parsed['columns'][0].name == 'id'
    assert parsed['columns'][1].name == 'name'
    assert parsed['columns'][2].name == 'age'

def test_parse_insert():
    """Test INSERT parsing"""
    parser = SimpleParser()
    
    sql = "INSERT INTO users VALUES (1, 'Alice', 25)"
    parsed = parser.parse(sql)
    
    assert parsed['command'] == 'INSERT'
    assert parsed['table'] == 'users'
    assert parsed['values'] == [1, 'Alice', 25]

def test_parse_select():
    """Test SELECT parsing"""
    parser = SimpleParser()
    
    sql = "SELECT * FROM users"
    parsed = parser.parse(sql)
    
    assert parsed['command'] == 'SELECT'
    assert parsed['table'] == 'users'
    assert parsed['columns'] == ['*']