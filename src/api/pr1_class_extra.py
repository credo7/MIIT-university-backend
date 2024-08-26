import logging
from bson import ObjectId

from fastapi import APIRouter, status, Depends, HTTPException
from pymongo.database import Database

from db.mongo import get_db, CollectionNames
from schemas import (
    SelectLogist,
    EventType,
    EventMode,
    Incoterm,
    PR1ClassChosenBet,
    PR1ClassEvent,
    BetsRolePR1,
    PR1ClassBetType,
    IncotermInfo,
    IncotermInfoSummarize,
)
from services.utils import normalize_mongo

router = APIRouter(tags=['Lessons'], prefix='/pr1-class-extra')

logger = logging.getLogger(__name__)


@router.post('/select-logist', status_code=status.HTTP_200_OK)
async def select_logist(
    select_logist_dto: SelectLogist, db: Database = Depends(get_db),
):
    event_db = db[CollectionNames.EVENTS.value].find_one({'_id': ObjectId(select_logist_dto.event_id)})

    if not event_db:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Event не найден')

    if not event_db['event_type'] == EventType.PR1.value or not event_db['event_mode'] == EventMode.CLASS.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Тип работы {event_db['event_type']}. mode работы {event_db['event_mode']}",
        )

    db[CollectionNames.EVENTS.value].update_one(
        {'_id': event_db['_id'],}, {'$set': {'chosen_logist_index': select_logist_dto.logist_index}}
    )


@router.get('/delivery-options/', status_code=status.HTTP_200_OK, response_model=dict[Incoterm, IncotermInfoSummarize])
async def get_comparison_options(
    event_id: str, db: Database = Depends(get_db),
):
    event_db = db[CollectionNames.EVENTS.value].find_one({'_id': event_id})

    if not event_db['event_type'] == EventType.PR1.value or not event_db['event_mode'] == EventMode.CLASS.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Тип работы {event_db['event_type']}. mode работы {event_db['event_mode']}",
        )

    pr1_class_event = normalize_mongo(event_db, PR1ClassEvent)

    if pr1_class_event.delivery_options is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'Запрашивались ли comparison-options до?')

    delivery_options = {key: IncotermInfoSummarize(**value).dict() for key, value in pr1_class_event.delivery_options}

    return delivery_options


@router.get('/comparison-options/', status_code=status.HTTP_200_OK, response_model=dict[Incoterm, IncotermInfo])
async def get_comparison_options(
    event_id: str, db: Database = Depends(get_db),
):
    event_db = db[CollectionNames.EVENTS.value].find_one({'_id': event_id})

    if not event_db['event_type'] == EventType.PR1.value or not event_db['event_mode'] == EventMode.CLASS.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Тип работы {event_db['event_type']}. mode работы {event_db['event_mode']}",
        )

    pr1_class_event = normalize_mongo(event_db, PR1ClassEvent)

    incoterms_mapping = {}
    for incoterm in list(Incoterm):
        chosen_bets = []
        for bet in pr1_class_event.bets:
            chosen_by = None
            bet_type = None

            if incoterm in bet.bet_pattern.buyer:
                bet_type = PR1ClassBetType.BUYER.value
                chosen_by = BetsRolePR1.BUYER.value
            elif incoterm in bet.bet_pattern.seller:
                bet_type = PR1ClassBetType.SELLER.value
                chosen_by = BetsRolePR1.SELLER.value
            elif incoterm in bet.bet_pattern.common:
                bet_type = PR1ClassBetType.COMMON.value
                if incoterm in pr1_class_event.common_bets_ids_chosen_by_seller:
                    if bet.id in pr1_class_event.common_bets_ids_chosen_by_seller[incoterm]:
                        chosen_by = BetsRolePR1.SELLER.value
                    else:
                        chosen_by = BetsRolePR1.BUYER.value
                else:
                    chosen_by = BetsRolePR1.BUYER.value
            if chosen_by is not None or bet_type is not None:
                chosen_bet = PR1ClassChosenBet(
                    id=bet.id, name=bet.name, rate=bet.rate, chosen_by=chosen_by, type=bet_type
                )

                chosen_bets.append(chosen_bet)

        agreement_price_seller = pr1_class_event.product_price
        delivery_price_buyer = 0

        for bet in chosen_bets:
            if bet.chosen_by == BetsRolePR1.BUYER.value:
                delivery_price_buyer += bet.rate
            else:
                agreement_price_seller += bet.rate

        incoterm_info = IncotermInfo(
            bets=chosen_bets,
            agreement_price_seller=agreement_price_seller,
            delivery_price_buyer=delivery_price_buyer,
            total=agreement_price_seller + delivery_price_buyer,
        )

        incoterms_mapping[incoterm] = incoterm_info

        incoterms_mapping_json = {key: value.dict() for key, value in incoterms_mapping.items()}

        db[CollectionNames.EVENTS.value].update_one(
            {'_id': ObjectId(pr1_class_event.id)}, {'$set': {'delivery_options': incoterms_mapping_json}}
        )

    return incoterms_mapping
