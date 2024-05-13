import logging
import copy
from typing import List

import pymongo
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pymongo.database import Database
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from db.mongo import get_db, CollectionNames
import schemas
from services import oauth2, utils
from services.utils import normalize_mongo

router = APIRouter(tags=['Users'], prefix='/users')

logger = logging.getLogger(__name__)


@router.get('', status_code=status.HTTP_200_OK, response_model=List[schemas.UserOut])
async def get_users(
    search: str = Query(None, description='Search by first name, last name, or surname'),
    group_id: str = Query(None, description='Filter by group ID'),
    group_name: str = Query(None, description='Filter by group name'),
    sort: str = Query(None, description='AZ or ZA'),
    _current_user: schemas.FullUser = Depends(oauth2.get_current_user),
):
    found_users = utils.search_users_by_group(
        schemas.UserSearch(search=search, group_id=group_id, group_name=group_name),
        sort
    )
    return normalize_mongo(found_users, schemas.UserOut)


@router.patch('/edit', status_code=status.HTTP_200_OK, response_model=schemas.UserOut)
async def edit(
    user_update: schemas.UserUpdate,
    current_user: schemas.FullUser = Depends(oauth2.get_current_user),
    db: Database = Depends(get_db),
):
    try:
        group_filter = {}
        if user_update.group_id:
            group_filter['_id'] = ObjectId(user_update.group_id)
        if user_update.group_name:
            group_filter['name'] = user_update.group_name

        if group_filter:
            group_db = db[CollectionNames.GROUPS.value].find_one(group_filter)
            if not group_db:
                raise HTTPException(status.HTTP_404_NOT_FOUND, 'Группа не найдена')
            user_update.group_id = str(group_db['_id'])
            user_update.group_name = group_db['name']

        user_update_dict = {}
        required_fields = ['first_name', 'last_name', 'surname', 'student_id', 'group_id', 'group_name']
        required_to_change = current_user.fix_for_approve_fields
        for field, value in user_update.dict().items():
            if field in required_fields and value is not None:

                if required_to_change:
                    if 'group' in field and 'group' in required_to_change:
                        required_to_change.remove('group')
                    if field in required_to_change:
                        required_to_change.remove(field)

                user_update_dict[field] = value

        if required_to_change:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=jsonable_encoder(
                    {
                        'detail': 'Заполнены не все требуемые поля!',
                        'rest_fields': [field if field != 'group' else 'group_id' for field in required_to_change],
                    }
                ),
            )

        user_db = db[CollectionNames.USERS.value].find_one_and_update(
            {'_id': ObjectId(current_user.id)},
            {'$set': {**user_update_dict, 'fix_for_approve_fields': None}},
            return_document=pymongo.ReturnDocument.AFTER,
        )

        logger.info(f'user updated {user_db}')

        return normalize_mongo(user_db, schemas.UserOut)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{str(e)}')


@router.post('/approve/{user_id}', status_code=status.HTTP_200_OK, response_model=schemas.UserOut)
async def approve_user(
    user_id: str,
    _current_teacher: schemas.UserOut = Depends(oauth2.get_current_teacher),
    db: Database = Depends(get_db),
):
    try:
        user_db = db[CollectionNames.USERS.value].find_one_and_update(
            {'_id': ObjectId(user_id)}, {'$set': {'approved': True}}, return_document=pymongo.ReturnDocument.AFTER
        )

        if not user_db:
            raise HTTPException(status_code=404, detail='Кандидат на апрув не найден')

        logger.info(f'user approved {user_db}')

        return normalize_mongo(user_db, schemas.UserOut)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{str(e)}')


@router.post('/request-edits', status_code=status.HTTP_200_OK)
async def request_edits(
    body: schemas.RequestEditsBody,
    _current_teacher: schemas.UserOut = Depends(oauth2.get_current_teacher),
    db: Database = Depends(get_db),
):
    fix_for_approve_fields = [
        field_name for field_name, field_value in body.__dict__.items() if field_value and field_name != 'user_id'
    ]

    if len(fix_for_approve_fields) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Поля не заданы.')

    user_db = db[CollectionNames.USERS.value].find_one_and_update(
        {'_id': ObjectId(body.user_id), 'approved': False}, {'$set': {'fix_for_approve_fields': fix_for_approve_fields}}
    )

    if not user_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Студент не найден либо уже подтвержден')


