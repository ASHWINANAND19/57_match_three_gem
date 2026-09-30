# Match-3 Gem Swap Repair Lab

This project is a grid-based match-3 puzzle game using **Pygame**. It introduces students to 2D matrix manipulation, animated tile gravity, adjacent swap validation, recursive match resolution, and move-budget turn constraints within an object-oriented codebase.
---

## What's Provided

A working Match-3 Gem Swap game with:

- An 8x8 procedural gem grid with smooth vertical dropping animations
- Click-to-select and adjacent gem swapping mechanics
- Horizontal and vertical 3-in-a-row detection with automatic drop-and-refill resolution
- Score tracking, move budgeting, and win/loss overlay states

It has **one deliberate bug** and **three optional features** left as tasks to implement. You are expected to **analyze**, **interact with an AI assistant**, and **complete/fix** the game to make it fully functional and more interesting.

### **Use an LLM (e.g. ChatGPT or Claude) as your debugging and pair-programming partner for this lab.**
---

## Getting Started

### Setup

1. Make sure you have Python 3.10+ installed.
2. Install dependencies:

```bash
pip install pygame
```

3. Run the game:

```bash
python main.py
```

**Controls:** Left-click two adjacent gems to swap them. Press R to restart. Press B to load a demo board (a ready 4-in-a-row and a ready Bomb Gem match).

> On Python 3.14 the classic `pygame` wheel may fail to build; `pip install pygame-ce` is a drop-in replacement (`import pygame` still works).


## Tasks to Complete

Each task must be completed using an iterative process involving LLM suggestions and your critical code review.

### Task 1: Fix the invalid swap move deduction bug

Swapping two gems that do not produce any 3-in-a-row match reverts the gems back to their original tiles, but the game still docks a move. In board.process_swap(), self.moves_remaining is decremented before validating whether matches were found. This unfairly penalizes players for invalid moves. Move the deduction logic so that self.moves_remaining -= 1 is only executed when a swap successfully generates at least one match.

### Task 2: Implement cascade combo bonus scoring

Currently, all cleared gems award a flat 10 points each, even if a cascade causes multiple successive drop reactions. In board.resolve_matches(), track the cascade combo chain count and apply a progressive score multiplier (e.g., 1x for initial matches, 2x for secondary drops, 3x for tertiary cascades) so players are rewarded for planning chain reactions.

### Task 3: Implement 4-in-a-row special / bomb gems

In match-3 games, matching 4 gems of the same color typically creates an enhanced tile. Modify board.find_matches() and match resolution so that matching 4 gems spawns a special glowing "Bomb Gem". When that Bomb Gem is later matched or detonated, it clears its entire row or column.

### Task 4:Implement an idle hint indicator

If a player stays idle without clicking for more than 5 seconds, find a valid pair of adjacent gems that would produce a match if swapped, and render a pulsing outline or shimmer over those two gems to provide a gentle hint.

---

## Lab 4 Changes (completed)

| Item | What was done |
|---|---|
| **Hidden crash** | `drop_and_refill()` was missing its `for c in range(GRID_SIZE):` loop, so the game crashed on launch with `NameError: name 'c' is not defined`. Loop restored. The board is now generated with no ready-made matches and at least one valid move. |
| **Task 1** | `process_swap()` only decrements `moves_remaining` after a swap produces a match. Invalid swaps revert for free. |
| **Task 2** | `resolve_matches()` counts cascade levels and pays `10 x gems x level` (1x, 2x, 3x...). A `COMBO xN! +points` banner appears under the HUD. |
| **Task 3** | `find_runs()` finds maximal runs; a run of 4+ turns one gem (the swapped one if possible) into a glowing **Bomb Gem**. A horizontal run gives a row bomb (↔) and a vertical run gives a column bomb (↕). When a bomb is matched it clears its whole row/column, and bombs caught in a blast chain-detonate. |
| **Task 4** | After 5 s without a click, `find_hint()` locates a valid swap and the two gems get a pulsing golden outline. Any click hides it. |
| Extras | Refilling gems are clipped to the board, the board reshuffles if no valid moves remain, `[B]` demo board, headless tests in `tests/test_board.py` (`python tests/test_board.py`). |

## Expected Behavior

- Clicking two adjacent gems swaps them.
- If a swap creates 3 or more matching gems in a row or column, the matched gems clear, higher gems fall down, new gems populate the top, and remaining moves decrease by 1
- If a swap produces no matches, gems revert to their prior positions and the move counter does not decrease.
- Reaching 500 points triggers the STAGE CLEARED! win banner; running out of moves triggers OUT OF MOVES!
---

## Folder Structure

```
match_three_gem/
├── game/
│   ├── board.py
│   └── game_engine.py
├── main.py
└── README.md
```

---

## Submission Checklist

Submission is only the following three things:

- [] A 10-second video of gameplay **before** your changes, showing the bug/broken behavior
- [] A 10-second video of gameplay **after** your changes, showing the bug fixed and the new features working
- [] The Chat/LLM used page link, with the complete chat history
