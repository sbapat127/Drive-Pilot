from app.utils import generate_linking_code
 
 
def test_code_is_six_alphanumeric_characters():
    code = generate_linking_code(lambda c: False)
    assert len(code) == 6 and code.isalnum()
 
 
def test_code_retries_when_taken():
    calls = []
 
    def exists(code):
        calls.append(code)
        return len(calls) < 3  # first two are "taken"
 
    generate_linking_code(exists)
    assert len(calls) == 3