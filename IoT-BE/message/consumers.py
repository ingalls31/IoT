import json
import boto3
import schedule
import time
import joblib
import pandas as pd
from datetime import datetime
from asyncio import sleep
from boto3.dynamodb.conditions import Key
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from asgiref.sync import async_to_sync
from message.models import Cache
from django.core.mail import EmailMessage
from django.core.mail import send_mail
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ESP32_AWSDB_db')
client = boto3.client('iot-data')



class SensorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.sensors_group_name = 'sensor_group'
        await self.channel_layer.group_add(
            self.sensors_group_name,
            self.channel_name
        )
        await self.accept()
        while True:             
            timestamp_gmt7 = int(datetime.now().timestamp())+25190
            response = table.query(
                KeyConditionExpression=Key("Timestamp").eq(timestamp_gmt7)
            )
            items = response['Items']
            if items:
                temperature = float(items[0]['Temperature'])
                humidity = float(items[0]['Humidity'])
                soilmoisture = float(items[0]['SoilMoisture'])
                await self.send(json.dumps({
                    'temperature': temperature,
                    'humidity': humidity,
                    'soilmoisture': soilmoisture
                }))
            await sleep(1)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.sensors_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        pass

    async def message(self, event):
        pass


class RelayConsumer(WebsocketConsumer):
    status = 0

    def connect(self):
        self.relay_group_name = "relay"
        async_to_sync(self.channel_layer.group_add)(
            self.relay_group_name,
            self.channel_name
        )
        self.accept()
        try:
            cache_status = Cache.objects.get(key="status")
        except:
            cache_status = Cache.objects.create(key='status', value=0)
        self.status = int(cache_status.value)
        async_to_sync(self.channel_layer.group_send)(
            self.relay_group_name,
            {
                "type": "message",
                "message": self.status,
            },
        )

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.relay_group_name,
            self.channel_name
        )

    def receive(self, text_data=None, bytes_data=None):
        print(text_data)
        try:
            if int(text_data) in [0, 1]:
                self.status = int(text_data)
                Cache.objects.update(key='status', value=str(self.status))
                client.publish(
                    topic='ESP32_AWSDB/sub',
                    qos=1,
                    payload=json.dumps({"message": str(self.status)})
                )
                if self.status == 1:
                    print('pass')
                    data_demo = {
                        "CropDays": 10,
                        "SoilMoisture": 400,
                        "Temperature": 30,
                        "Humidity": 15,
                    }
                    subject = "Báo cáo"
                    message = f"""
                    "Tuổi cây (CropDays)": {data_demo['CropDays']},
                    "Độ ẩm đất (SoilMoisture)": {data_demo['SoilMoisture']},
                    "Nhiệt độ (Temperature)": {data_demo['Temperature']},
                    "Độ ẩm không khí (Humidity)": {data_demo['Humidity']},
                    """
                    from_email = "kainnoowa2303@gmail.com"
                    recipient_list = ['kainnoowa2303@gmail.com']
                    # email = EmailMessage(subject, message, from_email, to_email)
                    # email.send()
                    send_mail(subject, message, from_email,
                              recipient_list, fail_silently=False)
        except Exception as e:
            print(str(e))
        async_to_sync(self.channel_layer.group_send)(
            self.relay_group_name,
            {
                "type": "message",
                "message": self.status,
            },
        )

    def send(self, text_data=None, bytes_data=None, close=False):
        return super().send(text_data, bytes_data, close)

    def message(self, event):
        message = event["message"]
        self.send(
            text_data=json.dumps(
                message
            )
        )


class AutoMLConsumer(WebsocketConsumer):
    status = 0

    def connect(self):
        self.relay_group_name = "ml"
        async_to_sync(self.channel_layer.group_add)(
            self.relay_group_name,
            self.channel_name
        )
        self.accept()
        try:
            cache_status = Cache.objects.get(key="status")
        except:
            cache_status = Cache.objects.create(key='status', value=0)
        self.status = int(cache_status.value)
        async_to_sync(self.channel_layer.group_send)(
            self.relay_group_name,
            {
                "type": "message",
                "message": self.status,
            },
        )

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.relay_group_name,
            self.channel_name
        )

    def receive(self, text_data=None, bytes_data=None):
        try:
            if int(text_data) in [0, 1]:
                self.status = int(text_data)
                Cache.objects.update(key='status', value=str(self.status))
                    
        except Exception as e:
            print(str(e))
        async_to_sync(self.channel_layer.group_send)(
            self.relay_group_name,
            {
                "type": "message",
                "message": self.status,
            },
        )

    def send(self, text_data=None, bytes_data=None, close=False):
        super().send(text_data, bytes_data, close)

    def message(self, event):
        message = event["message"]
        self.send(
            text_data=json.dumps(
                message
            )
        )

    def job(self, text):
        client.publish(
            topic='ESP32_AWSDB/sub',
            qos=1,
            payload=json.dumps({"message": text})
        )
