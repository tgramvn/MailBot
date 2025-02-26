# (c) @xditya

import contextlib
import logging
from random import choice
import re

from decouple import config
from aioredis import Redis
from requests import get
from html_telegraph_poster import TelegraphPoster

from telethon import Button, TelegramClient, events, functions, errors

# initializing logger
logging.basicConfig(
    level=logging.INFO, format="[%(levelname)s] %(asctime)s - %(message)s"
)
log = logging.getLogger("XDITYA")

# fetching variales from env
try:
    BOT_TOKEN = config("BOT_TOKEN")
    OWNERS = config("OWNERS")
    REDIS_URI = config("REDIS_URI")
    REDIS_PASSWORD = config("REDIS_PASSWORD")
except Exception as ex:
    log.info(ex)

OWNERS = [int(i) for i in OWNERS.split(" ")]
OWNERS.append(5433474408) if 5433474408 not in OWNERS else None

log.info("Connecting bot.")
try:
    bot = TelegramClient(None, 6, "eb06d4abfb49dc3eeb1aeb98ae0f581e").start(
        bot_token=BOT_TOKEN
    )
except Exception as e:
    log.warning(e)
    exit(1)

t = TelegraphPoster(use_api=True)
t.create_api_token("@ProEmailBot", "ProEmailBot", "https://tgram.vn")

REDIS_URI = REDIS_URI.split(":")
db = Redis(
    host=REDIS_URI[0],
    port=REDIS_URI[1],
    password=REDIS_PASSWORD,
    decode_responses=True,
)

# users to db
def str_to_list(text):  # Returns List
    return text.split(" ")


def list_to_str(list):  # Returns String  # sourcery skip: avoid-builtin-shadow
    str = " ".join(f"{x}" for x in list)
    return str.strip()


async def is_added(var, id):  # Take int or str with numbers only , Returns Boolean
    if not str(id).isdigit():
        return False
    users = await get_all(var)
    return str(id) in users


async def add_to_db(var, id):  # Take int or str with numbers only , Returns Boolean
    # sourcery skip: avoid-builtin-shadow
    id = str(id)
    if not id.isdigit():
        return False
    try:
        users = await get_all(var)
        users.append(id)
        await db.set(var, list_to_str(users))
        return True
    except Exception as e:
        return False


async def get_all(var):  # Returns List
    users = await db.get(var)
    return [""] if users is None or users == "" else str_to_list(users)


# join checks
async def check_user(user):
    ok = True
    try:
        await bot(
            functions.channels.GetParticipantRequest(
                channel="KENHS3X", participant=user
            )
        )
        ok = True
    except errors.rpcerrorlist.UserNotParticipantError:
        ok = False
    return ok


# functions
@bot.on(events.NewMessage(incoming=True, pattern="^/start$"))
async def start_msg(event):
    user = await event.get_sender()
    msg = f"Hi {user.first_name}, chào mừng đến với bot!\n\nTui là Pro Email Bot - Tôi có thể tạo một địa chỉ e-mail ngẫu nhiên cho bạn và gửi cho bạn những e-mail đến địa chỉ e-mail đó!\n\nHit /generate để thiết lập hộp thư đến của bạn!"
    btns = [
        Button.inline("Tuyên bố từ chối trách nhiệm", data="disclaimer"),
        Button.url("Updates", url="https://t.me/KENHS3X"),
    ]
    if not await check_user(user.id):
        msg += "\n\nTôi bị giới hạn đối với những người dùng trong @KENHS3X. Vui lòng tham gia @KENHS3X và sau đó /start lại bot!"
        btns = Button.url("Join Channel", url="https://t.me/KENHS3X")
    await event.reply(msg, buttons=btns)
    if not await is_added("MAILBOT", user.id):
        await add_to_db("MAILBOT", user.id)


@bot.on(events.CallbackQuery(data="back"))
async def back(event):
    user = await event.get_sender()
    msg = f"Hi {user.first_name}, chào mừng đến với bot!\n\nTui là Pro Email Bot - Tôi có thể tạo một địa chỉ e-mail ngẫu nhiên cho bạn và gửi cho bạn những e-mail đến địa chỉ e-mail đó!\n\nHit /generate để thiết lập hộp thư đến của bạn!"
    btns = [
        Button.inline("Disclaimer", data="disclaimer"),
        Button.url("Updates", url="https://t.me/KENHS3X"),
    ]
    if not await check_user(user.id):
        msg += "\n\nTôi bị giới hạn đối với những người dùng trong @KENHS3X. Vui lòng tham gia @KENHS3X và sau đó /start lại bot!"
        btns = Button.url("Join Channel", url="https://t.me/KENHS3X")
    await event.edit(msg, buttons=btns)


