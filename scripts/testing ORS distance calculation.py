import openrouteservice

# Initialize the ORS client with your actual API key
client = openrouteservice.Client(key='5b3ce3597851110001cf6248a051259647f748f29a186d717f60beef')

# Example: Using the client to calculate directions
coordinates = [(144.9631, -37.8136), (144.9514, -37.8172)]  # Example coordinates: Melbourne CBD to Southern Cross Station
route = client.directions(coordinates)

# Output the route distance
distance = route['routes'][0]['summary']['distance']
print(f"Distance: {distance} meters")
