# Sudoku Solver 🧩

This computer vision application solves 9x9 Sudoku puzzles from images through a multi-stage process: It detects and extracts Sudoku grids from input images, recognizes existing digits using Tesseract OCR with custom preprocessing, solves the puzzle using an efficient backtracking algorithm, and finally overlays the digital solution back onto the original image for clear visualization.

<div align="center">
  <img src="assets/workflow.png" alt="Workflow" style="width:100%;"/>
</div>


## Installation ⚙️

### Prerequisites
Tesseract OCR installed on your system ([Installation guide](https://github.com/UB-Mannheim/tesseract/wiki))
### Clone the repository
```bash
git clone https://github.com/Monzer-Hw/sudoku-solver.git
```

### Prepare the environment using uv
```bash
uv sync
```
this will create a virtual environment and install the required dependencies.


## Usage 🚀
- Activate your virtual environment
- Run the Streamlit app:
    ```bash
    streamlit run app.py
    ```


## Project Structure 📁
```
sudoku-solver/
├── assets/
├── notebooks/
│ └── prototype.ipynb
├── src/
│ ├── core/
│ │ ├── __init__.py
│ │ ├── detector.py      # Grid detection & processing
│ │ ├── ocr.py           # Digit recognition
│ │ ├── solver.py        # Puzzle solving logic
│ │ └── visualizer.py    # Solution visualization
│ └── io/
│   ├── __init__.py           
│   └── sudoku_ui.py          
├── app.py                    # Streamlit application entry point
├── pyproject.toml            # Dependencies
├── .python-version
├── README.md
├── LICENSE
└── uv.lock 
```


## License 📄
MIT License - See [LICENSE](LICENSE) for details
