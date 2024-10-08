from prophet import Prophet
import matplotlib as plt
import pandas as pd
import os
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from pmdarima import auto_arima 
from statsmodels.tsa.statespace.sarimax import SARIMAX
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_squared_error
import seaborn as sns
import pandas as pd
import numpy as np
import os
from statsmodels.tsa.statespace.sarimax import SARIMAX
import matplotlib.pyplot as plt

# Function for SARIMA modeling and forecasting for each suburb and property type
def forecast_sarima(df):
    results = []
    no_results = 0

    # Loop over unique Suburb and Property_Type combinations
    unique_combinations = df[['Suburb', 'Property_Type']].drop_duplicates()

    for _, row in unique_combinations.iterrows():
        suburb = row['Suburb']
        prop_type = row['Property_Type']
        print(f"Processing: {suburb} - {prop_type}")

        # Subset the data for this suburb and property type
        subset = df[(df['Suburb'] == suburb) & (df['Property_Type'] == prop_type)]

        # Sort data by date and ensure monthly frequency
        subset = subset.sort_values(by='Date').set_index('Date')

        # Handle duplicate dates by aggregating them (e.g., using mean)
        # Only aggregate numeric columns
        numeric_cols = subset.select_dtypes(include=[np.number]).columns
        subset = subset.groupby(subset.index)[numeric_cols].mean()
        
        subset = subset[['Rent']]

        # Handle NaN values (impute or drop)
        subset = subset.fillna(method='ffill').dropna()

        # Ensure data is non-empty and has sufficient length
        if subset.empty or len(subset) < 36:  # Skip if not enough data for a 3-year forecast
            print(f"Skipping {suburb} - {prop_type} due to insufficient data")
            continue

        # Fit SARIMA model
        try:
            model = SARIMAX(subset, order=(1,1,1), seasonal_order=(1,1,1,12))
            sarima_fit = model.fit(disp=False)

            # Forecast the next 36 months (3 years)
            forecast = sarima_fit.get_forecast(steps=36)
            forecast_dates = pd.date_range(subset.index[-1], periods=37, freq='M')[1:]
            forecast_values = forecast.predicted_mean

            # Store results in a DataFrame
            forecast_df = pd.DataFrame({
                'Suburb': suburb,
                'Property_Type': prop_type,
                'Date': forecast_dates,
                'Forecasted_Rent': forecast_values
            })
            results.append(forecast_df)

            # Plot the forecast
            plt.figure(figsize=(10, 6))
            plt.plot(subset.index, subset['Rent'], label='Actual Rent')
            plt.plot(forecast_dates, forecast_values, label='Forecasted Rent', color='orange')
            plt.title(f"SARIMA Rent Forecast for {suburb} - {prop_type}")
            plt.xlabel('Date')
            plt.ylabel('Rent')
            plt.legend()
            
            # Save the plot
            suburb_folder = f"../plots/modelling_plots/{suburb.replace(' ', '_')}/"
            os.makedirs(suburb_folder, exist_ok=True)
            plt.savefig(f"{suburb_folder}{suburb.replace(' ', '_')}_{prop_type.replace(' ', '_')}_forecast.png")
            plt.close()

        except Exception as e:
            print(f"Failed to fit SARIMA model for {suburb} - {prop_type}: {str(e)}")
            no_results += 1

    # Combine all forecast results into a single DataFrame
    if results:
        forecast_results_df = pd.concat(results, axis=0)
        return forecast_results_df
    else:
        raise ValueError(f"No forecasts were generated. {no_results} suburb-property combinations failed.")