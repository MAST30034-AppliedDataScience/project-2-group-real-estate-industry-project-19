# Generic Real Estate Consulting Project
Groups should generate their own suitable `README.md`.

See the `scrape.py` file in the `scripts` directory to get started scraping data. 

**Name:** Mary Zhang, Daniel Bi, Telia Tung, Feiyang Gu

**Research Goal: To discover the top 10 subrubs in Victoria with the most projected growth, to find the internal and external factors that influence rental prices the most and to find the most affordable and liveable suburbs**

**Timeline: Sprint 1: Scraping rental data from from public websites, Sprint 2-3: Cleaning and feature engineering our data for preliminary analysis, Sprint 4-5: Creating models to analyse the features and calculating scores for affordability and liveability, Sprint 6-7: Creating graphs and preparing final presentation** 

To run the pipeline, please visit the `notebooks` directory and run the files in order:
1. `download.ipynb`, `population_download_preprocess.ipynb` and `download.py`: This downloads the raw data into the `data/landing` directory.
2. **Preprocessing**: These notebooks details all preprocessing steps and outputs it to the `data/raw` and `data/curated` directory. Does not matter which one is run first.
   1. `preprocessing_historical_rent.ipynb`: Preprocesses historical rent
   2. `preprocessing_income.ipynb`: Preprocesses income data
   3. `preprocessing_proximity.ipynb`: Preprocessing proximity from rentals to feature locations
   4. `preprocessing_rental_scrape.ipynb`: Preprocesses scraped rental data
   5. `merge_income_population.ipynb`: Merge income and population features with the rental dataset
3. **Analysis**: This notebook is used to conduct analysis on the curated data. Please run the below in order.
   1. `analysis_feat_count.ipynb`
   2. `analysis_affordability_and_livability.ipynb`
4. `model.ipynb`: The script is used to run the model from CLI and the notebook is used for analysing and discussing the model.
5. `Summary_notebook.ipynb` for summary
6. `visualization_income_population.ipynb`: Generate heat maps for income and population dataset

