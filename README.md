# Installation

## 1. Create the conda environment
```python
conda create --name hovdeg -c conda-forge python=3.9 jupyter numpy matplotlib pandas scipy dill pre-commit folium streamlit openpyxl streamlit-folium
conda activate hovdeg
pre-commit install
```

## 2. Obtain the raw data
Download the meta, hourly, and stationdata from our Google Drive folder and place them in the respective folders under `/data'

## 3. Run the data processor.
The command for doing this is in `code/run_data_processor.sh'.
Here you can select which roues to process. The processed data files will be stored in `/processed'

## 4. Run the data viewer.
The command for doing this is in `code/run_data_viewer.sh'.
