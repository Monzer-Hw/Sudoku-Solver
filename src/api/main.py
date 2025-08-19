from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import cv2
from pathlib import Path

from src.core.detector import SudokuDetector
from src.core.ocr import SudokuTesseract
from src.core.solver import SudokuSolver
from src.core.visualizer import SudokuVisualizer
import io


app = FastAPI(title="Sudoku Solver API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SolveResponse(BaseModel):
    grid: list[list[int]]
    solved: bool


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/solve", response_model=SolveResponse)
async def solve_endpoint(file: UploadFile = File(...), return_image: bool = False):
    if file.content_type not in {"image/png", "image/jpeg", "image/jpg"}:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    image_bytes = await file.read()
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image_bgr = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise HTTPException(status_code=400, detail="Invalid image")

    detector = SudokuDetector()
    ocr = SudokuTesseract()

    # 1) Preprocess and find grid
    original, _, _, thresh = detector.preprocess_image(image_bgr)
    grid_contour = detector.find_grid_contour(thresh)
    if grid_contour is None:
        raise HTTPException(status_code=422, detail="Could not detect the Sudoku grid")

    # 2) Rectify grid and split into cells
    warped, _ = detector.perspective_transform(original, grid_contour)
    cells, _ = detector.extract_cells(warped)

    # 3) OCR
    mask_path = (Path(__file__).resolve().parents[2] / "assets" / "mask.png").as_posix()
    processed_cells = ocr.process_cells(cells, mask_path)
    sudoku_grid = ocr.recognize(processed_cells)

    # 4) Solve
    try:
        solved_grid = SudokuSolver.solve(sudoku_grid)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if return_image:
        positions = np.where(sudoku_grid > 0, 0, 1)
        # Recompute cell_size for overlay
        _, cell_size = detector.extract_cells(warped)
        final_image = SudokuVisualizer.overlay_solution(
            image_bgr, warped, solved_grid, positions, grid_contour, cell_size
        )
        success, png_bytes = cv2.imencode(".png", final_image)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to encode image")
        return StreamingResponse(io.BytesIO(png_bytes.tobytes()), media_type="image/png")

    return SolveResponse(grid=solved_grid.tolist(), solved=True)