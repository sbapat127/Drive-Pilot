import pytest
from app.utils import code_generator
from app import create_app
from app.db import get_db, init_db 
from app.utils import link_student_to_instructor

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
    (username, password_hash, account_type, first_name, last_name)
    VALUES (?, ?, ?, ?, ?)""",
    ("example_username", "test_hash", "INSTRUCTOR", "Test", "Instructor")
    )
    account_id = cursor.lastrowid
    instructor_cursor = db.execute(
        """INSERT INTO instructor
        (account_id, linking_code, adi_number)
        VALUES (?, ?, ?)""",
        (account_id, None, None)
    )
    instructor_id = instructor_cursor.lastrowid
    #calls the code generator function
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
    (username, password_hash, account_type, first_name, last_name)
    VALUES (?, ?, ?, ?, ?)""",
    ("example_username", "test_hash", "INSTRUCTOR", "Test", "Instructor")
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

def test_code_generator_rejects_invalid_instructor_id(app):
    db = get_db()
    cursor = db.execute(
    """INSERT INTO account
    (username, password_hash, account_type, first_name, last_name)
    VALUES (?, ?, ?, ?, ?)""",
    ("example_username", "test_hash", "INSTRUCTOR", "Test", "Instructor")
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
    with pytest.raises(ValueError):
        code_generator(-1)

def test_successful_linking(app):
    db = get_db()
    cursor = db.execute(
    """INSERT INTO account
    (username, password_hash, account_type, first_name, last_name)
    VALUES (?, ?, ?, ?, ?)""",
    ("example_username", "test_hash", "INSTRUCTOR", "Test", "Instructor")
    )
    account_id = cursor.lastrowid
    instructor_cursor = db.execute(
        """INSERT INTO instructor
        (account_id, linking_code, adi_number)
        VALUES (?, ?, ?)""",
        (account_id, "ABC123", None)
    )
    instructor_id = instructor_cursor.lastrowid
    cursor = db.execute(
    """INSERT INTO account
    (username, password_hash, account_type, first_name, last_name)
    VALUES (?, ?, ?, ?, ?)""",
    ("test_student", "teststudent_hash", "STUDENT", "John", "Doe",)
    )
    student_account_id = cursor.lastrowid
    student_cursor = db.execute(
        '''INSERT INTO student
        (account_id, instructor_id, transmission_type)
        VALUES (?, ?, ?)''',
        (student_account_id, None, "MANUAL")
    )
    student_id = student_cursor.lastrowid
    result = link_student_to_instructor(student_id, "ABC123")
    instructorcheck = db.execute(
        '''SELECT instructor_id
        FROM student
        WHERE student_id = ?''', (student_account_id,)
    ).fetchone()
    assert result is True

def test_link_student_rejects_invalid_linking_code(app):
    db = get_db()
    cursor = db.execute(
    """INSERT INTO account
    (username, password_hash, account_type, first_name, last_name)
    VALUES (?, ?, ?, ?, ?)""",
    ("test_student", "teststudent_hash", "STUDENT", "John", "Doe")
    )
    account_id = cursor.lastrowid
    student_cursor = db.execute(
        """INSERT INTO student
        (account_id, instructor_id, transmission_type)
        VALUES (?, ?, ?)""",
        (account_id, None, "MANUAL")
    )
    student_id = student_cursor.lastrowid
    db.commit()
    with pytest.raises(ValueError):
        link_student_to_instructor(student_id, "INVALID")
    student_record = db.execute(
    '''SELECT instructor_id
    FROM student
    WHERE student_id = ?''',
    (student_id,)
    ).fetchone()
    assert student_record["instructor_id"] is None