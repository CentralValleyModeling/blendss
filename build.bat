if not exist "dist" (
    mkdir "dist" 2>nul
)
conda build . --output-folder ./dist