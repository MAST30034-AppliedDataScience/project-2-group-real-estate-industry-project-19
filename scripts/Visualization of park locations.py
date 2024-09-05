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
