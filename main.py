from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Literal
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent
model = joblib.load(BASE_DIR / 'Mental_Health_Model.pkl')
dataset = pd.read_csv(BASE_DIR / 'Student Social Media And Mental Health Impact.csv')
top_countries = ['Other','India','USA','Canada','Australia','UK','Germany','Mexico','Turkey','France']

app = FastAPI()
app.mount('/static', StaticFiles(directory=BASE_DIR / 'static'), name='static')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


#A first Pydantic Model
class StudentData(BaseModel):
    age                     : int = Field(..., ge=10, le=100)
    gender                  : Literal['Male', 'Female']
    country                 : str
    academic_level          : Literal['Undergraduate', 'Graduate', 'High School']
    most_used_platform      : Literal['Facebook', 'LinkedIn', 'Instagram', 'Snapchat','Twitter','YouTube', 'TikTok', 'LINE', 'KakaoTalk', 'VKontakte', 'WhatsApp','WeChat']
    purpose_of_use          : Literal['Networking', 'Education', 'Entertainment', 'News']
    avg_daily_usage_hours   : float = Field(..., ge=0, le=24)
    daily_unlocks           : int   = Field(..., ge=0)
    study_hours             : float = Field(..., ge=0, le=24)
    physical_activity_hours : float = Field(..., ge=0, le=24)
    sleep_hours_per_night   : float = Field(..., ge=0, le=24)
    stress_level            : Literal['Medium', 'Low', 'Very High', 'High']




# Describe what we send back
class PredictionResponse(BaseModel):
    predicted_mental_health_score:float
    #6.777777 -> float




@app.get('/')
def greet():
    return FileResponse(BASE_DIR / 'static' / 'index.html')


@app.get('/api/stats')
def stats():
    score_bins = pd.cut(
        dataset['Mental_Health_Score'],
        bins=[0, 5, 7, 8.5, 10],
        labels=['Needs support', 'Steady', 'Strong', 'Thriving'],
        include_lowest=True,
    )
    by_platform = (
        dataset.groupby('Most_Used_Platform', as_index=False)['Mental_Health_Score']
        .mean()
        .sort_values('Mental_Health_Score', ascending=False)
    )
    by_stress = (
        dataset.groupby('Stress_Level', as_index=False)['Mental_Health_Score']
        .mean()
        .sort_values('Mental_Health_Score')
    )
    return {
        'overview': {
            'students': int(len(dataset)),
            'average_score': round(float(dataset['Mental_Health_Score'].mean()), 2),
            'average_usage': round(float(dataset['Avg_Daily_Usage_Hours'].mean()), 2),
            'high_stress_share': round(float((dataset['Stress_Level'] == 'Very High').mean() * 100), 1),
        },
        'score_distribution': [
            {'label': str(label), 'value': int((score_bins == label).sum())}
            for label in score_bins.cat.categories
        ],
        'platforms': [
            {'label': row['Most_Used_Platform'], 'value': round(float(row['Mental_Health_Score']), 2)}
            for _, row in by_platform.head(7).iterrows()
        ],
        'stress_levels': [
            {'label': row['Stress_Level'], 'value': round(float(row['Mental_Health_Score']), 2)}
            for _, row in by_stress.iterrows()
        ],
    }


@app.post('/predict', response_model=PredictionResponse) #6.77777
def predict(data: StudentData):
   
   country_group = data.country if data.country in top_countries else "Other"

   input_row = pd.DataFrame([{
        'Age'                       :data.age,
        'Gender'                    :data.gender,
        'Academic_Level'            :data.academic_level,
        'Most_Used_Platform'        :data.most_used_platform,
        'Purpose_Of_Use'            :data.purpose_of_use,
        'Avg_Daily_Usage_Hours'     :data.avg_daily_usage_hours,
        'Daily_Unlocks'             :data.daily_unlocks,
        'Study_Hours'               :data.study_hours,
        'Physical_Activity_Hours'   :data.physical_activity_hours,
        'Sleep_Hours_Per_Night'     :data.sleep_hours_per_night,
        'Stress_Level'              :data.stress_level,
        'Grouped_Countries'         :country_group
   }])

   prediction = model.predict(input_row)[0] #6.77
   return PredictionResponse(predicted_mental_health_score=round(float(prediction),2))