# from flask import Flask, request
import requests
import json
import base64
from keras.models import load_model
import os
from Analysis import detect_wrinkle
from fastapi import FastAPI, HTTPException

app = FastAPI()


@app.post('/')
def index(request: dict):
    """ Receive and parse pubsub request"""
    payload = request

    # check the pubsub request payload
    if not payload:
        msg = "no pubsub payload received"
        print(f"error: {msg}")
        raise HTTPException(400, detail=f"Bad Request:{msg}")
    
    if not isinstance(payload, dict):
        msg = "invalid payload format"
        print(f"error: {msg}")
        raise HTTPException(400, detail=f"Bad Request:{msg}")
    
    # decode pubsub message
    pubsub_message = payload["message"]

    if isinstance(pubsub_message, dict) and "data" in pubsub_message:
        try:
            data = json.loads(base64.b64decode(pubsub_message["data"]).decode())
        except Exception as e:
            msg = (
                "Invalid Pub/Sub message: "
                "data property is not valid base64 encoded JSON"
            )
            print(f"error: {e}")
            raise HTTPException(400, detail=f"Bad Request:{e}")
        
        if not data["name"] or not data["bucket"]:
            msg = (
                "Invalid Cloud Storage notification: "
                "expected name and bucket properties"
            )
            print(f"error: {msg}")
            raise HTTPException(400, detail=f"Bad Request:{msg}")
        
        try:
            model = load_model('models/model.h5')
            print(f"DEBUG: {model}")
            detect_wrinkle(data, model, 0.5)
            return ("", 204)
        except Exception as e:
            print(f"DEBUG: exception when trying to detect acne. Error message: {e}")
            raise HTTPException(500, detail="")
        
    raise HTTPException(500, detail="")

@app.get('/')
def example():
    return "hello world"