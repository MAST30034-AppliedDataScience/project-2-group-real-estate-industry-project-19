# Generic Real Estate Consulting Project
Groups should generate their own suitable `README.md`.

See the `scrape.py` file in the `scripts` directory to get started scraping data. 

**Name:** Mary Zhang, Daniel Bi, Telia Tung, Feiyang Gu

**Research Goal:**

**Timeline:** 

To run the pipeline, please visit the `notebooks` directory and run the files in order:
1. `download.ipynb`: This downloads the raw data into the `data/landing` directory.
2. **Preprocessing**: These notebooks details all preprocessing steps and outputs it to the `data/raw` and `data/curated` directory. Does not matter which one is run first.
   a. 'preprocessing_historical_rent.ipynb': Preprocesses historical rent
   b. 'preprocessing_income.ipynb': Preprocesses income data
   c. 'preprocessing_proximity.ipynb': Preprocessing proximity from rentals to feature locations
   d. 'preprocessing_rental_scrape.ipynb': Preprocesses rentals
3. **Analysis**: This notebook is used to conduct analysis on the curated data.
   a. 'analysis_affordability_and_livability.ipynb'
   b. 'analysis_feat_count.ipynb'
4. `model.ipynb`: The script is used to run the model from CLI and the notebook is used for analysing and discussing the model.

