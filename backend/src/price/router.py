from fastapi import APIRouter, Query

from . import service


router = APIRouter(prefix="/api/v1/prices")


@router.get("/necessities-price")
def read_necessities_prices(category=Query(None), commodity=Query(None)):
    return service.fetch_necessities_prices(category, commodity)