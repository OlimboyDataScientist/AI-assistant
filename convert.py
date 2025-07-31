import pandas as pd
import os

directory = r"E:\TIEJUN DOCUMENTS\HHS-RFI Scanner"

data = pd.read_excel(r"C:\Users\Administrator\Desktop\ALL RFI LOG 04.07.2025.xlsx")
df = data[['Work Section (Location)', 'Department', " Inspection Request for:\n(Type of Inspection)"]]

num = 0
    
    
for root, dirs, files in os.walk(directory):
    for file in files:
        if file.endswith('.pdf'):
            parts = file.split('-')
            if len(parts) > 1 and parts[-1].startswith(parts[0]):
                print(f"Match found: {file}")
