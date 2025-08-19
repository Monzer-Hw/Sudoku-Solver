import io
import cv2
import numpy as np
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from src.api.schemas.sudoku import SolveResponse
from src.api.config import Settings, get_settings

from src.core.detector import SudokuDetector
from src.core.ocr import SudokuTesseract
from src.core.solver import SudokuSolver
from src.core.visualizer import SudokuVisualizer


sudoku_router = APIRouter(
    prefix="/sudoku",
    tags=["sudoku"],
)


def _run_pipeline(image_bgr: np.ndarray) -> tuple:
    detector = SudokuDetector()
    ocr = SudokuTesseract()

    original, _, _, thresh = detector.preprocess_image(image_bgr)
    grid_contour = detector.find_grid_contour(thresh)
    if grid_contour is None:
        raise HTTPException(status_code=422, detail="Could not detect the Sudoku grid")

    warped, _ = detector.perspective_transform(original, grid_contour)
    cells, cell_size = detector.extract_cells(warped)

    mask_path = (Path(__file__).resolve().parents[3] / "assets" / "mask.png").as_posix()
    processed_cells = ocr.process_cells(cells, mask_path)
    sudoku_grid = ocr.recognize(processed_cells)

    try:
        solved_grid = SudokuSolver.solve(sudoku_grid)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return original, warped, sudoku_grid, solved_grid, grid_contour, cell_size


@sudoku_router.post("/solve", response_model=SolveResponse)
async def solve_json(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
):
    if file.content_type not in settings.FILE_ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="File type not supported")

    image_bytes = await file.read()
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image_bgr = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise HTTPException(status_code=400, detail="Invalid image")

    _, _, _, solved_grid, _, _ = _run_pipeline(image_bgr)
    return SolveResponse(grid=solved_grid.tolist(), solved=True)


@sudoku_router.post("/solve:image")
async def solve_image(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
):
    if file.content_type not in settings.FILE_ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="File type not supported")

    image_bytes = await file.read()
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image_bgr = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise HTTPException(status_code=400, detail="Invalid image")

    original, warped, sudoku_grid, solved_grid, grid_contour, cell_size = _run_pipeline(
        image_bgr
    )
    positions = np.where(sudoku_grid > 0, 0, 1)
    final_image = SudokuVisualizer.overlay_solution(
        image_bgr, warped, solved_grid, positions, grid_contour, cell_size
    )
    success, png_bytes = cv2.imencode(".png", final_image)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to encode image")
    return StreamingResponse(io.BytesIO(png_bytes.tobytes()), media_type="image/png")
