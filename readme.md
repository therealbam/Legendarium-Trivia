# INSTALLED MINIFORGE
curl -fsSLo Miniforge3.sh "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-$(uname -m).sh"
bash Miniforge3.sh -b

# Environment
python3 --env venv venv
source ./venv/bin/activate 
deactivate

# Another environment
python3 -m pip install virtualenv
virtualenv -p python3.8 venv
source venv/bin/activate
pip install --upgrade pip
pip install numpy cython
git clone --depth 1 https://github.com/pandas-dev/pandas.git
cd pandas
python3 setup.py install

# Conda
conda create --name py39 python=3.9
conda activate py39

# Use jupyter:
 ~/.local/bin/jupyter-notebook --allow-root --NotebookApp.iopub_data_rate_limit=2.0e6

# conda cheat sheet
https://docs.conda.io/projects/conda/en/4.6.0/_downloads/52a95608c49671267e40c689e0bc00ca/conda-cheatsheet.pdf

# COINMETRICS
https://github.com/coinmetrics/api-client-python/blob/master/examples/notebooks/walkthrough_community_python_event.ipynb