from .db import get_db
import random
import string
upperletters = string.ascii_uppercase
lowerletters = string.ascii_lowercase
digits = string.digits
def code_generator(instructor_id):
	codeassigned = False
	db = get_db()
	instructor = db.execute(
    '''SELECT instructor_id 
	FROM instructor 
	WHERE instructor_id = ?''',
    (instructor_id,)).fetchone()
	if instructor is None:
		raise ValueError("Instructor_id doesn't exist")
	else:
		while codeassigned == False:
			code = ""
			choices = upperletters + lowerletters + digits 
			for i in range (0,6):
				randvalue = random.choice(choices)
				code = code + randvalue
			instructor_pairing_code = code
			result = db.execute(
			'''SELECT instructor_id 
			FROM instructor 
			WHERE linking_code = ?''',
			(instructor_pairing_code,)
			).fetchone()
			if result is None:
				updatecode = db.execute(
				'''UPDATE instructor
				SET linking_code = ?
				WHERE instructor_id = ?;''', (instructor_pairing_code, instructor_id,))
				if updatecode.rowcount == 1:
					db.commit()
					codeassigned = True
					return instructor_pairing_code