@router.get('/check-approval', response_model=schemas.CheckApprovalResponse)
async def check_approval(current_user: schemas.FullUser = Depends(oauth2.get_current_user),):
    if current_user.approved:
        return schemas.CheckApprovalResponse(is_approved=True)
    if current_user.fix_for_approve_fields:
        return schemas.CheckApprovalResponse(is_approved=False, fields_to_be_fixed=current_user.fix_for_approve_fields)
    return schemas.CheckApprovalResponse(is_approved=False)


@router.get('/unapproved', status_code=status.HTTP_200_OK, response_model=List[schemas.UserToApprove])
async def get_unapproved_users(
    group_id: str = None,
    _current_teacher: schemas.UserOut = Depends(oauth2.get_current_teacher),
    db: Database = Depends(get_db),
):
    try:
        filter = {'approved': False, 'fix_for_approve_fields': None}
        if group_id:
            filter['group_id'] = group_id
        unapproved_users_db = db[CollectionNames.USERS.value].find(filter)
        return normalize_mongo(unapproved_users_db, schemas.UserToApprove)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{str(e)}')


# @router.post('/forgot-password')
# async def forgot_password(
#     body: schemas.ForgotPasswordBody, db: Database = Depends(get_db),
# ):
#     new_password = utils.generate_password()
#
# hash_password = utils.hash(new_password)
#
#     user_db = db[CollectionNames.USERS.value].find_one_and_update(
#         {'username': body.username, 'student_id': body.student_id}, {'$set': {'password': hash_password}}
#     )
#
#     if user_db is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Пользователь с таким данными не найден')
#
#     return schemas.ForgotPasswordResponse(username=body.username, new_password=new_password)

@router.post('/change-password', status_code=status.HTTP_200_OK, response_model=schemas.UserOut)
async def change_password(body: schemas.ChangePasswordBody, db: Database = Depends(get_db)):
    user_db = db[CollectionNames.USERS.value].find_one({
        "last_name": body.last_name.capitalize(),
        "student_id": body.student_id.upper()
    })

    hash_password = utils.hash(body.new_password)

    if user_db is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    user = normalize_mongo(user_db, schemas.UserOut)

    db[CollectionNames.USERS.value].update_one({"_id": ObjectId(user.id)}, {"$set": {"password": hash_password}})

    return user


# @router.patch(
#     '/change-password/{user_id}', status_code=status.HTTP_200_OK, response_model=schemas.UserCredentials,
# )
# async def change_password(
#     user_id: str,
#     _current_teacher: schemas.UserOut = Depends(oauth2.get_current_teacher),
#     db: Database = Depends(get_db),
# ):
#     try:
#         new_password = utils.generate_password()
#
#         hash_password = utils.hash(new_password)
#
#         user_db = db[CollectionNames.USERS.value].find_one_and_update(
#             {'_id': ObjectId(user_id)}, {'$set': {'password': hash_password}}
#         )
#
#         if not user_db:
#             raise HTTPException(status_code=404, detail='Пользователь не найден')
#
#         logger.info(f"password change for user with id {user_db['_id']}")
#
#         return schemas.UserCredentials(username=user_db['username'], password=new_password)
#     except Exception as e:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{str(e)}')


