"""Interactive chat loop: pick an agent, then talk to it."""

import argparse

from . import ui
from .agents import AGENTS, Agent, Reply

COMMANDS = {
    "/agent": "Switch to another agent",
    "/help": "Show this help",
    "/clear": "Clear the screen",
    "/exit": "Quit",
}

HELP = "\n".join(f"  {ui.cyan(c):<18} {d}" for c, d in COMMANDS.items()) + "\n" + ui.dim(
    "  Type '/' alone for a command menu. End a line with '\\' for multi-line input."
)


class ChatApp:
    def __init__(self):
        self.agent: Agent | None = None

    # ---- agent management -------------------------------------------------
    def choose_agent(self, name: str | None = None) -> bool:
        """Select (by name or via menu) and connect to an agent. Returns False if cancelled."""
        classes = {cls.name: cls for cls in AGENTS}
        if name is None:
            labels = [f"{cls.name:<8} {ui.dim(cls.description)}" for cls in AGENTS]
            picked = ui.select("Choose an agent", labels)
            if picked is None:
                return False
            name = AGENTS[labels.index(picked)].name
        if name not in classes:
            print(ui.red(f"Unknown agent '{name}'. Available: {', '.join(classes)}"))
            return False

        agent = classes[name]()
        print(ui.dim(f"Connecting to {name}..."))
        try:
            agent.connect()
        except KeyboardInterrupt:
            print(ui.yellow("Connection cancelled."))
            return False
        except Exception as e:  # missing deps, DB down, etc.
            print(ui.red(f"Could not connect to '{name}': {e}"))
            return False
        self.disconnect()  # only drop the old agent once the new one is ready
        self.agent = agent
        print(ui.green(f"Connected to {ui.bold(name)}.") + ui.dim(" Type /help for commands."))
        return True

    def disconnect(self) -> None:
        if self.agent:
            try:
                self.agent.disconnect()
            except Exception as e:
                print(ui.yellow(f"Error while disconnecting: {e}"))
            self.agent = None

    # ---- messaging ---------------------------------------------------------
    def send(self, message: str) -> None:
        """Send a message; if the agent replies with options, let the user pick one and continue."""
        while message:
            print(ui.dim("thinking..."))
            try:
                reply = self.agent.send(message)
            except KeyboardInterrupt:
                print(ui.yellow("Cancelled."))
                return
            except Exception as e:
                print(ui.red(f"Agent error: {e}"))
                return
            if isinstance(reply, str):
                reply = Reply(reply)

            print(f"{ui.bold(ui.green(self.agent.name + ' ›'))} {reply.text}\n")
            message = ui.select("Choose an option", reply.options) if reply.options else None

    # ---- commands ----------------------------------------------------------
    def run_command(self, cmd: str) -> bool:
        """Handle a slash command. Returns False when the app should exit."""
        if cmd == "/":
            labels = [f"{c:<8} {ui.dim(d)}" for c, d in COMMANDS.items()]
            picked = ui.select("Commands", labels)
            if picked is None:
                return True
            cmd = list(COMMANDS)[labels.index(picked)]

        name, _, arg = cmd.partition(" ")
        if name in ("/exit", "/quit"):
            return False
        if name == "/agent":
            self.choose_agent(arg.strip() or None)
        elif name == "/help":
            print(HELP)
        elif name == "/clear":
            print("\033[2J\033[H", end="")
        else:
            print(ui.red(f"Unknown command {name}. Type /help."))
        return True

    # ---- main loop ---------------------------------------------------------
    def run(self, agent_name: str | None = None) -> None:
        print(ui.bold(ui.cyan("Personal Assistance · Agent Chat")))
        print(ui.dim("Ctrl-D or /exit to quit.\n"))
        try:
            while self.agent is None:
                if not self.choose_agent(agent_name) and not ui.confirm("Try another agent?"):
                    return
                agent_name = None

            while True:
                try:
                    text = ui.ask(f"{ui.bold(ui.cyan('you ›'))} ")
                except KeyboardInterrupt:
                    print()
                    continue  # Ctrl-C clears the current line
                except EOFError:
                    print()
                    break
                if not text:
                    continue
                if text.startswith("/"):
                    if not self.run_command(text):
                        break
                    if self.agent is None and not self.choose_agent():
                        break
                    continue
                self.send(text)
        finally:
            self.disconnect()
            print(ui.dim("Bye!"))


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m chat", description="Chat with your agents.")
    parser.add_argument("-a", "--agent", help=f"Agent to connect to ({', '.join(a.name for a in AGENTS)})")
    parser.add_argument("-l", "--list", action="store_true", help="List available agents and exit")
    args = parser.parse_args()

    if args.list:
        for cls in AGENTS:
            print(f"{cls.name:<8} {cls.description}")
        return
    ChatApp().run(args.agent)
