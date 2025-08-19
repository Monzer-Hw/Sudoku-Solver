from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import base, sudoku


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(base.base_router)
app.include_router(sudoku.sudoku_router)
