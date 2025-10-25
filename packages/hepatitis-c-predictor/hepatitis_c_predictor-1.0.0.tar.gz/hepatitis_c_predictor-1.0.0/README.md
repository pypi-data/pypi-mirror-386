# Hepatitis C Predictor

Developing a Deep Learning model with PyTorch to identify patterns and predict the presence of Hepatitis C from patient data, paving the way for faster, more accurate diagnostics.

[![Documentation Status](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://ninjalice.github.io/HEPATITIS_C_MODEL/src.html)

## Features

- 📊 **Interactive Data Exploration**: Visualize and explore the Hepatitis C dataset
- 🚀 **Model Training Interface**: Train models with custom hyperparameters
- 📈 **Model Evaluation**: Comprehensive performance metrics and visualizations
- 🤖 **Deep Learning**: PyTorch-based neural network with residual connections
- 📦 **Auto-download**: Dataset downloads automatically if not present

## Dataset

The dataset contains laboratory values from blood donors and Hepatitis C patients:

- **Source**: [UCI Machine Learning Repository](https://archive.ics.uci.edu/ml/datasets/HCV+data) / [Kaggle](https://www.kaggle.com/datasets/fedesoriano/hepatitis-c-dataset)
- **Size**: 615 samples
- **Features**: 12 laboratory measurements + age and sex
- **Target**: Binary classification (Healthy vs Hepatitis C)
- **Auto-download**: The app will automatically download the dataset if not present

## Model

- **Architecture**: Deep Neural Network with Residual Connections
  - Input Layer: 12 features
  - Hidden Layers: [128, 64, 32] neurons
  - Residual Blocks: 2 per hidden layer
  - Output Layer: 2 classes (Binary classification)
- **Framework**: PyTorch 2.8+
- **Regularization**: Layer Normalization + Dropout (0.3)
- **Expected Accuracy**: ~97.5% on validation set

## 🚀 Deployment

### Requirements for Deployment

- Python 3.10
- All dependencies listed in `requirements.txt`
- Dataset will be downloaded automatically on first run

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Important Note

⚠️ This model is for educational purposes only. Do not use for actual medical diagnosis. Always consult healthcare professionals.

To run it locally:

```bash
uvx --from hepatitis-c-predictor --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ hepatitis-c-demo
```

## Docs

You can check the modules docs in the docs folder or directly from the deployed version on GH pages here: https://ninjalice.github.io/HEPATITIS_C_MODEL/src.html

## Getting Started

1. Clone the repository:

   ```bash
   git clone https://github.com/Ninjalice/HEPATITIS_C_MODEL.git
   cd HEPATITIS_C_MODEL
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

   Or using `uv`:

   ```bash
   uv sync --frozen
   ```

3. Run the interactive dashboard:

   ```bash
   streamlit run app.py
   ```

   The app will automatically download the dataset if not present.

### Option 2: Jupyter Notebooks

Follow the notebooks in order:

1. `01-data-exploration.ipynb` - Explore the dataset
2. `02-data-preprocessing.ipynb` - Clean and prepare data
3. `03-model-training.ipynb` - Train the neural network
4. `04-model-prediction.ipynb` - Make predictions on new data (WIP)

### Manual Download (Optional)

If auto-download fails, you can manually download from:

1. Kaggle: https://www.kaggle.com/datasets/fedesoriano/hepatitis-c-dataset
2. Place the file in `data/raw/hepatitis_data.csv`

## Project Organization

    ├── data/
    │   ├── raw/              <- The original, immutable data dump
    │   └── processed/        <- The final, canonical data sets for modeling
    │
    ├── models/               <- Trained and serialized models
    │
    ├── notebooks/            <- Jupyter notebooks for analysis and modeling
    │   ├── 01-data-exploration.ipynb
    │   ├── 02-data-preprocessing.ipynb
    │   ├── 03-model-training.ipynb
    │   └── 04-model-prediction.ipynb
    │
    ├── reports/              <- Generated analysis as HTML, PDF, LaTeX, etc.
    │   └── figures/          <- Generated graphics and figures
    │
    ├── src/                  <- Source code for use in this project
    │   ├── __init__.py
    │   ├── data.py           <- Scripts to download or generate data
    │   ├── train.py          <- Scripts to train models
    │   ├── models.py         <- Scripts to train models and make predictions
    │   └── visualization.py  <- Scripts to create exploratory visualizations
    │
    ├── requirements.txt      <- The requirements file for reproducing the environment
    └── README.md             <- The top-level README for developers
