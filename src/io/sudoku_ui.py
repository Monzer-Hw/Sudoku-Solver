"""
Provides the SudokuUI class that encapsulates all Streamlit user interface components.
This includes file uploads, image display, error/info messaging, and custom styling.
"""

import cv2
import numpy as np
import streamlit as st


class SudokuUI:
    """
    SudokuUI handles the Streamlit user interface for the Sudoku Solver app.
    It manages file uploads, displays images, shows messages, and applies custom CSS.
    """

    def setup_page(self):
        """Configure the Streamlit page."""
        st.set_page_config(
            page_title="Sudoku Vision Solver",
            page_icon="🧩",
            layout="wide",
            initial_sidebar_state="expanded",
        )

    def inject_custom_css(self):
        """Inject custom CSS for modern styling."""
        custom_css = """ 
        <style>
            .main {
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            }
            .header {
                padding: 2rem;
                border-radius: 15px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .upload-box {
                border: 2px dashed #4a90e2;
                border-radius: 10px;
                padding: 2rem;
                background: rgba(255, 255, 255, 0.9);
            }
            .success-box {
                border: 2px solid #4CAF50;
                background: rgba(76, 175, 80, 0.1);
                padding: 1rem;
                border-radius: 10px;
            }
            .stProgress > div > div > div {
                background-color: #4a90e2;
            }
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            .fade-in {
                animation: fadeIn 0.5s ease-in;
            }
        </style>    
        """
        st.markdown(custom_css, unsafe_allow_html=True)

    def display_header(self):
        """Displays application header"""
        with st.container():
            st.markdown(
                """
            <div class="header">
                <h1 style='text-align: center; color: #ffffff;'>Sudoku Vision Solver</h1>
                <p style='text-align: center; color: #ffffff;'>
                    Upload a 9x9 Sudoku puzzle image and watch it get solved magically! ✨
                </p>
            </div>
            """,
                unsafe_allow_html=True,
            )
            st.write("---")

    def file_uploader(self):
        """Displays file uploader component"""
        st.markdown("### 📤 Upload Your Puzzle")
        return st.file_uploader(
            " ",
            type=["jpg", "jpeg", "png"],
            label_visibility="collapsed",
        )

    def display_original_image(self, uploaded_file):
        """Displays uploaded image preview"""
        with st.container():
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            st.image(image, caption="Original Puzzle", use_container_width=True)
            return image

    def solve_button(self):
        """Displays solve button with progress status"""
        return st.button(
            "🚀 Solve Sudoku",
            use_container_width=True,
            help="Click to start solving process",
        )

    def processing_status(self):
        """Context manager for processing status"""
        return st.status("🔍 Processing...")

    def display_solution(self, result, column):
        """Displays solution results in specified column"""
        with column:
            st.markdown("### 🎉 Solved Puzzle")
            with st.container():
                st.markdown(
                    """
                <div class="success-box fade-in">
                    <h4 style='color: #4CAF50; margin: 0;'>🎯 Solution Found!</h4>
                    <p style='margin: 0.5rem 0 0 0;'>See solved puzzle below ⬇️</p>
                </div>
                <div style="margin: 1.5rem 0;"></div>
                """,
                    unsafe_allow_html=True,
                )
                result = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
                st.image(result, caption="Solved Puzzle", use_container_width=True)
                result = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
                result_bytes = cv2.imencode(".png", result)[1].tobytes()
                st.download_button(
                    label="📥 Download Solution",
                    data=result_bytes,
                    file_name="solved_sudoku.png",
                    mime="image/png",
                    help="Click to download solved image",
                    use_container_width=True,
                )

    def display_tips(self, column):
        """Displays usage tips in specified column"""
        with column:
            with st.expander("📚 For Best Results:"):
                st.markdown("""
                - 🖼️ High resolution image
                - 🧩 Ensure more than 17 clues
                """)
