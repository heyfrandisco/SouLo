from ultralytics import YOLO
import requests
import pygame
import json

key = json.loads(open("config.json").read()).get("API_KEY")
BASE_URL = 'https://freesound.org/apiv2'

def main():
    model = YOLO("yolo11n.pt")
    
    conf = 0.85
    
    res = model("images/dtm.png", conf=conf, save=True)
    
    labels = list()
    
    for r in res:
        # r.show()
        for box in r.boxes:
            label = model.names[int(box.cls)]
            labels.append(label)
            confidence = box.conf

    print(labels)

if __name__ == '__main__':
    main()