import os
from decouple import config

# OpenAI API Key
OPENAI_API_KEY = config('OPENAI_API_KEY', default=None)

# Supabase
SUPABASE_URL = config('SUPABASE_URL', default=None)
SUPABASE_KEY = config('SUPABASE_KEY', default=None)

# Firebase
FIREBASE_CONFIG = {
    "apiKey": config('FIREBASE_API_KEY', default=None),
    "authDomain": config('FIREBASE_AUTH_DOMAIN', default=None),
    "projectId": config('FIREBASE_PROJECT_ID', default=None),
    "storageBucket": config('FIREBASE_STORAGE_BUCKET', default=None),
    "messagingSenderId": config('FIREBASE_MESSAGING_SENDER_ID', default=None),
    "appId": config('FIREBASE_APP_ID', default=None)
}