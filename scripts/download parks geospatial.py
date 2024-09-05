import requests
import zipfile
import io
import os

# Step 1: URL for the Parks and Reserves shapefile
url = "https://data.casey.vic.gov.au/api/v2/catalog/datasets/parks-and-reserves1/exports/shp"

# Step 2: Send a request to download the file
response = requests.get(url)

# Step 3: Check if the request was successful
if response.status_code == 200:
    print("Download successful, extracting the file...")
    
    # Step 4: Open the downloaded zip file in memory and extract its contents
    zip_file = zipfile.ZipFile(io.BytesIO(response.content))
    extract_path = "parks_and_reserves_shapefile"
    zip_file.extractall(extract_path)
    
    # Step 5: Verify the extracted files
    extracted_files = os.listdir(extract_path)
    print("Extracted files:", extracted_files)
else:
    print("Failed to download the shapefile. Status code:", response.status_code)
    
    






import geopandas as gpd
import matplotlib.pyplot as plt

# Step 1: Load the shapefile
shapefile_path = "parks_and_reserves_shapefile/parks-and-reserves1.shp"  # Adjust the path as needed
gdf = gpd.read_file(shapefile_path)

# Step 2: Create the plot
fig, ax = plt.subplots(figsize=(10, 10))
gdf.plot(ax=ax, edgecolor='k', color='green')
plt.title('Parks and Reserves in Victoria')

# Step 3: Save the plot to a file
output_path = "parks_and_reserves_visualization.png"
plt.savefig(output_path, dpi=300)  # Save as a PNG with 300 DPI for high quality

# Optionally, you can also display the plot
# plt.show()

