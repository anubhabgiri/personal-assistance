"""Main entry point for the Personal Assistance System."""

import argparse
from chat_interface import ChatInterface


def main():
    """Main function to run the personal assistance system."""
    parser = argparse.ArgumentParser(
        description="Personal Assistance Note Processing System"
    )
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="Disable database storage",
    )
    parser.add_argument(
        "--auto-load-model",
        action="store_true",
        help="Automatically load the language model on startup",
    )

    args = parser.parse_args()

    # Initialize and run the chat interface
    chat = ChatInterface(
        use_db=not args.no_db,
        auto_load_model=args.auto_load_model,
    )
    chat.run()


if __name__ == "__main__":
    main()