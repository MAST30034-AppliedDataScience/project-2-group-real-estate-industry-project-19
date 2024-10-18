import pandas as pd
import geopandas as gpd
import numpy as np
from sklearn.metrics.pairwise import haversine_distances

def feat_sf (shapefile, feature_name, feat_type = None, feat_subtypes = None):
    """
    Cleaning shapefiles and dataframes for features we want.

    Args:
        shapefile (gpd.Geodataframe or pd.dataframe): the file with information on neighbourhood features
        feature_name (str): name of the feature
        feat_type (str or list, optional): any specific types of feature we want. Defaults to None.
        feat_subtypes (list, optional): feature subtypes, for example, a chicken is a subtype of a bird . Defaults to None.

    Raises:
        ValueError: feature name is wrong and not mentioned

    Returns:
        gpd.Geodataframe or pd.dataframe: the cleaned shapefile or dataframe
    """
    if feature_name in ("primary_school", "secondary_school", "school"):
        if feat_subtypes != None:
            raise ValueError("feat_subtypes must be none for school gdfs.")
        if feat_type == None and feature_name == "school":
            filtered_sf = shapefile.copy()
        elif feat_type != None and feature_name in ("primary_school", "secondary_school"):
            filtered_sf = shapefile[shapefile['School_Type'].isin(feat_type)]
        else: 
            raise ValueError("feat_type must be none for feature_name = \"school\" or \
                must have feat_type for to specify type of school.")
        # Renaming columns for ease of use for future functions
        filtered_sf = filtered_sf.rename(columns={'School_Name': 'NAME'})
        # Convert the school data into a GeoDataFrame using the Y (latitude) and X (longitude) columns
        filtered_sf = filtered_sf.rename(columns={'Y': 'latitude'})
        filtered_sf = filtered_sf.rename(columns={'X': 'longitude'})
        filtered_sf['geometry'] = gpd.points_from_xy(filtered_sf['longitude'], filtered_sf['latitude'])
        filtered_sf = gpd.GeoDataFrame(filtered_sf, geometry='geometry')
        filtered_sf = filtered_sf.set_crs(epsg=4326, inplace=True)
    else:
        if feature_name == "train_station":
            if feat_subtypes != None or feat_type != None:
                raise ValueError("Both feat_type and feat_subtypes must be none.")
            filtered_sf = shapefile[shapefile['STATUS'] == "Active"]
            # Renaming columns for ease of use for future functions
            filtered_sf = filtered_sf.rename(columns={'STATION': 'NAME'})
        elif feature_name in ("shopping", "parks", "hospital"):
            if feat_subtypes == None or feat_type == None:
                raise ValueError("Both feat_type and feat_subtypes must have value.")
            # We only want features in VIC
            filtered_sf = shapefile[shapefile['STATE'] == "VIC"]
            filtered_sf = filtered_sf[filtered_sf['FTYPE'] == feat_type]
            filtered_sf = filtered_sf[filtered_sf['FEATSUBTYP'].isin(feat_subtypes)]
        else:
            raise ValueError("Invalid feature_name provided.")
            # Setting shapefile format
        filtered_sf['geometry'] = filtered_sf['geometry'].to_crs("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")
        # Creating an array of centroids of polygons in the feature shapefiles
        filtered_sf['centroid'] = filtered_sf['geometry'].centroid.apply(lambda geom: (geom.y, geom.x))
        filtered_sf['latitude'] = filtered_sf['centroid'].apply(lambda coord: coord[0])
        filtered_sf['longitude'] = filtered_sf['centroid'].apply(lambda coord: coord[1])
    
    filtered_sf = filtered_sf.dropna(subset=['latitude', 'longitude']).copy()
    filtered_sf = filtered_sf.to_crs(epsg=4326)
    return filtered_sf.reset_index(drop=True)

def coord_radian_array (input_data):
    """
    Creates a numpy array of radians to use for Haversine distance calculations

    Args:
        input_data (pd.DataFrame, gpd.GeoDataFrame, list or tuple): getting the coordinates from dataframe,
                                                                    or converting the sole coordinate to an array

    Raises:
        ValueError: wrong type of input, or is not a single coordinate

    Returns:
        np.array: array of radians
    """
    # Check if the input is a DataFrame using type()
    if (type(input_data) == pd.DataFrame or type(input_data) == gpd.GeoDataFrame) and \
       ("latitude" in input_data.columns and "longitude" in input_data.columns):
       # Convert the latitude and longitude to separate numpy arrays
        lattitudes = np.radians(input_data['latitude'].to_numpy())
        longtitudes = np.radians(input_data['longitude'].to_numpy())
        
        # Combine latitudes and longitudes into a 2D array of radians
        coordinate = np.column_stack((lattitudes, longtitudes))
    elif (type(input_data) == list or type(input_data) == tuple) and len(input_data) == 2:
        # Turn the one coordinate into a 2D array, and turn it into a radian value
        coordinate = np.radians(np.array([input_data]))
    else:
        # Error if unexpected type of data or does not have the appropiate columns
        raise ValueError("Input must be a DataFrame with 'latitude' and 'longitude' columns or a \
                         list/tuple of coordinates [latitude, longitude].")
         
    return coordinate

