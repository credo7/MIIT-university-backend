from fastapi import APIRouter

router = APIRouter(tags=['Dev'], prefix='/dev')


@router.get('/test-tg-error-logging')
async def test_tg_error_logging():
    raise Exception("Special Exception")
