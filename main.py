"""
NextLeap RAG Chatbot — Interactive CLI

Wires Phase 2 (VectorStore) → Phase 3 (Retrieval) → Phase 4 (LLM) → Phase 5 (Chatbot)
and starts an interactive terminal session.

Usage:
    python main.py

Environment variable required:
    GOOGLE_API_KEY=your_gemini_api_key
"""

import os
import sys
import logging

from dotenv import load_dotenv

# ── Minimal logging (warnings + errors only) ──────────────────────────────
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _banner():
    print("\n" + "=" * 55)
    print("   NextLeap RAG Chatbot")
    print("=" * 55)
    print("  Type your question and press Enter.")
    print("  Type 'exit' or 'quit' to end the session.")
    print("=" * 55 + "\n")


def build_chatbot():
    """Initialise all pipeline components and return a Chatbot instance."""

    # ── Phase 2: Vector Store ─────────────────────────────────────────────
    from phase_2.store import VectorStore
    print("[...] Loading vector store...", end=" ", flush=True)
    try:
        store = VectorStore()
    except Exception as e:
        print(f"\n[X] Failed to initialise VectorStore: {e}")
        sys.exit(1)
    print("[OK]")

    # ── Phase 3: Retrieval Pipeline ───────────────────────────────────────
    from phase_3.pipeline import RetrievalPipeline
    pipeline = RetrievalPipeline(vector_store=store)

    # ── Phase 4: Response Generator ───────────────────────────────────────
    from phase_4.generator import ResponseGenerator
    generator = ResponseGenerator()

    # ── Phase 5: Chatbot ──────────────────────────────────────────────────
    from phase_5.chatbot import Chatbot
    chatbot = Chatbot(
        retrieval_pipeline=pipeline,
        response_generator=generator,
    )

    return chatbot


def main():
    load_dotenv()

    if not os.getenv("GOOGLE_API_KEY"):
        print("[X] GOOGLE_API_KEY is not set. Add it to your .env file and try again.")
        sys.exit(1)

    _banner()
    chatbot = build_chatbot()
    print("\n[BOT] Hi! How may I help you?\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n[BYE] Goodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit", "bye", "q"}:
            print("\n[BYE] Goodbye!")
            break

        # ── Get chatbot reply ─────────────────────────────────────────────
        print("\n[BOT] ", end="", flush=True)
        reply = chatbot.chat(user_input)

        if not reply.success:
            print(f"Sorry, something went wrong: {reply.error}\n")
            continue

        print(reply.answer)

        if reply.citations:
            # Already embedded in reply.answer by the formatter, but shown
            # here as a separate line if you prefer clean output
            pass

        print()  # blank line between turns


if __name__ == "__main__":
    main()