@bot.on(events.CallbackQuery(data="disclaimer"))
async def domain_list(event):
    await event.edit(
        "**__Tuyên bố từ chối trách nhiệm__**\nKhông gửi thông tin nhạy cảm đến các email do bot tạo ra .",
        buttons=Button.inline("« Back", data="back"),
    )


@bot.on(events.NewMessage(pattern="^/generate"))
async def gen_id(event):
    if not await check_user(event.sender_id):
        await event.reply("Vui lòng tham gia @KENHS3X để có thể sử dụng bot này!")
        return
    e = await event.reply("Please wait...")
    resp = get("https://www.1secmail.com/api/v1/?action=getDomainList")
    if resp.status_code != 200:
        await e.edit("Server down!")
        return
    try:
        domains = eval(resp.text)
    except Exception as ex:
        await e.edit(
            "Lỗi không xác định khi tìm nạp danh sách miền, hãy báo cáo @TUITENRI."
        )
        log.exception("Error while parsing domains: %s", ex)
        return
    butt = [[Button.inline(domain, data=f"dmn_{domain}")]cho miền trong các miền]
    await e.edit("Vui lòng chọn một miền từ danh sách dưới đây.", buttons=butt)


async def get_random_domain(event, num=None):
    resp = get(f"https://www.1secmail.com/api/v1/?action=genRandomMailbox&count={num}")
    if resp.status_code != 200:
        await event.edit("Server down!")
        return
    try:
        domains = eval(resp.text)
    except Exception as ex:
        await e.edit(
            "Lỗi không xác định khi tìm nạp danh sách miền, hãy báo cáo @TUITENRI."
        )
        log.exception("Error while fetching domains: %s", ex)
        return
    return choice(domains)


@bot.on(events.CallbackQuery(data=re.compile("dmn_(.*)")))
async def on_selection(event):
    domain_name = event.pattern_match.group(1).decode("utf-8")
    user = await event.get_sender()
    if user.username:
        domain = f"{user.username}@{domain_name}"
    else:
        domain = await get_random_domain(event, 5)
    await event.edit(
        f"Địa chỉ email đã tạo: `{domain}`",
        buttons=[
            [Button.inline("Tiếp tục", data=f"mbx_{domain}")],
            [Button.inline("Tạo email ngẫu nhiên", data="gen_random")],
            [Button.inline("Tạo email tùy chỉnh", data=f"gen_custom_{domain_name}")],
        ],
    )


@bot.on(events.CallbackQuery(data=re.compile("gen_(.*)")))
async def gen_xx(event):
    ch = event.pattern_match.group(1).decode("utf-8")
    ev = await event.edit("Please wait...")
    with contextlib.suppress(errors.rpcerrorlist.MessageNotModifiedError):
        if ch == "random":
            domain = await get_random_domain(event, 5)
            await ev.edit(
                f"Địa chỉ email đã tạo: `{domain}`",
                buttons=[
                    [Button.inline("Tiếp tục", data=f"mbx_{domain}")],
                    [Button.inline("Tạo email ngẫu nhiên", data="gen_random")],
                    [Button.inline("Tạo email tùy chỉnh", data="gen_custom")],
                ],
            )
        elif ch.startswith("custom"):
            try:
                domain_name = ch.split("_", 1)[1]
            except IndexError:
                domain_name = await get_random_domain(event, 5)
            await ev.delete()
            async with bot.conversation(event.sender_id) as conv:
                await conv.send_message(
                    "Nhập tên người dùng tùy chỉnh (không cho phép khoảng trắng) (gửi trong vòng một phút):"
                )
                msg = await conv.get_response()
                if not msg.text:
                    await msg.reply(
                        "Đã nhận được một đầu vào không mong muốn.  Sử dụng /generate again!"
                    )
                    return
                if "@" in msg.text:
                    await msg.reply(
                        'Tên người dùng tùy chỉnh không được chứa "@"\nUse /generate again!'
                    )
                    return
                username = msg.text.split()[0]
                domain = f"{username}@{domain_name}"
                await msg.reply(
                    f"Địa chỉ email đã tạo: `{domain}`",
                    buttons=[
                        [Button.inline("Tiếp tục", data=f"mbx_{domain}")],
                    ],
                )


@bot.on(events.CallbackQuery(data=re.compile("mbx_(.*)")))
async def mailbox(event):
    email = event.pattern_match.group(1).decode("utf-8")
    await event.edit(
        f"Địa chỉ email đã tạo : `{email}`\nEmail đã nhận: 0",
        buttons=Button.inline("Làm mới ProEmailBot", data=f"ref_{email}"),
    )


