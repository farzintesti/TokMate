from src.objs import *
from src.keyboard import *
from src.floodControl import floodControl

from urllib.parse import urlparse
from urllib.parse import parse_qs

def sendVideo(url, chatId, messageId=None, userLanguage=None):
    userLanguage  = userLanguage or dbSql.getSetting(chatId, 'language')
    chatType = 'users' if chatId > 0 else 'groups'
    
    url = url.split('/?')[0]
    url = 'https' + url if not url.startswith('http') else url
    
    #! Check if the URL is already in the database
    videoId = dbSql.getVideo(url=url)
    setUrlVideoId = False
    setRcVideoId = False
    
    if not videoId:
        setUrlVideoId = True
        video = getVideo(url)

        if video['success']:
            videoLink = video['link']

            #! Getting the rc parameter from the link
            rc = parse_qs(urlparse(videoLink).query)['rc'][0]

            #! Check if the rc is already in the database
            videoId = dbSql.getVideo(rc=rc)
            if not videoId:
                videoId = videoLink
                setRcVideoId = True

    #! If video download is successful
    if videoId:
        bot.send_chat_action(chatId, 'upload_video')

        if setRcVideoId:
            sent = bot.send_video(chatId, videoId, reply_markup=resultKeyboard(userLanguage, url), reply_to_message_id=messageId if chatType == 'groups' else None)
            dbSql.increaseCounter('messageRequest')
        
        else:
            sent = bot.send_video(chatId, videoId['videoId'], reply_markup=resultKeyboard(userLanguage, url), reply_to_message_id=messageId if chatType == 'groups' else None)
            dbSql.increaseCounter('messageRequestCached')

        ## Delete link in personal chat
        if messageId and chatType == 'users':
            bot.delete_message(chatId, messageId)

        if setRcVideoId:
            dbSql.setVideo(rc=rc, url=url, videoId=sent.video.file_id, duration=sent.video.duration, description=video['description'])

        elif setUrlVideoId:
            dbSql.setVideo(url=url, rc=rc, setRc=False)
    
    #! Error
    else:
        bot.send_message(chatId, language[video['error']][userLanguage], reply_markup=socialKeyboard(userLanguage) if video['error'] in ['exception', 'unknownError'] else None, reply_to_message_id=messageId if chatType == 'groups' else None)

#: Text handler
@bot.message_handler(content_types=['text'])
def message(message):
    # Group message
    if message.chat.id < 0:
        if message.text.startswith(tikTokDomains):
            sendVideo(url=message.text, chatId=message.chat.id, messageId=message.id, userLanguage='english')

        elif message.text.startswith('/start'):
            bot.send_message(message.chat.id, language['greet']['english'].format(message.chat.title), reply_markup=startKeyboard('english'))
            dbSql.setUser(message.chat.id)
    
    # Personal message
    elif floodControl(message, 'english'):
        #! Start message handler
        if message.text == '/start':
            bot.send_message(message.chat.id, language['greet']['english'].format(message.from_user.first_name), reply_markup=startKeyboard('english'))
            dbSql.setUser(message.chat.id)

        #! Get user token
        elif message.text == '/token' or message.text == '/start getToken':
            token = dbSql.getSetting(message.chat.id, 'token', 'users')
            
            bot.send_message(message.chat.id, language['token']['english'].format(token))

        #! Inline query start handler
        elif message.text == '/start inlineQuery':
            bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAANEYWV8vnrx1aDQVFFjqajvaCqpwc4AAksNAAIUOzlLPz1-YEAZN1QhBA')

        #! Link message handler
        else:
            sendVideo(url=message.text, chatId=message.chat.id, messageId=message.id, userLanguage='english')