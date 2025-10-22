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
    p("Name:", get("name")),
    p("Age:", get("age")),
    
    if_(
        gt(get("age"), 18),
        p(get("name"), "is an adult"),
        else_=p(get("name"), "is a minor")
    )
)

program.run()
```

**Output:**
```sh
Name: Alice
Age: 25
Alice is an adult
```

## Core Components

**Basic Structure**:<br>
· `src(*nodes)` - Main program container<br>
· `var(name, value)` - Variable declaration<br>
· `p(*values)` - Print statement<br>
· `get(name)` - Variable reference<br>

**Control Flow**:<br>
· `if_(condition, then_branch, else_branch)` - If statement<br>
· `for_(item, iterable, body)` - For loop<br>
· `while_(condition, body)` - While loop<br>

**Functions**:<br>
· `function(name, params, *body)` - Function definition<br>
· `call(name, args)` - Function call<br>
· `return_(value)` - Return statement<br>

**Data Structures**:<br>
· `list_(*items)` - List literal<br>
· `dict_(**items)` - Dictionary literal<br>

**Operations**:<br>
· `add(a, b)`, `subtract(a, b)`, `multiply(a, b)`, `divide(a, b)`<br>
· `eq(a, b)`, `neq(a, b)`, `gt(a, b)`, `lt(a, b)`<br>
· `and_(a, b)`, `or_(a, b)`, `not_(a)`<br>

## Advanced Examples

**Function with Loop**
```python
from starexx import *

program = src(
    function(
        "calculate_sum",
        ["numbers"],
        var("total", 0),
        for_("num", get("numbers"), src(
            set_("total", add(get("total"), get("num")))
        )),
        return_(get("total"))
    ),
    
    var("scores", list_(85, 92, 78, 96)),
    var("total_score", call("calculate_sum", [get("scores")])),
    p("Scores:", get("scores")),
    p("Total:", get("total_score"))
)

program.run()
```

**List Operations**
```python
from starexx import *

program = src(
    var("fruits", list_("apple", "banana", "orange")),
    p("Fruits:", get("fruits")),
    p("First fruit:", call("fruits.__getitem__", [0])),
    
    # Add a new fruit
    call("fruits.append", ["grape"]),
    p("Updated fruits:", get("fruits")),
    
    # List length
    p("Number of fruits:", len_(get("fruits")))
)

program.run()
```