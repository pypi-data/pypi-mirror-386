import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix, classification_report, roc_curve, auc
import os
import time
import tempfile

try:
    from src.models import HepatitisNet, evaluate_model, save_model, load_model
    from src.data import  download_dataset, load_raw_data, clean_data, prepare_features, HepatitisDataset
    from src.train import ModelTrainer
    from src.visualization_demo import *
    from sklearn.preprocessing import LabelEncoder
    from torch.utils.data import DataLoader
    # Try to import visualization functions
    try:
        from src.visualization import plot_correlation_matrix, plot_feature_distributions
    except ImportError:
        st.warning("Visualization functions not found. Using built-in alternatives.")
        def plot_correlation_matrix(data):
            return None
        def plot_feature_distributions(data):
            return None
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Hepatitis C Classification Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #ff7f0e;
        margin: 1rem 0;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def load_sample_data():
    """Load and cache sample data"""
    try:
        file_temp_path = download_dataset(demo=True)
        # Try to load real data first
        return load_raw_data(filepath=file_temp_path, demo=True)

    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

@st.cache_data
def prepare_data(data):
    """Prepare and preprocess data"""
    if data is None:
        return None, None, None, None, None, None
    
    try:
        # Implement preprocessing directly in app.py
        # Clean the data
        cleaned_data, sex_encoder = clean_data(data)
        
        # Prepare features  
        X_processed, y_processed, imputer = prepare_features(cleaned_data)
        
        # Split the data
        X_train, X_temp, y_train, y_temp = train_test_split(
            X_processed, y_processed, test_size=0.4, random_state=42, stratify=y_processed
        )
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
        )
        
        # Scale the features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        X_test_scaled = scaler.transform(X_test)
        
        return X_train_scaled, X_val_scaled, X_test_scaled, y_train, y_val, y_test
        
    except Exception as e:
        st.error(f"Error preprocessing data: {e}")
        return None, None, None, None, None, None

def main():
    st.markdown('<div class="main-header">🏥 Hepatitis C Classification Dashboard</div>', unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a section:",
        ["Data Exploration", "Model Training", "Model Evaluation"]
    )
    
    # Load data
    data = load_sample_data()
    
    if data is None:
        st.error("Failed to load data. Please check your data files.")
        return
    
    # Prepare data
    X_train, X_val, X_test, y_train, y_val, y_test = prepare_data(data)
    saved_path = os.path.join(tempfile.gettempdir(), 'hepatitis_model.pth')
    if page == "Data Exploration":
        data_exploration_page(data)
    elif page == "Model Training":
        model_training_page(X_train, X_val, y_train, y_val, data, model_path=saved_path)
    elif page == "Model Evaluation":
        model_evaluation_page(X_test, y_test, saved_path, data)

def data_exploration_page(data):
    st.markdown('<div class="section-header">📊 Data Exploration</div>', unsafe_allow_html=True)
    
    # Dataset Overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Samples", len(data))
    with col2:
        st.metric("Features", len(data.columns) - 1)
    with col3:
        # Calculate positive rate
        if 'target' in data.columns:
            positive_rate = (data['target'] == 1).mean() * 100
        else:
            # Simple check for non-blood donor cases
            positive_rate = (~data['Category'].str.contains('Blood Donor', na=False)).mean() * 100
        st.metric("Positive Rate", f"{positive_rate:.1f}%")
    
    # Display sample data
    st.subheader("Sample Data")
    st.dataframe(data.head(10))
    
    # Basic statistics
    st.subheader("Statistical Summary")
    st.dataframe(data.describe())
    
    # Feature distributions
    st.subheader("Feature Distributions")

    display_features(data)

    display_violin_with_outliers(data)

    # Correlation matrix
    display_correlation_matrix(data)
    
    # Class distribution
    display_class_distribution(data)
    

