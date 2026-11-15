# chat

A small command-line chat tool for talking to the personal-assistance agents. It only uses the Python standard library.

```bash
python -m chat              # pick an agent from a menu
python -m chat -a echo      # connect to an agent directly
python -m chat --list       # list agents
```

Run it from the project root.

## Using it

- **Typing**: you get line editing and history (↑/↓). End a line with `\` to keep typing on the next line.
- **Menus**: move with ↑/↓ (or `j`/`k`, or a number key), press Enter to pick, Esc to cancel.
- **Commands**: `/agent [name]`, `/help`, `/clear`, `/exit`. Type `/` by itself to get a command menu.
- Ctrl-C cancels the current line or a running request. Ctrl-D quits.

## Agents

| name     | what it does                                                        | needs                           |
|----------|---------------------------------------------------------------------|---------------------------------|
| `notes`  | Classifies, summarises and stores a note (`NoteProcessingWorkflow`) | `requirements.txt`, GPU, Postgres |
| `search` | Searches stored notes by tag or category (`DatabaseAgent`). Type `recent` to see the latest notes | Postgres |
| `echo`   | Repeats what you type. End a message with `?` to see an options menu | nothing                         |

## Adding an agent

Add it in [`agents.py`](agents.py):

```python
class MyAgent(Agent):
    name = "mine"
    description = "Does something useful"

    def connect(self):            # optional: load models, open connections
        ...

    def send(self, message: str) -> Reply:
        return Reply("Pick one:", options=["A", "B"])   # options are optional

AGENTS.append(MyAgent)
```

If a reply includes `options`, the user sees them as a menu, and the option they pick is sent back to the agent as the next message.

