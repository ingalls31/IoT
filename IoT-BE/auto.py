import os
import django
import joblib
import pandas as pd
import time


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iot.settings')
django.setup()

from message.models import Cache
from django.core.mail import EmailMessage
from django.core.mail import send_mail

   
while True:
    while Cache.objects.get(key='status').value == '1':
        model = joblib.load('RFC_model.joblib')
        CropDays = 24.0
        temperature = 40.0
        soilMoisture = 600.0
        humidity = 30.0
        features = pd.DataFrame({
            'CropType': [0],
            'CropDays': [CropDays],
            'SoilMoisture': [soilMoisture],
            'temperature': [temperature],
            'Humidity': [humidity]
        })
        predict = model.predict(features)
        if predict == 1:
            data_demo = {
                "CropDays": 24,
                "SoilMoisture": 600,
                "Temperature": 40,
                "Humidity": 30,
            }
            subject = "Báo cáo"
            message = f"""
            "Tuổi cây (CropDays)": {data_demo['CropDays']},
            "Độ ẩm đất (SoilMoisture)": {data_demo['SoilMoisture']},
            "Nhiệt độ (Temperature)": {data_demo['Temperature']},
            "Độ ẩm không khí (Humidity)": {data_demo['Humidity']},
            """
            from_email = "kainnoowa2303@gmail.com"
            recipient_list = ['huy52670@gmail.com']
            email = EmailMessage(subject, message, from_email, recipient_list)
            email.send()
        time.sleep(60)