def model_training_page(X_train, X_val, y_train, y_val, data, model_path=''):
    st.markdown('<div class="section-header">🚀 Model Training</div>', unsafe_allow_html=True)
    
    # Training parameters
    st.subheader("Training Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        epochs = st.slider("Number of Epochs", 10, 100, 50)
        learning_rate = st.selectbox("Learning Rate", [0.001, 0.01, 0.1], index=0)
        batch_size = st.selectbox("Batch Size", [16, 32, 64], index=1)
    
    with col2:
        hidden_sizes = st.text_input("Hidden Layer Sizes (comma-separated)", "128,64,32")
        dropout_rate = st.slider("Dropout Rate", 0.0, 0.5, 0.3)
        num_residual_blocks = st.slider("Residual Blocks", 1, 4, 2)
    
    # Parse hidden sizes
    try:
        hidden_sizes_list = [int(x.strip()) for x in hidden_sizes.split(',')]
    except:
        hidden_sizes_list = [128, 64, 32]
        st.warning("Invalid hidden sizes format. Using default: [128, 64, 32]")
    
    # Training button
    if st.button("Start Training", type="primary"):
        # Create model
        modified_train_loop_with_visualization(
            X_train, y_train, X_val, y_val,
            epochs=epochs,
            batch_size=batch_size,
            learning_rate=learning_rate,
            hidden_sizes_list=hidden_sizes_list,
            dropout_rate=dropout_rate,
            num_residual_blocks=num_residual_blocks,
            model_path=model_path
        )


def model_evaluation_page(X_test, y_test, model_path, data):
    st.markdown('<div class="section-header">📈 Model Evaluation</div>', unsafe_allow_html=True)


    if not os.path.exists(model_path):
        st.warning(f"No trained model found at {model_path or 'the default location'}. Please train a model first in the 'Model Training' section.")
        return
    
    # Load model
    try:
        model, model_info = load_model(model_path, input_size=X_test.shape[1])
        st.success("Model loaded successfully!")
        
        if model_info:
            st.subheader("Model Information")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Input Size", model_info.get('input_size', 'N/A'))
            with col2:
                st.metric("Hidden Layers", str(model_info.get('hidden_sizes', 'N/A')))
            with col3:
                st.metric("Validation Accuracy", f"{model_info.get('final_val_acc', 0):.2f}%")
        
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return
    
    # Create test dataset and dataloader
    test_dataset = HepatitisDataset(X_test, y_test)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)
    
    # Evaluate model
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = model.to(device)
    y_true, y_pred, y_probs = evaluate_model(model, test_loader, device)
    
    # Performance metrics
    st.subheader("Performance Metrics")
    
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred)
    recall = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Accuracy", f"{accuracy:.3f}")
    with col2:
        st.metric("Precision", f"{precision:.3f}")
    with col3:
        st.metric("Recall", f"{recall:.3f}")
    with col4:
        st.metric("F1-Score", f"{f1:.3f}")
    
    # Confusion Matrix
    display_confusion_matrix(y_true, y_pred)
    
    # ROC Curve
    display_roc_curve(y_true, y_probs)
    
    # Prediction examples
    st.subheader("Sample Predictions")
    
    # Select random samples
    sample_indices = np.random.choice(len(X_test), min(10, len(X_test)), replace=False)
    
    for i, idx in enumerate(sample_indices[:5]):  # Show first 5 samples
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write(f"**Sample {i+1}**")
            # Show feature values - use the processed feature names
            feature_names = ['Age', 'ALB', 'ALP', 'ALT', 'AST', 'BIL', 'CHE', 'CHOL', 'CREA', 'GGT', 'PROT', 'sex_encoded']
            # Only use as many features as we actually have
            available_features = min(len(feature_names), X_test.shape[1])
            sample_features = {feature_names[j]: float(X_test[idx, j]) for j in range(available_features)}
            st.json(sample_features)
        
        with col2:
            actual = "Positive" if y_true[idx] == 1 else "Negative"
            st.metric("Actual", actual)
        
        with col3:
            predicted = "Positive" if y_pred[idx] == 1 else "Negative"
            confidence = max(y_probs[idx]) * 100
            st.metric("Predicted", predicted)
            st.metric("Confidence", f"{confidence:.1f}%")
        
        st.divider()
    
    # Feature importance (using model weights)
    display_feature_importance(model)

def cli_main():
    """Entry point for command-line interface."""
    import sys
    import subprocess
    
    # Get the path to this file
    app_path = __file__
    
    # Launch Streamlit app
    subprocess.run([sys.executable, "-m", "streamlit", "run", app_path])

if __name__ == "__main__":
    main()