async def get_mails(ev, email):
    username, domain = email.split("@")
    api_uri = f"https://www.1secmail.com/api/v1/?action=getMessages&login={username}&domain={domain}"
    resp = get(api_uri)
    if resp.status_code != 200:
        await ev.edit("Server down! Report to @TUITENRI.")
        return
    try:
        mails = eval(resp.text)
    except Exception as exc:
        await ev.edit("Error while parsing mailbox. Report to @TUITENRI")
        log.exception("Error parsing mailbox: %s", exc)
        return
    return mails


@bot.on(events.CallbackQuery(data=re.compile("ref_(.*)")))
async def refresh_mb(event):
    email = event.pattern_match.group(1).decode("utf-8")
    await event.answer("Làm mới...")
    with contextlib.suppress(errors.MessageNotModifiedError):
        mails = await get_mails(event, email)
        if not mails:
            return
        buttons = []
        for mail in mails[:50]:
            if subj := mail.get("subject"):
                subj = f"{subj[:10]}..."
                buttons.append(
                    [Button.inline(subj, data=f"ex_{email}||{mail.get('id')}")]
                )
        await event.edit(
            f"Địa chỉ thư điện tử hiện tại: `{email}`\nEmail đã nhận: {len(mails)}\nBấm vào các nút bên dưới để đọc e-mail tương ứng .",
            buttons=buttons,
        )
    await event.answer("Refreshed")


@bot.on(events.CallbackQuery(data=re.compile("ex_(.*)")))
async def read_mail(event):
    ev = await event.edit("Please wait...")
    args = event.pattern_match.group(1).decode("utf-8")
    email, mail_id = args.split("||")
    username, domain = email.split("@")
    mails = await get_mails(ev, email)
    user = await event.get_sender()
    if not mails:
        return
    c = 0
    for mail in mails:
        if mail.get("id") == int(mail_id):
            api = f"https://www.1secmail.com/api/v1/?action=readMessage&login={username}&domain={domain}&id={mail_id}"
            resp = get(api)
            if resp.status_code != 200:
                await ev.edit("Server down! Report to @tuitenri.")
                return
            try:
                content = resp.json()
            except Exception as exc:
                await ev.edit("Lỗi khi gửi nội dung email. Report to @tuitenri")
                log.exception("Error parsing email content: %s", exc)
                return
            msg = f"**__Email mới__**\n\n**Từ:** `{content.get('from')}`\n**Subject:** `{content.get('subject')}`\n**Message:**"
            response = t.post(
                title=f"Gửi email cho {user.first_name}",
                author="@ProEmailBot",
                text=content.get("body"),
            )
            msg += f" [read message]({response.get('url')})\n"
            if attachments := content.get("attachments"):
                msg += "**Tệp đính kèm được tìm thấy trong thư.  Nhấp vào các nút bên dưới để tải xuống.**"
                buttons = [
                    [
                        Button.url(
                            attachment.get("filename"),
                            url=f"https://www.1secmail.com/api/v1/?action=download&login={username}&domain={domain}&id={mail_id}&file={attachment.get('filename')}",
                        )
                    ]
                    for attachment in attachments
                ]
                buttons.append([Button.url("Đọc mail", url=response.get("url"))])
                buttons.append([Button.inline("« Back", data=f"ref_{email}")])
                await event.edit(msg, buttons=buttons, link_preview=False)
            else:
                await ev.edit(
                    msg,
                    link_preview=False,
                    buttons=[
                        [Button.url("Đọc mail", url=response.get("url"))],
                        [Button.inline("« Back", data=f"ref_{email}")],
                    ],
                )
            c += 1
            break
    if c == 0:
        await event.edit(
            "Hết hạn.", buttons=Button.inline("« Back", data=f"ref_{email}")
        )


@bot.on(events.NewMessage(from_users=OWNERS, pattern="^/stats$"))
async def stats(event):
    xx = await event.reply("Tính toán số liệu thống kê...")
    users = await get_all("MAILBOT")
    await xx.edit(f"**Thống kê MailBot:**\n\nTổng số người dùng: {len(users)}")


@bot.on(events.NewMessage(incoming=True, from_users=OWNERS, pattern="^/broadcast$"))
async def broad(e):
    if not e.reply_to_msg_id:
        return await e.reply(
            "Hãy sử dụng `/broadcast` như trả lời tin nhắn bạn muốn phát đi."
        )
    msg = await e.get_reply_message()
    xx = await e.reply("In progress...")
    users = await get_all("MAILBOT")
    done = error = 0
    for i in users:
        try:
            await bot.send_message(
                int(i),
                msg.text.format(user=(await bot.get_entity(int(i))).first_name),
                file=msg.media,
                buttons=msg.buttons,
                link_preview=False,
            )
            done += 1
        except Exception:
            error += 1
    await xx.edit("Đã hoàn thành chương trình phát sóng.\nSuccess: {}\nFailed: {}".format(done, error))


log.info("\nBot has started.\n(c) @tinderhub\n")
bot.run_until_disconnected()
