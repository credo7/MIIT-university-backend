from constants.pr1_control_info import pr1_control_info
from constants.practice_one_info import practice_one_info
from schemas import TestQuestionPR1

# doc = "ПР1 Контрольная тестовые вопросы\n\n"
doc = "ПР1 Класс тестовые вопросы\n\n"

for i, q in enumerate(
    [
*practice_one_info.classic_test_questions.first_block,
*practice_one_info.classic_test_questions.second_block,
*practice_one_info.classic_test_questions.third_block
    ]
):
    q:TestQuestionPR1
    doc += f"Вопрос #{i+1}\n{q.question}\n"
    doc += f"Верный(-ые) ответ(ы):\n"
    for o in [o for o in q.options if o.is_correct]:
        doc += f"- {o.value}\n"
    doc += f"Неверный(-ые) ответ(ы):\n"
    for o in [o for o in q.options if not o.is_correct]:
        doc += f"-{o.value}\n"
    doc += "\n"

with open('pr1_class_questions.txt', 'w', encoding='utf-8') as file:
  file.write(str(doc))