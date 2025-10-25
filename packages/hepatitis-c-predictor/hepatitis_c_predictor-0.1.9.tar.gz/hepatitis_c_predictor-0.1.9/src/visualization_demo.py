from plotly.subplots import make_subplots
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
from sklearn.metrics import confusion_matrix, roc_curve, auc
import numpy as np
import plotly.express as px
import seaborn as sns
from src.data import HepatitisDataset
from src.models import HepatitisNet, save_model
from src.train import ModelTrainer
from torch.utils.data import DataLoader
import torch
import torch.nn as nn
import time
import os

# Set up inferno color palette to match visualization.py
sns.set_palette("inferno")

"""
Contains visualization functions for the Streamlit demo app.
The functions here are mailnly either wrappers or modified versions of existing training
functions to include real-time interactive visualization of training metrics and data distributions.
"""

def display_features(data):
    # Select only numeric features to plot
    numeric_cols = data.select_dtypes(include=[np.number]).columns
    feature_cols = [col for col in numeric_cols if col not in ['Category', 'target']]
    
    selected_features = st.multiselect(
        "Select features to visualize:",
        feature_cols,
        default=feature_cols[:4] if len(feature_cols) >= 4 else feature_cols
    )
    
    if selected_features:
        # Create simple distribution plots without categories
        fig = make_subplots(
            rows=(len(selected_features) + 1) // 2, 
            cols=2,
            subplot_titles=selected_features
        )
        
        # Use inferno colors for each feature
        inferno_palette = sns.color_palette("inferno", len(selected_features))
        
        for i, feature in enumerate(selected_features):
            row = i // 2 + 1
            col = i % 2 + 1
            
            # Convert seaborn color to hex for plotly
            color_rgb = inferno_palette[i]
            color_hex = f'rgb({int(color_rgb[0]*255)}, {int(color_rgb[1]*255)}, {int(color_rgb[2]*255)})'
            
            # Simple histogram with inferno color
            fig.add_trace(
                go.Histogram(
                    x=data[feature],
                    name=feature,
                    showlegend=False,
                    marker_color=color_hex
                ),
                row=row, col=col
            )
        
        fig.update_layout(height=300 * ((len(selected_features) + 1) // 2))
        st.plotly_chart(fig, use_container_width=True)
    

def display_correlation_matrix(data):
    st.subheader("Correlation Matrix")
    numeric_cols = data.select_dtypes(include=[np.number]).columns
    corr_matrix = data[numeric_cols].corr()
    
    # Create mask for upper triangle (including diagonal) - same as visualization.py
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    
    # Apply mask to correlation matrix
    masked_corr = corr_matrix.copy()
    masked_corr = masked_corr.mask(mask)
    
    # Round to 3 decimal places for display
    masked_corr_rounded = masked_corr.round(3)
    
    fig = px.imshow(
        masked_corr_rounded,
        title="Feature Correlation Matrix (Lower Triangle)",
        color_continuous_scale="inferno",  # Use inferno colorscale
        aspect="equal",  # Make it square (width = height)
        text_auto=True,
        color_continuous_midpoint=0
    )
    
    # Set square dimensions
    matrix_size = len(numeric_cols)
    fig.update_layout(
        height=800,
        width=800,  # Make width equal to height for square shape
        xaxis=dict(constrain='domain'),
        yaxis=dict(constrain='domain', scaleanchor='x')
    )
    st.plotly_chart(fig, use_container_width=True)

def display_class_distribution(data):
    st.subheader("Class Distribution")
    
    col1, col2 = st.columns(2)
    
    # Disease Categories stacked bar (similar to plot_data_overview)
    with col1:
        if 'Category' in data.columns:
            category_counts = data['Category'].value_counts()
            inferno_colors = sns.color_palette("inferno", len(category_counts))
            inferno_hex = [f'rgb({int(c[0]*255)}, {int(c[1]*255)}, {int(c[2]*255)})' for c in inferno_colors]
            
            # Create stacked bar chart
            fig = go.Figure()
            bottom = 0
            
            for i, (category, count) in enumerate(category_counts.items()):
                fig.add_trace(go.Bar(
                    x=['Total Population'],
                    y=[count],
                    name=f'{category}: {count}',
                    marker_color=inferno_hex[i],
                    base=bottom
                ))
                bottom += count
            
            fig.update_layout(
                title='Disease Categories',
                xaxis_title='Population',
                yaxis_title='Count',
                barmode='stack',
                showlegend=True,
                legend=dict(orientation="v", yanchor="bottom", y=0, xanchor="left", x=1.02)
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Sex Distribution stacked bar (similar to plot_data_overview)
    with col2:
        if 'Sex' in data.columns:
            sex_counts = data['Sex'].value_counts()
            inferno_colors = sns.color_palette("inferno", len(sex_counts))
            inferno_hex = [f'rgb({int(c[0]*255)}, {int(c[1]*255)}, {int(c[2]*255)})' for c in inferno_colors]
            
            # Create stacked bar chart
            fig = go.Figure()
            bottom = 0
            
            for i, (sex, count) in enumerate(sex_counts.items()):
                fig.add_trace(go.Bar(
                    x=['Total Population'],
                    y=[count],
                    name=f'{sex}: {count}',
                    marker_color=inferno_hex[i],
                    base=bottom
                ))
                bottom += count
            
            fig.update_layout(
                title='Sex Distribution',
                xaxis_title='Population',
                yaxis_title='Count',
                barmode='stack',
                showlegend=True,
                legend=dict(orientation="v", yanchor="bottom", y=0, xanchor="left", x=1.02)
            )
            
            st.plotly_chart(fig, use_container_width=True)

def modified_train_loop_with_visualization(X_train, y_train, X_val, y_val, epochs, batch_size, learning_rate, hidden_sizes_list, dropout_rate, num_residual_blocks, model_path):
    input_size = X_train.shape[1]
    model = HepatitisNet(
        input_size=input_size,
        hidden_sizes=hidden_sizes_list,
        num_classes=2,
        dropout_rate=dropout_rate,
        num_residual_blocks=num_residual_blocks
    )
    
    # Create data loaders
    train_dataset = HepatitisDataset(X_train, y_train)
    val_dataset = HepatitisDataset(X_val, y_val)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    # Create trainer
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    trainer = ModelTrainer(model, device)
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Create placeholders for real-time plots
    col1, col2 = st.columns(2)
    with col1:
        loss_chart = st.empty()
    with col2:
        acc_chart = st.empty()
    
    # Modified training loop for real-time updates
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    
    history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}
    
    start_time = time.time()
    
    for epoch in range(epochs):
        # Training
        train_loss, train_acc = trainer.train_epoch(train_loader, criterion, optimizer)
        val_loss, val_acc = trainer.validate_epoch(val_loader, criterion)
        
        # Update history
        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)
        
        # Update progress
        progress = (epoch + 1) / epochs
        progress_bar.progress(progress)
        status_text.text(f'Epoch {epoch + 1}/{epochs} - Train Loss: {train_loss:.4f}, Val Acc: {val_acc:.2f}%')
        
        # Update plots every 5 epochs
        if epoch % 5 == 0 or epoch == epochs - 1:
            # Get inferno colors for training plots
            inferno_palette = sns.color_palette("inferno", 10)
            train_color = f'rgb({int(inferno_palette[0][0]*255)}, {int(inferno_palette[0][1]*255)}, {int(inferno_palette[0][2]*255)})'
            val_color = f'rgb({int(inferno_palette[-1][0]*255)}, {int(inferno_palette[-1][1]*255)}, {int(inferno_palette[-1][2]*255)})'
            
            # Loss plot
            with loss_chart.container():
                fig_loss = go.Figure()
                fig_loss.add_trace(go.Scatter(
                    y=history['train_loss'],
                    mode='lines',
                    name='Train Loss',
                    line=dict(color=train_color, width=3)
                ))
                fig_loss.add_trace(go.Scatter(
                    y=history['val_loss'],
                    mode='lines',
                    name='Validation Loss',
                    line=dict(color=val_color, width=3)
                ))
                fig_loss.update_layout(title='Training Loss', xaxis_title='Epoch', yaxis_title='Loss')
                st.plotly_chart(fig_loss, use_container_width=True)
            
            # Accuracy plot
            with acc_chart.container():
                fig_acc = go.Figure()
                fig_acc.add_trace(go.Scatter(
                    y=history['train_acc'],
                    mode='lines',
                    name='Train Accuracy',
                    line=dict(color=train_color, width=3)
                ))
                fig_acc.add_trace(go.Scatter(
                    y=history['val_acc'],
                    mode='lines',
                    name='Validation Accuracy',
                    line=dict(color=val_color, width=3)
                ))
                fig_acc.update_layout(title='Training Accuracy', xaxis_title='Epoch', yaxis_title='Accuracy (%)')
                st.plotly_chart(fig_acc, use_container_width=True)
    
    training_time = time.time() - start_time
    
    # Training summary
    st.success("Training completed!")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Final Train Accuracy", f"{history['train_acc'][-1]:.2f}%")
    with col2:
        st.metric("Final Val Accuracy", f"{history['val_acc'][-1]:.2f}%")
    with col3:
        st.metric("Training Time", f"{training_time:.2f}s")
    
    # Save model
    model_dir = os.path.join(os.path.dirname(__file__), 'saved_models')
    os.makedirs(model_dir, exist_ok=True)
    
    additional_info = {
        'input_size': input_size,
        'hidden_sizes': hidden_sizes_list,
        'num_classes': 2,
        'dropout_rate': dropout_rate,
        'num_residual_blocks': num_residual_blocks,
        'final_val_acc': history['val_acc'][-1]
    }
    
    saved_path = save_model(model, model_path, additional_info, demo=True)
    st.info(f"Model saved to: {saved_path}")

def display_violin_with_outliers(data, numeric_cols=None):
    """
    Create violin plots with overlaid box plots to show outliers for each numeric feature.
    Replicates the plot_violin_with_outliers function from visualization.py using Plotly.
    
    Parameters
    ----------
    data: pd.DataFrame
        DataFrame containing the data
    numeric_cols: list[str]
        List of column names to plot. If None, uses default hepatitis C features.
    """
    st.subheader("Violin Plots with Outliers")
    
    if numeric_cols is None:
        numeric_cols = ['Age','ALB','ALP','ALT','AST','BIL','CHE','CHOL','CREA','GGT','PROT']
    
    # Filter columns that exist in the dataframe
    available_cols = [col for col in numeric_cols if col in data.columns]
    
    if not available_cols:
        st.warning("No numeric columns found")
        return
    
    # Use inferno colors for each feature
    inferno_palette = sns.color_palette("inferno", len(available_cols))
    inferno_hex = [f'rgb({int(c[0]*255)}, {int(c[1]*255)}, {int(c[2]*255)})' for c in inferno_palette]
    
    # Create subplots arranged horizontally
    fig = make_subplots(
        rows=1, 
        cols=len(available_cols),
        subplot_titles=available_cols,
        shared_yaxes=False
    )
    
    for i, col in enumerate(available_cols):
        col_num = i + 1
        
        # Add violin plot
        fig.add_trace(
            go.Violin(
                y=data[col],
                name=col,
                box_visible=True,  # Show box plot inside violin
                meanline_visible=True,  # Show mean line
                fillcolor=inferno_hex[i],
                opacity=0.7,
                line_color='black',
                showlegend=False
            ),
            row=1, col=col_num
        )
        
        # Update y-axis labels (only for first subplot)
        if i == 0:
            fig.update_yaxes(title_text="Values", row=1, col=col_num)
        else:
            fig.update_yaxes(title_text="", row=1, col=col_num)
        
        # Update x-axis
        fig.update_xaxes(title_text="", row=1, col=col_num)
    
    # Update layout
    fig.update_layout(
        title_text="Violin Plots with Outliers for Each Feature",
        title_x=0.5,
        height=500,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_confusion_matrix(y_true, y_pred, class_names=['Healthy', 'Hepatitis C']):

    st.subheader("Confusion Matrix")
    
    cm = confusion_matrix(y_true, y_pred)
    
    # Calculate accuracy
    accuracy = np.trace(cm) / np.sum(cm)
    
    # Display accuracy metric
    st.metric("Overall Accuracy", f"{accuracy:.3f}")
    
    col1, col2 = st.columns(2)
    
    # Percentages version
    with col1:
        # Calculate percentage confusion matrix (row-wise normalization)
        cm_percent = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis] * 100
        
        fig_percent = px.imshow(
            cm_percent,
            title="Confusion Matrix (Percentages)",
            color_continuous_scale="inferno",
            aspect="equal",
            text_auto=True,
            x=class_names,
            y=class_names,
            labels=dict(x="Predicted", y="Actual")
        )
        
        # Update text formatting for percentages
        fig_percent.update_traces(texttemplate="%{z:.1f}%", textfont_size=14)
        
        # Set square dimensions
        fig_percent.update_layout(
            height=400,
            width=400,
            xaxis=dict(constrain='domain'),
            yaxis=dict(constrain='domain', scaleanchor='x')
        )
        
        st.plotly_chart(fig_percent, use_container_width=True)
    
    # Counts version
    with col2:
        fig_counts = px.imshow(
            cm,
            title="Confusion Matrix (Counts)",
            color_continuous_scale="inferno",
            aspect="equal",
            text_auto=True,
            x=class_names,
            y=class_names,
            labels=dict(x="Predicted", y="Actual")
        )
        
        # Update text formatting for counts
        fig_counts.update_traces(texttemplate="%{z:d}", textfont_size=14)
        
        # Set square dimensions
        fig_counts.update_layout(
            height=400,
            width=400,
            xaxis=dict(constrain='domain'),
            yaxis=dict(constrain='domain', scaleanchor='x')
        )
        
        st.plotly_chart(fig_counts, use_container_width=True)

def display_roc_curve(y_true, y_probs):
    st.subheader("ROC Curve")
    fpr, tpr, _ = roc_curve(y_true, y_probs[:, 1])
    roc_auc = auc(fpr, tpr)
    
    # Get inferno colors
    inferno_palette = sns.color_palette("inferno", 10)
    roc_color = f'rgb({int(inferno_palette[-2][0]*255)}, {int(inferno_palette[-2][1]*255)}, {int(inferno_palette[-2][2]*255)})'
    random_color = f'rgb({int(inferno_palette[2][0]*255)}, {int(inferno_palette[2][1]*255)}, {int(inferno_palette[2][2]*255)})'
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=fpr, y=tpr,
        mode='lines',
        name=f'ROC Curve (AUC = {roc_auc:.3f})',
        line=dict(color=roc_color, width=3)
    ))
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1],
        mode='lines',
        name='Random Classifier',
        line=dict(color=random_color, dash='dash', width=2)
    ))
    fig.update_layout(
        title='Receiver Operating Characteristic (ROC) Curve',
        xaxis_title='False Positive Rate',
        yaxis_title='True Positive Rate',
        width=600, height=400,
        showlegend=True,
        legend=dict(x=0.6, y=0.1)
    )
    st.plotly_chart(fig, use_container_width=True)

