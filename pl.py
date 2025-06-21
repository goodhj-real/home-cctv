import nest_asyncio
nest_asyncio.apply()

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import cv2
import os
from datetime import datetime
from gpiozero import DistanceSensor
import asyncio
import logging

# 로그 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 텔레그램 봇 토큰
BOT_TOKEN ="7649039695:AAHp5plX7aF-G6OpCoIsKhnDZycfEd0sd2M"

# 초음파 센서 설정
sensor = DistanceSensor(echo=24, trigger=23)
SENSOR_THRESHOLD = 0.2  # 20cm 이내로 감지되면 촬영

# chat_id 저장용
chat_id = None

# 사진 찍는 함수
def take_picture():
    filename = f"/tmp/photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if ret:
        cv2.imwrite(filename, frame)
        return filename
    return None

# /start 명령어 처리
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global chat_id
    chat_id = update.effective_chat.id
    await update.message.reply_text("텔레그램 카메라 시스템이 준비되었습니다. /capture 입력 시 사진을 촬영합니다.")
    logger.info(f"채팅 ID 저장됨: {chat_id}")

# /capture 명령어 처리
async def capture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    filename = take_picture()
    if filename:
        await update.message.reply_photo(photo=open(filename, 'rb'))
        os.remove(filename)
        logger.info("수동 사진 촬영 완료")
    else:
        await update.message.reply_text("사진 촬영에 실패했습니다.")

# 초음파 감지 루프
async def monitor_sensor(app):
    global chat_id
    bot = app.bot
    logger.info("초음파 감지 루프 시작됨")

    while True:
        try:
            if sensor.distance < SENSOR_THRESHOLD and chat_id:
                logger.info("움직임 감지됨. 자동 사진 촬영 시도")
                filename = take_picture()
                if filename:
                    await bot.send_message(chat_id=chat_id, text="움직임이 감지되어 사진을 전송합니다.")
                    await bot.send_photo(chat_id=chat_id, photo=open(filename, 'rb'))
                    os.remove(filename)
                await asyncio.sleep(5)
            await asyncio.sleep(0.3)
        except Exception as e:
            logger.error(f"감지 루프 에러: {e}")
            await asyncio.sleep(1)

# 메인 실행 함수
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("capture", capture))

    asyncio.create_task(monitor_sensor(app))

    logger.info("텔레그램 봇이 시작되었습니다. /start 명령어를 입력해 주세요.")
    await app.run_polling()

# 메인 시작점
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())  
