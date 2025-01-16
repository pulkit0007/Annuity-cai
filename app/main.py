import signal
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.routes import chat, health

# from app.routes.chat import BotResponseProcessor
from chatbot.response_processor import BotResponseProcessor
from app.services.redis_app_state import AppState
from app.services.pdf_handler import PDFHandler
from app.logger import get_logger
import os
import sys
from dotenv import load_dotenv
from contextlib import asynccontextmanager

from app.config import REDIS_PREFIX, REDIS_TOPIC

import uvicorn

# Load environment variables from .env file
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

pdf_handler = PDFHandler()
app_state = AppState()

logger = get_logger("check pdf files")

async def check_new_pdfs():
    """Asynchronous task to check for new PDF files periodically."""
    while True:
        try:
            logger.info("Checking for new PDF files...")
            count, pdf_files = pdf_handler.get_pdf_count_local()
            if count:
                print("The count of pdf files are: ", count)
                logger.info(f"New PDF files counts are: {count}")
            else:
                count = 0
                print("The count of pdf files are: ", count)
                logger.info("No new PDF files found.")
        except Exception as e:
            logger.error(f"Error checking for new PDFs: {str(e)}")
        await asyncio.sleep(10)  # Wait for 10 seconds before checking again


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await app_state.initialize_redis()

        async def process_message(msg: dict) -> None:
            try:
                app_state.logger.info(f"Processing message: {msg}")
                print("Inside lifespan process_message")
                processor = BotResponseProcessor(
                    query=msg["query"],
                    adviser_id=msg["adviser_id"],
                    chat_id=msg["chat_id"],
                )
                await processor.process()
            except Exception as e:
                app_state.logger.error(f"Error processing message: {e}", exc_info=True)

        topic = f'{REDIS_PREFIX}_{REDIS_TOPIC}'
        logger.info(f"topic: {topic}")
        app_state.subscription_task = asyncio.create_task(
            app_state.pubsub_manager.subscribe(topic, process_message)
        )
        app_state.logger.info(f"Subscribed to '{topic}' channel")
        yield

    except Exception as e:
        app_state.logger.error(f"Startup error: {e}", exc_info=True)
        raise
    finally:
        await app_state.cleanup()

# Initialize the FastAPI app
app = FastAPI(title="AI Chat Bot API",
    description="API for processing chat bot queries",
    version="1.0.0",
    lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, use specific domains in production
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

# Include routes for handling different parts of the application
app.include_router(chat.router, prefix="/cai", tags=["Chat"])
app.include_router(health.router, prefix="/cai")


@app.on_event("startup")
async def startup_event():
    """Startup logic for the FastAPI server."""
    try:
        logger.info("FastAPI server started.")
        asyncio.create_task(check_new_pdfs())  # Start background task
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start the application.")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown logic for the FastAPI server."""
    try:
        logger.info("FastAPI server stopped.")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to stop the application.")

# Gracefully handle shutdown on CTRL+C
def shutdown_signal_handler(signal, frame):
    logger.info("Received shutdown signal. Exiting gracefully...")
    loop = asyncio.get_event_loop()
    loop.stop()

# Attach signal handlers
signal.signal(signal.SIGINT, shutdown_signal_handler)  # Handle CTRL+C
signal.signal(signal.SIGTERM, shutdown_signal_handler)  # Handle termination signals

# Run the app programmatically
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
