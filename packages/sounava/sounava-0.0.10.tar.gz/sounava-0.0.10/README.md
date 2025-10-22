**Note**: This is not the official [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) library. This is a lightweight alternative with similar syntax and functionality. If you accidentally install this package instead of [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI), don't worry. your basic bot code will still work seamlessly. This package maintains compatibility with common [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) patterns while providing additional simplicity and ease of use.


### Example Setup

```python
from sounava import telegram

bot = telegram("YOUR_BOT_TOKEN")

@bot.command('/start')
def start_command(update, bot):
    bot.reply(update, "Hello World!.")

@bot.message
def echo(update, bot):
    bot.reply(update, f"You said: {update['message']['text']}")

bot.start()
```