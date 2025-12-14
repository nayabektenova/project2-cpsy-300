import io
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from azure.storage.blob import BlobServiceClient, BlobClient

def upload_to_blob(container_name, blob_name, data_bytes):
    connection_string = os.environ['AzureWebJobsStorage']
    blob_client = BlobClient.from_connection_string(
        conn_str=connection_string,
        container_name=container_name,
        blob_name=blob_name
    )
    blob_client.upload_blob(data_bytes, overwrite=True)
    print(f"[INFO] Uploaded {blob_name} to container {container_name}")

# UPDATED FUNCTION: Split into two parts rather than the original run_analysis() function doing everything at once.
# Process the csv file by cleaning the data and completeing the nessecary 
def process_csv(df):
    # ---- CLEANING ----
    if 'Diet_type' in df.columns:
        df['Diet_type'] = df['Diet_type'].str.strip().str.title()
    if 'Cuisine_type' in df.columns:
        df['Cuisine_type'] = df['Cuisine_type'].str.strip().str.title()

    numeric_cols = ['Protein(g)', 'Carbs(g)', 'Fat(g)']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].mean())

    df = df.fillna('Unknown')

    # ---- METRICS ----
    avg_macros = df.groupby('Diet_type')[['Protein(g)', 'Carbs(g)', 'Fat(g)']].mean()
    top_protein = df.sort_values('Protein(g)', ascending=False).groupby('Diet_type').head(5)

    df['Protein_to_Carbs_ratio'] = df['Protein(g)'] / df['Carbs(g)']
    df['Carbs_to_Fat_ratio'] = df['Carbs(g)'] / df['Fat(g)']

    return df, avg_macros, top_protein

# Takes calculated metrics and uploads CSV and Visualizations to the "outputs" blob container in Azure
def generate_outputs(df, avg_macros, top_protein):
    # ---- Upload CSV Metrics ----
    upload_to_blob("outputs", "average_macros_by_diet.csv", avg_macros.to_csv().encode())
    upload_to_blob("outputs", "top5_protein_recipes_by_diet.csv", top_protein.to_csv(index=False).encode())
    upload_to_blob("outputs", "processed_data_with_metrics.csv", df.to_csv(index=False).encode())


    # ---- Visualizations ----
    # Bar Chart
    buf = io.BytesIO()
    plt.figure(figsize=(10,6))
    avg_macros.plot(kind='bar')
    plt.title('Average Macronutrient Content by Diet Type')
    plt.tight_layout()
    plt.savefig(buf, format='png')
    buf.seek(0)
    upload_to_blob("outputs", "avg_macros_bar_chart.png", buf.read())
    plt.close()

    # Heatmap
    buf = io.BytesIO()
    plt.figure(figsize=(8,6))
    sns.heatmap(avg_macros, annot=True, cmap='YlGnBu', fmt=".2f")
    plt.tight_layout()
    plt.savefig(buf, format='png')
    buf.seek(0)
    upload_to_blob("outputs", "macronutrient_heatmap.png", buf.read())
    plt.close()

    # Scatter Plot
    buf = io.BytesIO()
    plt.figure(figsize=(10,6))
    sns.scatterplot(
        data=top_protein,
        x='Cuisine_type',
        y='Protein(g)',
        hue='Diet_type',
        size='Protein(g)',
        sizes=(50, 300),
        alpha=0.7
    )
    plt.tight_layout()
    plt.savefig(buf, format='png')
    buf.seek(0)
    upload_to_blob("outputs", "top5_protein_scatter.png", buf.read())
    plt.close()

    print("[INFO] CSVs and visualizations uploaded successfully")