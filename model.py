import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import MinMaxScaler

def predict_next_days(df, days=7):
    df = df.copy()
    df['SMA20'] = df['Close'].rolling(20).mean()
    df['SMA50'] = df['Close'].rolling(50).mean()
    df['Lag1'] = df['Close'].shift(1)
    df['Lag2'] = df['Close'].shift(2)
    df['Lag3'] = df['Close'].shift(3)
    df['Lag5'] = df['Close'].shift(5)
    df.dropna(inplace=True)

    features = ['SMA20', 'SMA50', 'Lag1', 'Lag2', 'Lag3', 'Lag5']
    X = df[features].values
    y = df['Close'].values

    # Train on all data for prediction
    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X, y)
    score = model.score(X, y)

    # Predict future
    last_row = X[-1].copy().astype(float)
    predictions = []
    for _ in range(days):
        pred = model.predict(last_row.reshape(1, -1))[0]
        predictions.append(pred)
        last_row[2] = last_row[3]
        last_row[3] = last_row[4]
        last_row[4] = pred

    return predictions, score