@router.get('/{id}', status_code=status.HTTP_200_OK, response_model=schemas.GetUserResponse)
async def get_user(id: str, db: Database = Depends(get_db)):

    user_db = db[CollectionNames.USERS.value].find_one({'_id': ObjectId(id)})

    if not user_db:
        raise HTTPException(status_code=404, detail='User not found')

    user = normalize_mongo(user_db, schemas.UserOut)

    history = []

    events = db[CollectionNames.EVENTS.value].find(
        {
            'is_finished': True,
            'users_ids': {'$in': [user.id]},
            '$or': [
                {"event_mode": "CONTROL"},
                {"$and": [{"event_mode": "CLASS"}, {"test_results": {"$exists": True}}]}
            ]
        }
    ).sort('created_at', -1)

    for event_db in events:
        event = normalize_mongo(event_db, schemas.EventInfo)

        print({"event_id": event.id, "type": event.event_type, "event_mode": event.event_mode})
        history_element = schemas.UserHistoryElement(
            id=event.id,
            type=event.event_type,
            mode=event.event_mode,
            created_at=event.created_at,
            finished_at=event.finished_at
        )

        if event.event_type == schemas.EventType.PR1:
            if event.event_mode == schemas.EventMode.CLASS:
                for step in event.steps_results:
                    if step.step_code == "DESCRIBE_OPTION":
                        history_element.description = step.description
                        break

                incoterms = {inc: schemas.CorrectOrError.CORRECT for inc in list(schemas.Incoterm)}
                for step in event.steps_results:
                    if user.id in step.users_ids:
                        if step.fails >= 3:
                            incoterms[step.incoterm] = schemas.CorrectOrError.ERROR

                best = schemas.TestCorrectsAndErrors(correct=0, error=20)
                for test_result in event.test_results:
                    current = schemas.TestCorrectsAndErrors(correct=0, error=0)
                    for step in test_result:
                        if step.fails >= 3:
                            current.error += 1
                        else:
                            current.correct += 1
                    if current.correct > best.correct:
                        best = copy.deepcopy(current)
            else:
                incoterms = {
                    event.steps_results[0].incoterm: schemas.CorrectOrError.CORRECT,
                    event.steps_results[1].incoterm: schemas.CorrectOrError.CORRECT,
                    event.steps_results[2].incoterm: schemas.CorrectOrError.CORRECT
                }
                for step in event.steps_results[:3]:
                    if step.fails >= 3:
                        incoterms[step.incoterm] = schemas.CorrectOrError.ERROR

                best = schemas.TestCorrectsAndErrors(correct=0, error=0)
                for step in event.steps_results[3:]:
                    if step.fails > 0:
                        best.error += 1
                    else:
                        best.correct += 1

                fails_points_mapping = {
                    0:3,
                    1:2,
                    2:1,
                    3:0
                }

                incoterm_points_mapping = {
                    event.steps_results[0].incoterm: fails_points_mapping[event.steps_results[0].fails],
                    event.steps_results[1].incoterm: fails_points_mapping[event.steps_results[1].fails],
                    event.steps_results[2].incoterm: fails_points_mapping[event.steps_results[2].fails]
                }

                history_element.incoterm_points_mapping = incoterm_points_mapping


            history_element.incoterms = incoterms
            history_element.test = best
            history.append(history_element)

    return schemas.GetUserResponse(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        surname=user.surname,
        username=user.username,
        group_id=user.group_id,
        group_name=user.group_name,
        history=history,
    )


@router.delete('/{user_id}', status_code=status.HTTP_200_OK, response_model=schemas.ResponseMessage)
async def delete_user(
    user_id: str,
    _current_teacher: schemas.UserOut = Depends(oauth2.get_current_teacher),
    db: Database = Depends(get_db),
):
    deleted = db[CollectionNames.USERS.value].delete_one({'_id': ObjectId(user_id)})

    if deleted.deleted_count < 1:
        raise HTTPException(status_code=404, detail='Пользователь не найден')

    logger.info(f'user with id {user_id} was deleted')

    return {'message': 'Deleted'}


@router.post('/make-teacher', status_code=status.HTTP_200_OK)
async def make_teacher(
    user_id: str, db: Database = Depends(get_db),
):
    db[CollectionNames.USERS.value].update_one(
        {'_id': ObjectId(user_id)}, {'$set': {'approved': True, 'role': 'TEACHER'}}
    )
