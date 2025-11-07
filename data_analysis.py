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

def run_analysis():
    connection_string = os.environ['AzureWebJobsStorage']
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    # Load dataset
    container_client = blob_service_client.get_container_client("datasets")
    blob_data = container_client.download_blob("All_Diets.csv").readall()
    df = pd.read_csv(io.BytesIO(blob_data))

    # Data cleaning
    if 'Diet_type' in df.columns:
        df['Diet_type'] = df['Diet_type'].str.strip().str.title()
    if 'Cuisine_type' in df.columns:
        df['Cuisine_type'] = df['Cuisine_type'].str.strip().str.title()
    numeric_cols = ['Protein(g)', 'Carbs(g)', 'Fat(g)']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].mean())
    df = df.fillna('Unknown')

    # Metrics
    avg_macros = df.groupby('Diet_type')[['Protein(g)', 'Carbs(g)', 'Fat(g)']].mean()
    top_protein = df.sort_values('Protein(g)', ascending=False).groupby('Diet_type').head(5)
    df['Protein_to_Carbs_ratio'] = df['Protein(g)'] / df['Carbs(g)']
    df['Carbs_to_Fat_ratio'] = df['Carbs(g)'] / df['Fat(g)']

    # Upload CSVs
    upload_to_blob("outputs", "average_macros_by_diet.csv", avg_macros.to_csv(index=True).encode())
    upload_to_blob("outputs", "top5_protein_recipes_by_diet.csv", top_protein.to_csv(index=False).encode())
    upload_to_blob("outputs", "processed_data_with_metrics.csv", df.to_csv(index=False).encode())

    # Visualizations
    # Bar chart
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

    # Scatter plot
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

    print("[INFO] Analysis complete and all outputs uploaded.")

    #Return status and summary for testing endpoint
    uploaded_files = [
        "average_macros_by_diet.csv",
        "top5_protein_recipes_by_diet.csv",
        "processed_data_with_metrics.csv",
        "avg_macros_bar_chart.png",
        "macronutrient_heatmap.png",
        "top5_protein_scatter.png"
    ]

    return {
        "status": "success",
        "rows_processed": len(df),
        "uploaded_files": uploaded_files
    }
