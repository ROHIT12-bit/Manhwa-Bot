import pyrogram
from time import time 
from loguru import logger

from pyrogram import idle
import random, os, shutil, asyncio

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import sys 


class Vars:
  API_ID = int(os.environ.get("API_ID", "26047636"))
  API_HASH = os.environ.get("API_HASH", "d8b1ed69ae1f937c5dd4d3cc8c8de440")
  
  BOT_TOKEN = os.environ.get("BOT_TOKEN", "8360002384:AAFnRTI4Wv5mdVBql1G9WimrNaxzFA24Joo")
  plugins = dict(root="TG")
  
  LOG_CHANNEL = os.environ.get("LOG_CHANNEL", "-1003404863533")
  UPDATE_CHANNEL = os.environ.get("UPDATE_CHANNEL", "")
  DB_URL = os.environ.get("DB_URL", "mongodb+srv://rohitreddyathuru:R6Co7MOjTYQOAqcq@cluster0.xrwjpl9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
  
  PORT = int(os.environ.get("PORT", "5000"))
  OWNER = int(os.environ.get("OWNER","8367080346"))
  ADMINS = os.environ.get("ADMINS", "8367080346")
  ADMINS = [int(admin) for admin in (ADMINS).split(" ")]
  ADMINS.append(OWNER)
  
  IS_PRIVATE = os.environ.get("IS_PRIVATE", None) #True Or None  Bot is for admins only
  CONSTANT_DUMP_CHANNEL = os.environ.get("CONSTANT_DUMP_CHANNEL", None)
  WEBS_HOST = os.environ.get("WEBS_HOST", None) # For Render and Koyeb
  
  DB_NAME = "Manhwadb"
  PING = time()
  
  SHORTENER = os.environ.get("SHORTENER", None)
  SHORTENER_API = os.environ.get("SHORTENER_API", "") # put {} for url, ex: shornter.api?url={}
  DURATION = int(os.environ.get("DURATION", "20")) # hrs
  
  FORCE_SUB_TEXT = os.environ.get("FORCE_SUB_TEXT", """<b><i>❗️ You must join our channel before using this feature:</i></b>""")
  
  # Force Sub Channel Format : Button Text: Username(Without @) or Chat ID
  FORCE_SUB_CHANNEL = os.environ.get("FORCE_SUB_CHANNEL", "")#𝕵𝖔𝖎𝖓 𝕮𝖍𝖆𝖓𝖓𝖊𝖑: , 𝕸𝖆𝖎𝖓 𝕮𝖍𝖆𝖓𝖓𝖊𝖑: ")
  
  BYPASS_TXT = os.environ.get("BYPASS_TXT", """<blockquote><b>🚨 ʙʏᴘᴀss ᴅᴇᴛᴇᴄᴛᴇᴅ 🚨</b></blockquote>

<blockquote expandable><b>ʜᴏᴡ ᴍᴀɴʏ ᴛɪᴍᴇs ʜᴀᴠᴇ ɪ ᴛᴏʟᴅ ʏᴏᴜ, ᴅᴏɴ'ᴛ ᴛʀʏ ᴛᴏ ᴏᴜᴛsᴍᴀʀᴛ ʏᴏᴜʀ ᴅᴀᴅ 🥸🖕

ɴᴏᴡ ʙᴇ ᴀ ɢᴏᴏᴅ ʙᴏʏ ᴀɴᴅ sᴏʟᴠᴇ ɪᴛ ᴀɢᴀɪɴ, ᴀɴᴅ ᴛʜɪs ᴛɪᴍᴇ ᴅᴏɴ'ᴛ ɢᴇᴛ sᴍᴀʀᴛ !! 🌚💭</b></blockquote>""")

  PICS = (
    "https://i.rj1.dev/hwFUy.png",
  )




remove_site_sf = ["cf"]

def load_fsb_vars(self):
  channel = Vars.FORCE_SUB_CHANNEL
  try:
    if "," in Vars.FORCE_SUB_CHANNEL:
      for channel_line in channel.split(","):
        self.FSB.append(
          (channel_line.split(":")[0], channel_line.split(":")[1])
        )
    else:
      self.FSB.append((channel.split(":")[0], channel.split(":")[1]))
  except:
    logger.error(" FORCE_SUB_CHANNEL is not set correctly! ")
    sys.exit()


class Manhwa_Bot(pyrogram.Client):
  def __init__(self):
    super().__init__(
      "ManhwaBot",
      api_id=Vars.API_ID,
      api_hash=Vars.API_HASH,
      bot_token=Vars.BOT_TOKEN,
      plugins=Vars.plugins,
      workers=50,
    )
    self.__version__ = pyrogram.__version__
    self.FSB = []
    
  async def start(self):
    await super().start()
    
    async def run_flask():
      cmds = ("gunicorn", "app:app")
      process = await asyncio.create_subprocess_exec(
        *cmds,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
      )
      stdout, stderr = await process.communicate()

      if process.returncode != 0:
        logger.error(f"Flask app failed to start: {stderr.decode()}")
      
      logger.info("Webs app started successfully")
    
    usr_bot_me = await self.get_me()
    
    if os.path.exists("restart_msg.txt"):
      with open("restart_msg.txt", "r") as f:
        chat_id, message_id = f.read().split(":")
        f.close()

      try: await self.edit_message_text(int(chat_id), int(message_id), "<code>Restarted Successfully</code>")
      except Exception as e: logger.exception(e)

      os.remove("restart_msg.txt")
    
    if os.path.exists("Process"):
      shutil.rmtree("Process")
    
    if Vars.FORCE_SUB_CHANNEL:
      load_fsb_vars(self)
    
    logger.info("""
    
    ██╗    ██╗██╗███████╗ █████╗ ██████╗ ██████╗     ██████╗  ██████╗ ████████╗███████╗
    ██║    ██║██║╚══███╔╝██╔══██╗██╔══██╗██╔══██╗    ██╔══██╗██╔═══██╗╚══██╔══╝██╔════╝
    ██║ █╗ ██║██║  ███╔╝ ███████║██████╔╝██║  ██║    ██████╔╝██║   ██║   ██║   ███████╗
    ██║███╗██║██║ ███╔╝  ██╔══██║██╔══██╗██║  ██║    ██╔══██╗██║   ██║   ██║   ╚════██║
    ╚███╔███╔╝██║███████╗██║  ██║██║  ██║██████╔╝    ██████╔╝╚██████╔╝   ██║   ███████║
     ╚══╝╚══╝ ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝     ╚═════╝  ╚═════╝    ╚═╝   ╚══════╝

    """)
    self.username = usr_bot_me.username
    logger.info("Make By https://t.me/Botskingdoms ")
    logger.info(f"Manhwa Bot Started as {usr_bot_me.first_name} | @{usr_bot_me.username}")
    
    if Vars.WEBS_HOST:
      await run_flask()
    
    MSG = f"""<blockquote><b>🔥 SYSTEMS ONLINE. READY TO RUMBLE. 🔥

DC Mode: {usr_bot_me.dc_id}

Sleep mode deactivated. Neural cores at 100%. Feed me tasks, and watch magic happen. Let’s. Get. Dangerous.</b></blockquote>"""
    
    PICS = random.choice(Vars.PICS)
    
    button = [[
      InlineKeyboardButton('*Start Now*', url= f"https://t.me/{self.username}?start=start"),
      InlineKeyboardButton("*Channel*", url = "telegram.me/Botskingdoms")
    ]]
    
    try: await self.send_photo(-1002822095762, photo=PICS, caption=MSG, reply_markup=InlineKeyboardMarkup(button))
    except: pass

    
  async def stop(self):
    await super().stop()
    logger.info("Manhwa Bot Stopped")


Bot = Manhwa_Bot()
    
