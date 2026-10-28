# TasteMatch Dataset Setup

TasteMatch uses the Kaggle [Restaurant Recommendations dataset](https://www.kaggle.com/datasets/samayashar/restaurant-recommendations).

## 1. Dataset Files

Place the CSV files in the `data/` directory:

- `restaurants.csv`: restaurant IDs, names, cuisines, prices, ratings, and locations.
- `interactions.csv`: user interactions with restaurants, including clicks, likes, visits, and reviews.
- `users.csv`: user information.
- `context.csv`: contextual information.
- `social_graph.csv`: user relationship data.

Keep the original CSV files locally. Do not publish the raw dataset unless its license permits redistribution.

## 2. Interaction Data

The current `interactions.csv` contains the following columns:

- `user_id`
- `restaurant_id`
- `interaction_type`
- `timestamp`

The available interaction types are `click`, `like`, `visit`, and `review`.

These records represent implicit feedback, not explicit numeric ratings. They must not be treated as 1–5 star ratings without a documented modeling assumption.

## 3. Loading Restaurant Data

To load the restaurant records into the configured database, run:

```powershell
python import_restaurants.py
```

Run this command from the project root after configuring the database connection and installing the dependencies.

## 4. Recommendation Limitations

- Interaction-based recommendations can use behavioral signals to estimate user preferences.
- A `like` can be treated as a positive signal. Clicks and visits can represent different levels of engagement.
- A `review` indicates engagement but does not necessarily mean the user liked the restaurant.
- Explicit rating prediction requires actual numeric rating data.
- Location-based filtering depends on the availability of restaurant coordinates.
- Contextual and social information should only be incorporated when the recommendation model explicitly supports those features.

## 5. Reproducibility

Keep the original column names and document any transformations applied during data preparation. Evaluate recommendation quality using an appropriate ranking or recommendation metric before claiming model performance.