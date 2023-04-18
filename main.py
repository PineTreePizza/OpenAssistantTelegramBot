import requests
import datetime
import math
import os
from telebot.async_telebot import AsyncTeleBot
import asyncio
from deep_translator import GoogleTranslator
from googletrans import Translator

API_URL = "https://api-inference.huggingface.co/models/OpenAssistant/oasst-sft-1-pythia-12b"

headers = {"Authorization": f'Bearer {os.getenv("HF_TOKEN")}'}

def query(payload):
	response = requests.post(API_URL, headers=headers, json=payload)
	return response.json()

seed = int(str(datetime.datetime.now().timestamp()*math.pi).replace('.',''))
bot = AsyncTeleBot(os.getenv("TG_KEY"))

answerlanguage = 'en'
inputlanguage = 'auto'
shownontrans = False
allowed_languages=['en','ru']

def Translate(text, destl=answerlanguage, srcl=inputlanguage,userlang=None):
        tries = 0
        while tries < 20:
                try:
                        if(text == "\n"):
                                text = None
                                return text,'en','en'
                        if(inputlanguage == 'auto'):
                                lang=Translator().detect(text).lang
                                print("language: " + lang)
                                #if(lang not in allowed_languages and lang != 'en'):
                                 #       if(userlang != None):
                                  #              lang = userlang
                                   #     else:
                                    #            lang = 'en'
                        else:
                                lang = inputlanguage
                        translator = GoogleTranslator(source=srcl, target=destl)
                        translatedtext = translator.translate(text)
                        print(translatedtext)
                        return translatedtext, lang, translator.target
                except Exception as e:
                        print("translate error:",e)
                        tries+=1
        return None, 'en', 'en'

def get_replied_message(message):
        if(message.reply_to_message != None):
                return message.reply_to_message
        else:
                return None

def replier(msg):
    print(msg.text)
    inputs=""
    if(get_replied_message(msg)!=None):
        if(msg.reply_to_message.from_user.is_bot == True):
                inputs="<|assistant|>"+Translate(get_replied_message(msg).text,userlang=msg.from_user.language_code)[0]+"<|endoftext|>\n"
        else:
                inputs="<|prompter|>"+Translate(get_replied_message(msg).text,userlang=msg.from_user.language_code)[0]+"<|endoftext|>\n"
                
    msg,src,dest = Translate(msg.text)
    print(msg)
    inputs += "<|prompter|>"+msg+"<|endoftext|>\n<|assistant|>"
    output = query({
        "inputs": inputs,
        "parameters":{
            "temperature":0.7,
            "vocab_size":1003520,
            "max_new_tokens":1024,
            "num_beams":4,
            "penalty_alpha":None,
            "repetition_penalty":1.4,
            "max_time":None,
            "top_k":150,
            "top_p":0.8,
            "return_full_text":False,
            "do_sample":True,
            "slow_but_exact":True,
            "seed":seed,
        },
        "options": {
            "wait_for_model":True,
        },
    })
    print(output, dest, src)
    outputrans = Translate("\n"+output[0]['generated_text'],src,dest)
    print(outputrans)
    return(output[0]['generated_text'],outputrans[0],dest,src)
 
@bot.message_handler(func=lambda message: not message.text.startswith('/'))
async def chatbot(message):
        await bot.send_chat_action(message.chat.id, 'typing')
        answer,answertrans,src,dest = replier(message)
        mesage=""
        if len(answer) > 4095:
                for x in range(0, len(answer), 4095):
                         mesage = await bot.reply_to(message,answer[x:x+4095],parse_mode="Markdown")
        else:
                 mesage = await bot.reply_to(message, answer,parse_mode="Markdown")
        
        if src != dest:
                answertrans=answertrans
                if len(answertrans) > 4095:
                        for x in range(0, len(answertrans), 4095):
                                await bot.reply_to(mesage,answertrans[x:x+4095],parse_mode="Markdown")
                else:
                        await bot.reply_to(mesage, answertrans,parse_mode="Markdown")
        
@bot.message_handler(commands=['start'])
async def startchat(message):
        print("start command")
        await bot.reply_to(message,"`welcome`",parse_mode="Markdown")
        
asyncio.run(bot.polling())