def display_feature_importance(model):
    """
    Display feature importance analysis using inferno color palette.
    
    Parameters
    ----------
    model: torch.nn.Module
        Trained PyTorch model
    """
    st.subheader("Feature Importance Analysis")
    
    # Get first layer weights as proxy for feature importance
    first_layer_weights = model.layers[0].weight.data.cpu().numpy()
    feature_importance = np.abs(first_layer_weights).mean(axis=0)
    
    # Use the correct processed feature names
    feature_names = ['Age', 'ALB', 'ALP', 'ALT', 'AST', 'BIL', 'CHE', 'CHOL', 'CREA', 'GGT', 'PROT', 'sex_encoded']
    # Only use as many features as we actually have
    available_features = min(len(feature_names), len(feature_importance))
    
    importance_df = pd.DataFrame({
        'Feature': feature_names[:available_features],
        'Importance': feature_importance[:available_features]
    }).sort_values('Importance', ascending=True)
    
    # Get inferno colors for each bar
    inferno_palette = sns.color_palette("inferno", len(importance_df))
    inferno_hex = [f'rgb({int(c[0]*255)}, {int(c[1]*255)}, {int(c[2]*255)})' for c in inferno_palette]
    
    # Create bar chart with individual colors
    fig = go.Figure(data=[
        go.Bar(
            x=importance_df['Importance'],
            y=importance_df['Feature'],
            orientation='h',
            marker=dict(
                color=inferno_hex,
                line=dict(color='black', width=0.5)
            )
        )
    ])
    
    # Update layout for better appearance
    fig.update_layout(
        title='Feature Importance (First Layer Weights)',
        xaxis_title='Importance',
        yaxis_title='Feature',
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)