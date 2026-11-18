from .db import get_db
import random
import string
upperletters = string.ascii_uppercase
lowerletters = string.ascii_lowercase
digits = string.digits
def code_generator(instructor_id):
	#design a 6 digit code of numbers, lowercase and uppercase letters generated at random
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
			#check that code isn't generated already
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


def link_student_to_instructor(student_id, linking_code):
	db = get_db()
	#get a linking code from instructor's login details (acountid)
	get_instructor_id = db.execute(
	'''SELECT instructor_id
	FROM instructor
	WHERE linking_code = ?''',
		(linking_code,)
	).fetchone()
	#check that the linking code is linked to an instructor
	if get_instructor_id is None:
		raise ValueError ("linking_code doesn't link to an instructor")
	else:
		instructor_id = get_instructor_id[0]
	#update student with instructor's id
	updatestudent = db.execute(
		'''UPDATE student
		SET instructor_id = ?
		WHERE student_id = ?''',
		(instructor_id, student_id,)
	)
	if updatestudent.rowcount == 1:
		db.commit()
		return True
	else:
		return False