def rental_haversine_closest(rental_df, feature_data, feature_name):
    """
    Calculate the distance, and for features with multiple coordinates, picks the closest one.

    Args:
        rental_df (pd.DataFrame): Rental data and coordinates
        feature_data (pd.DataFrame, gpd.GeoDataFrame, list or tuple): coordinates and info on features
        feature_name (str): Name of feature

    Returns:
        pd.DataFrame: rental dataframe with info on distance and additional data
    """
    global nearest_distance
    
    # Turning info into radian arrays
    feat_radians = coord_radian_array(feature_data)
    rental_radians = coord_radian_array(rental_df)

    # Used Haversine distance as the earth's curve may affect distance 
    distances_radians = haversine_distances(feat_radians, rental_radians)
    distances_km = distances_radians * 6371
    
    # If only one coordinate
    if (type(feature_data) == list or type(feature_data) == tuple) and len(feature_data) == 2:
        nearest_distance = distances_km[0, :] 
    
    # If a set of coordinates
    elif type(feature_data) == pd.DataFrame or type(feature_data) == gpd.GeoDataFrame:
        # Grabbing the id of the nearest feature
        nearest_point_id = np.argmin(distances_km, axis=0)
        # Grabbing distance between the rental and the nearest feature
        nearest_distance = np.min(distances_km, axis=0)

        # Add the name, latitude, longitude and distance of the closest feature from the rental
        rental_df[f'nearest_{feature_name}_name'] = feature_data.loc[nearest_point_id, 'NAME'].values
        rental_df[f'nearest_{feature_name}_name'] = rental_df[f'nearest_{feature_name}_name'].str.title()
        # If feautre is schools, add school type
        if feature_name in ("primary_school", "secondary_school"):
            rental_df[f'nearest_{feature_name}_type'] = feature_data.loc[nearest_point_id, 'Education_Sector'].values
        rental_df[f'nearest_{feature_name}_latitude'] = feature_data.loc[nearest_point_id, 'latitude'].values
        rental_df[f'nearest_{feature_name}_longitude'] = feature_data.loc[nearest_point_id, 'longitude'].values

    # Add distance  
    rental_df[f'straight_line_distance_{feature_name}'] = nearest_distance
    return rental_df

# Calculate the driving route distance using Google Maps API
def calculate_route_distance(property_coords, destination_coords, gmaps_client):
    """
    Uses google maps api to look up the route distance in km

    Args:
        property_coords (float): coordinates of the rental property
        destination_coords (float): coordinates of the feature/desitnation
        gmaps_client (API): google maps API connection

    Returns:
        int: route distance in km
    """
    try:
        # Request the driving distance between the property and the closest train station
        result = gmaps_client.distance_matrix(origins=[property_coords], destinations=[destination_coords], mode="driving")
        
        # Check if the result is valid
        if result['rows'][0]['elements'][0]['status'] == 'OK':
            distance = result['rows'][0]['elements'][0]['distance']['value']  # Distance in meters
            return distance / 1000  # Convert from meters to kilometers
        else:
            print(f"No valid route distance found for {property_coords} to {destination_coords}: {result['rows'][0]['elements'][0]['status']}")
            return None
    except Exception as e:
        print(f"Error calculating route distance for {property_coords}: {e}")
        return None

def route_dist_and_save_csv(rental_df, feature_name, save_to_dir, gmaps_client, single_dest_coord = None):
    """
    Iterate through rows of a rental_df, then apply route (driving distance) calculation from
    each rental property to each feature in km.

    Args:
        rental_df (pd.dataframe): cleaned rental df with the closest feature listed with haversine distance
        feature_name (str): name of feature to save as
        save_to_dir (str): directory to save to
        gmaps_client (googlemaps.Client): google maps api to calculate distances
        single_dest_coord (list or tuple, optional): If only 1 destination is given instead of multiple(e.g. CBD). Defaults to None.

    Returns:
        pd.dataframe: final rental df with route distance calculated
    """
    
    # Create null column
    rental_df[f'route_distance_{feature_name}'] = np.nan

    # Iterate through each row 
    for index, rental in rental_df.iterrows():
        # Sacing coordinate
        property_coord = (rental['latitude'], rental['longitude'])
        if single_dest_coord != None:
            feat_coord = tuple(single_dest_coord)
        else:
            feat_coord = (rental[f'nearest_{feature_name}_latitude'], rental[f'nearest_{feature_name}_longitude'])
        # Calculate route distance
        route_distance = calculate_route_distance(property_coord, feat_coord, gmaps_client)
        rental_df.at[index, f'route_distance_{feature_name}'] = route_distance
        
        if (index + 1) % 100 == 0:
            print(f"Processed {index + 1} rows, saving progress...")
            rental_df.to_csv(f"{save_to_dir}rental_with_{feature_name}.csv", index=False)
            
    # Final save after processing all data
    rental_df.to_csv(f"{save_to_dir}rental_with_{feature_name}.csv", index=False)
    return rental_df