# import joblib
# import pandas as pd


# def outputer(output):
#     if output[0] == 0:
#         new_output = "Not irrigating"
#     elif output[0] == 1:
#         new_output = "Irrigating"
#     return new_output


# model = joblib.load('RFC_model.joblib')
# CropType = 'Wheat'
# CropDays = 24.0
# temperature = 40.0
# soilMoisture = 600.0
# humidity = 30.0
# features = pd.DataFrame({
#     'CropType': [0],
#     'CropDays': [CropDays],
#     'SoilMoisture': [soilMoisture],
#     'temperature': [temperature],
#     'Humidity': [humidity]
# })
# prediction = model.predict(features)
# print(prediction)
# prediction_text = outputer(prediction)
# print(prediction_text)
# Schedule Library imported
import schedule
import time

# Functions setup

pre = 0


def sudo_placement():
    print("Get ready for Sudo Placement at Geeksforgeeks")


def good_luck():
    print("Good Luck for Test")


def work():
    print("Study and work hard")


def bedtime():
    print("It is bed time go rest")


def geeks():
    pre = 1
    print("Shaurya says Geeksforgeeks")


# Task scheduling
# After every 10mins geeks() is called.
schedule.every(1).minutes.do(geeks)

# # After every hour geeks() is called.
# schedule.every().hour.do(geeks)

# # Every day at 12am or 00:00 time bedtime() is called.
# schedule.every().day.at("00:00").do(bedtime)

# # After every 5 to 10mins in between run work()
# schedule.every(5).to(10).minutes.do(work)

# # Every monday good_luck() is called
# schedule.every().monday.do(good_luck)

# # Every tuesday at 18:00 sudo_placement() is called
# schedule.every().tuesday.at("18:00").do(sudo_placement)

# Loop so that the scheduling task
# keeps on running all time.


def mma():
    global pre
    while True:

        # Checks whether a scheduled task
        # is pending to run or not
        schedule.run_pending()
        print(pre)
        time.sleep(1)
        pre = 0


mma()
