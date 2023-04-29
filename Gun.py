# импортируем необходимые библиотеки
import numpy as np
import cv2
import imutils
import telegram
import datetime
import os
import asyncio

# инициализируем Telegram-бота и chat_id для отправки сообщений
bot = telegram.Bot(token='TOKEN')
chat_id = 'CHAT_ID'

# загружаем каскадный классификатор для обнаружения оружия на изображении
gun_cascade = cv2.CascadeClassifier('cascade.xml')

# инициализируем камеру
camera = cv2.VideoCapture(0)

# переменные для отслеживания состояния программы
firstFrame = None   
gun_exist = False
alarm_active = False
frames_since_detection = 0

# функция для отправки сообщения в Telegram
async def send_warning(chat_id):
    try:
        await bot.send_message(chat_id=chat_id, text='Осторожно! Обнаружено оружие!')
    except telegram.error.TelegramError as e:
        print("Ошибка отправки сообщения: ", e)

# основная функция программы
async def main():
    global firstFrame, gun_exist, alarm_active, frames_since_detection
    
    while True:
        # читаем кадр с камеры
        ret, frame = camera.read()

        # изменяем размер кадра и переводим его в оттенки серого
        frame = imutils.resize(frame, width=500)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # обнаруживаем оружие на изображении с помощью каскадного классификатора
        gun = gun_cascade.detectMultiScale(gray, 1.3, 5, minSize=(100, 100))

        # если оружие обнаружено, устанавливаем флаг gun_exist в True
        if len(gun) > 0:
            gun_exist = True
        else:
            gun_exist = False

        # отображаем прямоугольник вокруг обнаруженного оружия на изображении
        for (x, y, w, h) in gun:
            frame = cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            roi_gray = gray[y:y + h, x:x + w]
            roi_color = frame[y:y + h, x:x + w]

        # добавляем дату и время кадра на изображение
        cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S %p"), (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

        # отображаем кадр на экране
        cv2.imshow("Security Feed", frame)

        # ждем нажатия клавиши
        key = cv2.waitKey(1) & 0xFF

        # если нажата клавиша 'q', выходим из программы
        if key == ord('q'):
            break

        # если обнаружено оружие, начинаем отслеживать количество кадров с оружием
        if gun_exist:
            print("guns detected")
            frames_since_detection += 1
            # если сигнал тревоги еще не активен, активируем его
            if not alarm_active:
                alarm_active = True
            # если количество кадров с оружием превышает 5, отправляем сообщение в Telegram
            if frames_since_detection > 5:
                screenshot = "screenshot.jpg"
                cv2.imwrite(screenshot, frame)
                await send_warning(chat_id)
                os.remove(screenshot)
                frames_since_detection = 0
        else:
            # если оружие не обнаружено, сбрасываем количество кадров с оружием и деактивируем сигнал тревоги
            print("guns NOT detected")
            frames_since_detection = 0
            if alarm_active:
                alarm_active = False

        # если нажата клавиша 's', отключаем сигнал тревоги
        if key == ord('s'):
            if alarm_active:
                alarm_active = False

    # освобождаем ресурсы и закрываем окна
    camera.release()
    cv2.destroyAllWindows()

# запускаем основную функцию программы
asyncio.run(main())