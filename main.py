# Command prompt to run inside the treminal:
# uvicorn main:app --reload

# Imports:
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, ConfigDict, Field, field_validator
import joblib
import pandas as pd
from typing import Literal, Optional
import os
from auth import (
    UserAuth, TokenResponse, register_new_user, authenticate_user, 
    create_access_token, verify_token, ACCESS_TOKEN_EXPIRE_MINUTES
)
from datetime import timedelta

# Initializing the app:
app = FastAPI(
    title="Customer Churn Prediction",
    description="THE MOST VIOLENT, DIABOLICAL, THE GOAT OF ALL GOATS: Churn Predictor API 😈"
)

# Robust Model Loading:
# A variable which is defined in all caps, will be constant and will not be changed again.
MODEL_PATH = 'DT_Extra_Proj_1.joblib'   #This is a constant variable.

if not os.path.exists(MODEL_PATH):
    # Stop the app immediately if the model is missing
    raise FileNotFoundError(f"⚠️ Model file not found at {MODEL_PATH}")

model = joblib.load(MODEL_PATH)

# Input Schema (Defining the input format):
class CustomerData(BaseModel):

    # This turns on "Flexible Mode": So if user sends 'Age', it works. But if user sends 'age', it will also work too. 
    model_config = ConfigDict(populate_by_name=True)

    '''
    We use underscores (_) here because Python variables can't have spaces.
    Python variables cannot have spaces, but our Machine Learning model's columns (like "Usage Frequency") do have spaces.
    If we just rename `usage_frequency` to `Usage Frequency`, Python will crash (Syntax Error).💥
    To use model_dump() in prediction endpoint, we must use Aliases. This maps our clean Python variables to the messy column names our model expects.
    These `...` means that the user MUST send the input, or the API will reject the request.
    '''

    age: int = Field(..., alias='Age', ge=3, le=110, example=20)
    gender: str = Field(..., alias='Gender', description="Customer's biological sex", example="Male")
    tenure: float = Field(..., alias='Tenure',ge=1, le=60, example=30.5)
    usage_frequency: float = Field(..., alias='Usage Frequency', ge=1, le=30, example=15.5)
    support_calls: float = Field(..., alias='Support Calls', ge=0, le=10, example=5)
    payment_delay: float = Field(..., alias='Payment Delay', ge=0, le=30, example=15)
    subscription_type: str = Field(..., alias='Subscription Type', description="Tier of the plan subscribed", example="Premium")
    contract_length: str = Field(..., alias='Contract Length', description="Duration of the contract", example="Monthly")
    total_spend: float = Field(..., alias='Total Spend', ge=100, le=1000, example=550)
    last_interaction: float = Field(..., alias='Last Interaction', ge=1, le=30, example=15.5)

    # Validator for Gender:
    @field_validator('gender')
    @classmethod
    def validate_gender(cls, value):
        # Step A: Clean the data:
        # If user sends "  male ", this turns it into "Male" automatically.
        cleaned_value = value.strip().title()
        # Step B: Check the list:
        allowed = {'Male', 'Female'}
        if cleaned_value not in allowed:
            raise ValueError(f"Gender must be one of {allowed}. You sent: {value}")    
        return cleaned_value
    
    # Validator for Subscription:
    @field_validator('subscription_type')
    @classmethod
    def validate_subscription(cls, value):
        cleaned_value = value.strip().title()
        allowed = {'Standard', 'Basic', 'Premium'}
        if cleaned_value not in allowed:
            raise ValueError(f"Subscription must be one of {allowed}. You sent: {value}")
        return cleaned_value

    # Validator for Contract:
    @field_validator('contract_length')
    @classmethod
    def validate_contract(cls, value):
        cleaned_value = value.strip().title()
        allowed = {'Annual', 'Monthly', 'Quarterly'}
        if cleaned_value not in allowed:
            raise ValueError(f"Contract must be one of {allowed}. You sent: {value}")
        return cleaned_value

# Output Schema:
# Defining what we will return:
class Result(BaseModel):
    prediction: str
    risk_level: str

# Prediction Endpoint:
# Add 'username: str = Depends(verify_token)' to lock this route!
@app.post('/predict', response_model=Result)

# By adding `username: str = Depends(verify_token)`, we only make prediction only if 
def predict(data: CustomerData, username: str = Depends(verify_token)):
    
    # Optional: You can now print who is using the model
    print(f"User {username} is making a prediction! 😈")

    # Add a safety net:
    try:

        # `by_alias=True` forces it to use "Usage Frequency" instead of "usage_frequency"
        input_df = pd.DataFrame([data.model_dump(by_alias=True)])

        # Now the DataFrame has the exact columns your model needs!
        # Make Prediction:
        prediction = model.predict(input_df)[0]

        return Result(
            prediction='Churn' if prediction == 1 else 'No Churn',
            risk_level='Critical' if prediction == 1 else 'Safe'
        )
    
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))

# Home Endpoint:
@app.get('/')
def home():
    return {'message': "Churn Predictor is Live! Go to /docs to test it."}

# Auth Endpoints:

# Register Endpoint:
@app.post('/register', response_model=TokenResponse)
def register(user: UserAuth):
    register_new_user(user)
    
    # Auto-login after register
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {'access_token': access_token, 'token_type': 'Bearer', 'expires_in': ACCESS_TOKEN_EXPIRE_MINUTES * 60}

# Login Endpoint:
@app.post('/login', response_model=TokenResponse)
def login(user: UserAuth):
    authenticated_user = authenticate_user(user)
    if not authenticated_user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={'sub': user.username}, expires_delta=access_token_expires
    )
    return {'access_token': access_token, 'token_type': 'Bearer', 'expires_in': ACCESS_TOKEN_EXPIRE_MINUTES * 60}