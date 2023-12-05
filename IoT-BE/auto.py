import os
import django
import joblib
import pandas as pd
import time


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iot.settings')
django.setup()
import json
from message.models import Cache
from django.core.mail import send_mail
from datetime import datetime
from boto3.dynamodb.conditions import Key
from pytz import timezone
import boto3
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ESP32_AWSDB_db')
ddb = boto3.client('dynamodb')
client = boto3.client('iot-data')
lst = []
dayOfWeek = ['Monday', 'Tuesday', 'Wednesday',
             'Thursday', 'Friday', 'Saturday', 'Sunday']
label_encoder = ['Wheat', 'Groundnuts', 'Garden Flower',
                 'Maize', 'Paddy', 'Potato', 'Pulse', 'Sugarcane', 'Coffee']
mlwater = [120, 192, 96, 144, 168, 192, 216, 120, 144]


def job(text):
    client.publish(
        topic='ESP32_AWSDB/sub',
        qos=1,
        payload=json.dumps({"message": text})
    )


while True:
    while Cache.objects.get(key='auto').value == '1':

        haNoiTz = timezone("Asia/Ho_Chi_Minh")
        dt = datetime.now(haNoiTz)
        ts = int(dt.timestamp())+25200
        date = dayOfWeek[dt.weekday()]+" "+dt.strftime("%Y-%m-%d %H:%M:%S")
        cropday = int((ts-1699772400)/86400)
        resp = table.scan(
            ProjectionExpression='TS'
        )
        result = resp['Items']
        while 'LastEvaluateKey' in resp:
            resp = table.scan(
                ProjectionExpression='TS',
                ExclusiveStartKey=resp['LastEvaluateKey'])
            result.extend(resp['Items'])
        latest_record = max(result, key=lambda d: d['TS'])
        response = table.query(
            KeyConditionExpression=Key("TS").eq(latest_record['TS'])
        )
        items = response['Items']
        Crop = int(Cache.objects.get(key='tree').value)
        print(Crop)
        model = joblib.load('RFC_model.joblib')
        features = pd.DataFrame({
            'CropType': [Crop],
            'CropDays': [items[0]['CropDays']],
            'SoilMoisture': [items[0]['SoilMoisture']],
            'temperature': [items[0]['temperature']],
            'Humidity': [items[0]['Humidity']]
        })
        predict = model.predict(features)
        if predict == 1:
            job('1')
            time.sleep(int(mlwater[Crop]/24))
            job('0')
            item = {
                'TS': {
                    'N': str(ts)
                },
                'DayWater': {
                    'S': date
                },
                'CropDays': {
                    'N': str(cropday)
                },
                'CropType': {
                    'S': label_encoder[Crop]
                },
                'Humidity': {
                    'N': str(items[0]['Humidity'])
                },
                'Irrigation': {
                    'N': str(1)
                },
                'SoilMoisture': {
                    'N': str(items[0]['SoilMoisture'])
                },
                'temperature': {
                    'N': str(items[0]['temperature'])
                },
                'Water': {
                    'N': str(120)
                }
            }
            ddb.put_item(TableName='ESP32_AWSDB_db', Item=item)
            subject = "Tưới tự động"
            message = f"""
            "Thời điểm tưới": {date},
            "Tuổi cây (CropDays)": {cropday},
            "Cây (CropType)": {label_encoder[Crop]},
            "Độ ẩm đất (SoilMoisture)": {float(100-items[0]['SoilMoisture']/10)}%,
            "Nhiệt độ (Temperature)": {items[0]['temperature']}℃,
            "Độ ẩm không khí (Humidity)": {items[0]['Humidity']}%,
            "Lượng nước tưới": {mlwater[Crop]} ml,
            """
            from_email = "kainnoowa2303@gmail.com"
            recipient_list = ['kainnoowa2303@gmail.com']
            send_mail(subject, message, from_email,
                      recipient_list, fail_silently=False)
        time.sleep(3600)
