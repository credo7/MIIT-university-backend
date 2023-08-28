"""
1. Create student (create group if not exist) // Will be deleted after test
2. Create teacher (create group if not exist) // Will be deleted after test
3. Student connects
4. Teacher connects
5. Teacher gets connected_computers
6. Teacher starts pr2 event for connected_computer
7. Student goes through every step ( checkpoints )
8. Student checks results
9. Student checks his works history
"""


def test_pr2_one_student(student_token_func, teacher_token):
    first_student_token = student_token_func(1)
