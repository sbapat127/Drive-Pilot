import pytest
from app.utils import code_generator
from app import create_app
from app.db import get_db, init_db 

@pytest.fixture
def app(tmp_path):
    database = tmp_path / "test.sqlite"
    app = create_app({
        "TESTING": True,
        "DATABASE": str(database)
    })
    with app.app_context():
        init_db()
        yield app


def test_code_is_six_alphanumeric_characters(app):
    db = get_db()
    cursor = db.execute(
    """INSERT INTO account
    (email, password_hash, account_type, first_name, last_name)
    VALUES (?, ?, ?, ?, ?)""",
    ("test@example.com", "test_hash", "INSTRUCTOR", "Test", "Instructor")
    )
    account_id = cursor.lastrowid
    instructor_cursor = db.execute(
        """INSERT INTO instructor
        (account_id, linking_code, adi_number)
        VALUES (?, ?, ?)""",
        (account_id, None, None)
    )
    instructor_id = instructor_cursor.lastrowid
    code = code_generator(instructor_id)
    coderecord = db.execute(
    '''SELECT linking_code
    FROM instructor
    WHERE instructor_id = ?''',(instructor_id,)
    ).fetchone()
    assert coderecord is not None
    assert len(code) == 6
    assert code.isalnum()
    assert coderecord["linking_code"] == code
    
def test_code_retries_when_already_exists(app, monkeypatch):
    db = get_db()
    cursor = db.execute(
    """INSERT INTO account
    (email, password_hash, account_type, first_name, last_name)
    VALUES (?, ?, ?, ?, ?)""",
    ("test@example.com", "test_hash", "INSTRUCTOR", "Test", "Instructor")
    )
    account_id = cursor.lastrowid
    instructor_cursor = db.execute(
        """INSERT INTO instructor
        (account_id, linking_code, adi_number)
        VALUES (?, ?, ?)""",
        (account_id, None, None)
    )
    instructor_id = instructor_cursor.lastrowid
    test = db.execute(
    '''UPDATE instructor 
    SET linking_code = ?
    WHERE instructor_id = ?''', 
    ("ABC123", instructor_id)
        ) 
    db.commit()
    characters = iter("ABC123XYZ789")
    def fake_choice(choices):
        return next(characters)
    monkeypatch.setattr("app.utils.random.choice", fake_choice)
    code = code_generator(instructor_id)
    coderecord = db.execute(
    '''SELECT linking_code
    FROM instructor
    WHERE instructor_id = ?''',(instructor_id,)
    ).fetchone()
    assert coderecord is not None
    assert code == "XYZ789"
    assert coderecord["linking_code"] == code
