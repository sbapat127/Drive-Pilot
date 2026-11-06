"""Pure logic functions: no Flask, no database. Easy to unit test."""
import secrets
import string
 
CODE_ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 6
 
 
def generate_linking_code(exists):
    """Return a unique 6-char code.
 
    `exists` is a function that takes a code and returns True if it is
    already in the database. Passing it in keeps this function testable.
    """
    while True:
        code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))
        if not exists(code):
            return code
 