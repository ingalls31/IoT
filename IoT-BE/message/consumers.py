import json
import boto3
import pandas as pd
from pytz import timezone
from datetime import datetime
from asyncio import sleep
from boto3.dynamodb.conditions import Key, Attr
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from asgiref.sync import async_to_sync
from message.models import Cache
from django.core.mail import send_mail
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ESP32_AWSDB_db')
client = boto3.client('iot-data')
ddb = boto3.client('dynamodb')
dayOfWeek = ['Monday', 'Tuesday', 'Wednesday',
             'Thursday', 'Friday', 'Saturday', 'Sunday']
crop = ['Wheat', 'Groundnuts', 'Garden Flower', 'Maize',
        'Paddy', 'Potato', 'Pulse', 'Sugarcane', 'Coffee']


class SensorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.sensors_group_name = 'sensor_group'
        await self.channel_layer.group_add(
            self.sensors_group_name,
            self.channel_name
        )
        await self.accept()
        while True:
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
            time = items[0]['DayWater'].split()[2]
            temperature = float(items[0]['temperature'])
            humidity = float(items[0]['Humidity'])
            soilmoisture = float(100-items[0]['SoilMoisture']/10)

            await self.send(json.dumps({
                'time': time,
                'temperature': temperature,
                'humidity': humidity,
                'soilmoisture': soilmoisture
            }))
            await sleep(16)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.sensors_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        pass

    async def message(self, event):
        pass


class WaterConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.sensors_group_name = 'water_group'
        await self.channel_layer.group_add(
            self.sensors_group_name,
            self.channel_name
        )
        await self.accept()
        while True:
            now = datetime.now()
            dt = datetime(now.year, now.month, now.day+1, 0, 0, 0)
            ts = int(dt.timestamp()+25200)-86400*7
            resp = table.scan(
                ProjectionExpression='DayWater, Water',
                FilterExpression=Attr('Irrigation').eq(1) & Attr('TS').gt(ts)
            )
            result = resp['Items']
            while 'LastEvaluateKey' in resp:
                resp = table.scan(
                    ProjectionExpression='DayWater, Water',
                    FilterExpression=Attr('Irrigation').eq(
                        1) & Attr('TS').gt(ts),
                    ExclusiveStartKey=resp['LastEvaluateKey'])
                result.extend(resp['Items'])
            for record in result:
                date = record['DayWater'].split()[1]
                date = datetime.strptime(date, '%Y-%m-%d')
                date = date.strftime('%d-%m')
                record['DayWater'] = date
            df = pd.DataFrame(result)
            grouped = df.groupby('DayWater')['Water'].sum().reset_index()
            grouped_dict = grouped.to_dict()
            for key, value in grouped_dict['Water'].items():
                grouped_dict['Water'][key] = int(value)
            await self.send(json.dumps(grouped_dict))
            await sleep(16)

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
    startTime = 0
    d = ""

    def connect(self):
        self.relay_group_name = "relay"
        async_to_sync(self.channel_layer.group_add)(
            self.relay_group_name,
            self.channel_name
        )
        self.accept()
        try:
            cache_status = Cache.objects.get(key='relay')
        except:
            cache_status = Cache.objects.create(key='relay', value=0)
        self.status = int(cache_status.value)
        async_to_sync(self.channel_layer.group_send)(
            self.relay_group_name,
            {
                "type": "message",
                "message": self.status,
            },
        )

    def disconnect(self, close_code):
        cache = Cache.objects.get(key='relay')
        cache.value = str(0)
        cache.save()
        async_to_sync(self.channel_layer.group_discard)(
            self.relay_group_name,
            self.channel_name
        )

    def receive(self, text_data=None, bytes_data=None):
        print(text_data)
        try:
            if int(text_data) in [0, 1]:
                self.status = int(text_data)
                cache = Cache.objects.get(key='relay')
                cache.value = str(self.status)
                cache.save()
                client.publish(
                    topic='ESP32_AWSDB/sub',
                    qos=1,
                    payload=json.dumps({"message": str(self.status)})
                )
                if self.status == 1:
                    haNoiTz = timezone("Asia/Ho_Chi_Minh")
                    dt = datetime.now(haNoiTz)
                    ts = int(dt.timestamp())+25200
                    self.startTime = ts
                    date = dayOfWeek[dt.weekday()]+" " + \
                        dt.strftime("%Y-%m-%d %H:%M:%S")
                    self.d = date
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
                        KeyConditionExpression=Key(
                            "TS").eq(latest_record['TS'])
                    )
                    items = response['Items']
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
                            'S': 'Unknown'
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
                            'N': str(0)
                        }
                    }
                    ddb.put_item(TableName='ESP32_AWSDB_db', Item=item)
                if self.status == 0:
                    haNoiTz = timezone("Asia/Ho_Chi_Minh")
                    dt = datetime.now(haNoiTz)
                    ts = int(dt.timestamp())+25200
                    table.update_item(
                        Key={
                            'TS': self.startTime,
                            'DayWater': self.d
                        },
                        UpdateExpression="SET Water= :s",
                        ExpressionAttributeValues={
                            ':s': (ts-self.startTime)*24
                        },
                    )
                    response = table.query(
                        KeyConditionExpression=Key("TS").eq(self.startTime)
                    )
                    items = response['Items']
                    subject = "Tưới thủ công"
                    message = f"""
                    "Thời điểm tưới": {items[0]['DayWater']},
                    "Tuổi cây (CropDays)": {items[0]['CropDays']},
                    "Cây (CropType)": {items[0]['CropType']},
                    "Độ ẩm đất (SoilMoisture)": {float(100-items[0]['SoilMoisture']/10)}%,
                    "Nhiệt độ (Temperature)": {items[0]['temperature']}℃,
                    "Độ ẩm không khí (Humidity)": {items[0]['Humidity']}%,
                    "Lượng nước tưới": {items[0]['Water']} ml,
                    """
                    from_email = "kainnoowa2303@gmail.com"
                    recipient_list = ['kainnoowa2303@gmail.com']
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
            cache_status = Cache.objects.get(key="auto")
        except:
            cache_status = Cache.objects.create(key='auto', value=0)
        self.status = int(cache_status.value)
        try:
            cache_status = Cache.objects.get(key='tree')
        except:
            cache_status = Cache.objects.create(key='tree', value=0)
        async_to_sync(self.channel_layer.group_send)(
            self.relay_group_name,
            {
                "type": "message",
                "message": self.status,
            },
        )

    def disconnect(self, close_code):
        cache = Cache.objects.get(key='auto')
        cache.value = str(0)
        cache.save()
        async_to_sync(self.channel_layer.group_discard)(
            self.relay_group_name,
            self.channel_name
        )

    def receive(self, text_data=None, bytes_data=None):
        try:
            if int(text_data[0]) == 0:
                self.status = int(text_data[0])
                cache = Cache.objects.get(key='auto')
                cache.value = str(self.status)
                cache.save()
                client.publish(
                    topic='ESP32_AWSDB/sub',
                    qos=1,
                    payload=json.dumps({"message": str(0)})
                )
                sleep(1)
                client.publish(
                    topic='ESP32_AWSDB/sub',
                    qos=1,
                    payload=json.dumps({"message": 'Unknown'})
                )
            else:
                self.status = int(text_data[0])
                cache = Cache.objects.get(key='auto')
                cache.value = str(self.status)
                cache.save()
                cache = Cache.objects.get(key='tree')
                cache.value = text_data[2]
                cache.save()

                client.publish(
                    topic='ESP32_AWSDB/sub',
                    qos=1,
                    payload=json.dumps({"message": str(1)})
                )
                sleep(1)
                client.publish(
                    topic='ESP32_AWSDB/sub',
                    qos=1,
                    payload=json.dumps({"message": crop[int(text_data[2])]})
                )

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
