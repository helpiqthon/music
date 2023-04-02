import asyncio
import logging
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import User
from iqthon import Config, iqmusic
from iqthon.core.managers import edit_delete, edit_or_reply
from .helper.stream_helper import Stream
from .helper.tg_downloader import tg_dl
from .helper.vcp_helper import iqthonvc
plugin_category = "extra"
logging.getLogger("pytgcalls").setLevel(logging.ERROR)

OWNER_ID = iqmusic.uid

vc_session = Config.VC_SESSION

if vc_session:
    vc_client = TelegramClient(        StringSession(vc_session), Config.APP_ID, Config.API_HASH    )
else:
    vc_client = iqmusic

vc_client.__class__.__module__ = "telethon.client.telegramclient"
vc_player = iqthonvc(vc_client)

asyncio.create_task(vc_player.start())


@vc_player.app.on_stream_end()
async def handler(_, update):
    await vc_player.handle_next(update)


ALLOWED_USERS = set()


@iqmusic.ar_cmd(    pattern="انضمام ?(\S+)? ?(?:-as)? ?(\S+)?")
async def joinVoicechat(event):
    "To join a Voice Chat."
    chat = event.pattern_match.group(1)
    joinas = event.pattern_match.group(2)

    await edit_or_reply(event, "**جار الانضمام للمكالمة الصوتية**")

    if chat and chat != "-as":
        if chat.strip("-").isnumeric():
            chat = int(chat)
    else:
        chat = event.chat_id

    if vc_player.app.active_calls:
        return await edit_delete(
            event, f"لقد انضممت بالفعل الى {vc_player.CHAT_NAME}"
        )

    try:
        vc_chat = await iqmusic.get_entity(chat)
    except Exception as e:
        return await edit_delete(event, f'ERROR : \n{e or "UNKNOWN CHAT"}')

    if isinstance(vc_chat, User):
        return await edit_delete(
            event, "لايمكنك استعمال اوامر الميوزك على الخاص فقط في المجموعات !"
        )

    if joinas and not vc_chat.username:
        await edit_or_reply(
            event, "**انت وين لكيت هل كلاوات حبيبي مو كتلك ميصير بلاتصال الخاص**"
        )
        joinas = False

    out = await vc_player.join_vc(vc_chat, joinas)
    await edit_delete(event, out)


@iqmusic.ar_cmd(
    pattern="مغادرة"
    
)
async def leaveVoicechat(event):
    "To leave a Voice Chat."
    if vc_player.CHAT_ID:
        await edit_or_reply(event, "** تم مغادرة من الاتصال **")
        chat_name = vc_player.CHAT_NAME
        await vc_player.leave_vc()
        await edit_delete(event, f"تمت المغادرة من {chat_name}")
    else:
        await edit_delete(event, "** لست منضم على الاتصال**")


@iqmusic.ar_cmd(
    pattern="قائمة_التشغيل"
    
)
async def get_playlist(event):
    "To Get all playlist for Voice Chat."
    await edit_or_reply(event, "**جارِ جلب قائمة التشغيل ......**")
    playl = vc_player.PLAYLIST
    if not playl:
        await edit_delete(event, "Playlist empty", time=10)
    else:
        jep = ""
        for num, item in enumerate(playl, 1):
            if item["stream"] == Stream.audio:
                jep += f"{num}. 🔉  `{item['title']}`\n"
            else:
                jep += f"{num}. 📺  `{item['title']}`\n"
        await edit_delete(event, f"**قائمة التشغيل:**\n\n{jep}\n**جيبثون يتمنى لكم وقتاً ممتعاً**")


@iqmusic.ar_cmd(
    pattern="تشغيل ?(-f)? ?([\S ]*)?"
    
)
async def play_audio(event):
    "To Play a media as audio on VC."
    flag = event.pattern_match.group(1)
    input_str = event.pattern_match.group(2)
    if input_str == "" and event.reply_to_msg_id:
        input_str = await tg_dl(event)
    if not input_str:
        return await edit_delete(
            event, "**قم بالرد على ملف صوتي او رابط يوتيوب**", time=20
        )
    if not vc_player.CHAT_ID:
        return await edit_or_reply(event, "**`قم بلانضمام للمكالمة اولاً بأستخدام أمر `انضمام")
    if not input_str:
        return await edit_or_reply(event, "No Input to play in vc")
    await edit_or_reply(event, "**يتم الان تشغيل الاغنية في الاتصال **")
    if flag:
        resp = await vc_player.play_song(input_str, Stream.audio, force=True)
    else:
        resp = await vc_player.play_song(input_str, Stream.audio, force=False)
    if resp:
        await edit_delete(event, resp, time=30)


@iqmusic.ar_cmd(
    pattern="ايقاف_مؤقت"
    
)
async def pause_stream(event):
    "To Pause a stream on Voice Chat."
    await edit_or_reply(event, "**تم ايقاف الموسيقى مؤقتاً ⏸**")
    res = await vc_player.pause()
    await edit_delete(event, res, time=30)


@iqmusic.ar_cmd(
    pattern="استمرار",
    
)
async def resume_stream(event):
    "To Resume a stream on Voice Chat."
    await edit_or_reply(event, "**تم استمرار الاغنيه استمتع ▶️**")
    res = await vc_player.resume()
    await edit_delete(event, res, time=30)


@iqmusic.ar_cmd(
    pattern="تخطي"
    
)
async def skip_stream(event):
    "To Skip currently playing stream on Voice Chat."
    await edit_or_reply(event, "**تم تخطي الاغنية وتشغيل الاغنيه التالية 🎵**")
    res = await vc_player.skip()
    await edit_delete(event, res, time=30)
