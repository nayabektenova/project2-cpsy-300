import azure.functions as func
import io
import pandas as pd
from data_analysis import process_csv, generate_outputs

def main(myblob: func.InputStream):
    print(f"[BLOB TRIGGER] {myblob.name} updated")

    df = pd.read_csv(io.BytesIO(myblob.read()))

    clean_df, avg_macros, top_protein = process_csv(df)

    generate_outputs(clean_df, avg_macros, top_protein)

    print("[BLOB TRIGGER] Processing complete")
