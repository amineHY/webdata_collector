from fastapi import APIRouter, Depends, HTTPException
from services.crawler import handle_crawler_request
from core.logging import setup_logging
from utils.misc import QueryParams

# Initialize logger
logger = setup_logging()

# Initialize the router
router = APIRouter()


# Define a simple root endpoint for testing purposes
@router.get("/")
def root() -> dict:
    """
    Returns a JSON response with the message "Hello, World!".

    Returns:
        dict: JSON response with the message "Hello, World!".
    """
    return {"message": "Hello, World!"}


# Define the endpoint for the crawler
@router.get("/crawler/")
async def crawler(params: QueryParams = Depends()):

    try:
        logger.info("Crawler request received with params: %s", params)
        return await handle_crawler_request(params)

    except Exception as e:
        logger.error("Error handling crawler request: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))
