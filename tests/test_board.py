"""Headless checks for the bug fixes and Tasks 1-4.  Run:  python tests/test_board.py"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random  # noqa: E402

import pygame  # noqa: E402
from game.board import Board, Gem, GEM_COLORS, GRID_SIZE  # noqa: E402

R, G, B, Y, P, O = GEM_COLORS


def make_board(rows):
    """Build a board from 8 strings of color letters; '*' marks a row-bomb, '|' a column-bomb
    (bomb takes the color of the letter after it, e.g. '*G')."""
    letters = dict(zip("RGBYPO", GEM_COLORS))
    board = Board(0, 0)
    for r, row in enumerate(rows):
        tokens, i = [], 0
        while i < len(row):
            if row[i] in "*|":
                tokens.append((letters[row[i + 1]], "row" if row[i] == "*" else "col"))
                i += 2
            else:
                tokens.append((letters[row[i]], None))
                i += 1
        assert len(tokens) == GRID_SIZE, row
        for c, (color, bomb) in enumerate(tokens):
            gem = Gem(color, r, c)
            gem.current_y = gem.target_y
            gem.bomb = bomb
            board.grid[r][c] = gem
    return board


# Checkerboard-ish base with no matches (rows alternate two 4-color patterns)
BASE = ["RGBYRGBY", "BYRGBYRG"] * 4


def test_startup_does_not_crash():
    for _ in range(50):
        board = Board(0, 0)
        assert all(board.grid[r][c] for r in range(GRID_SIZE) for c in range(GRID_SIZE))
        assert not board.find_matches(), "fresh board should have no ready-made matches"
        assert board.find_hint(), "fresh board should have a valid move"


def test_drop_and_refill_fills_every_column():
    board = make_board(BASE)
    for c in range(GRID_SIZE):
        board.grid[3][c] = None
    board.drop_and_refill()
    assert all(board.grid[r][c] for r in range(GRID_SIZE) for c in range(GRID_SIZE))


def test_task1_invalid_swap_costs_no_move():
    board = make_board(BASE)
    before = [[g.color for g in row] for row in board.grid]
    assert board.process_swap((0, 0), (0, 1)) is False
    assert board.moves_remaining == board.max_moves
    assert [[g.color for g in row] for row in board.grid] == before


def test_task1_valid_swap_costs_one_move():
    rows = list(BASE)
    rows[0] = "RRGRPOPO"  # swap (0,2)<->(1,2) brings an R into place
    rows[1] = "BYRGBYRG"
    board = make_board(rows)
    assert board.process_swap((0, 2), (1, 2)) is True
    assert board.moves_remaining == board.max_moves - 1
    assert board.score > 0


def test_task2_multiplier_is_exact():
    board = make_board(BASE)
    calls = {"n": 0}
    real_find_runs = board.find_runs

    def fake_find_runs():
        calls["n"] += 1
        if calls["n"] <= 3:  # three cascade levels, 3 gems each
            return [([(0, 0), (0, 1), (0, 2)], "row")]
        return []

    board.find_runs = fake_find_runs
    points = board.resolve_matches()
    board.find_runs = real_find_runs
    assert board.last_combo == 3
    assert points == 30 * 1 + 30 * 2 + 30 * 3


def test_task3_four_match_spawns_bomb():
    random.seed(0)  # refills are random; a lucky cascade could legitimately detonate the new bomb
    rows = list(BASE)
    rows[1] = "RRBRPOPO"
    rows[2] = "YPRBYPOB"  # (2,2) is R; swapping it up makes R R R R in row 1
    board = make_board(rows)
    assert board.process_swap((1, 2), (2, 2)) is True
    bombs = [(r, c, g.bomb) for r, row in enumerate(board.grid) for c, g in enumerate(row) if g.bomb]
    assert bombs, "4-in-a-row should leave a Bomb Gem"
    r, c, direction = bombs[0]
    assert direction == "row" and board.grid[r][c].color == R


def test_task3_vertical_four_makes_column_bomb():
    random.seed(0)  # refills are random; a lucky cascade could legitimately detonate the new bomb
    board = make_board(BASE)
    for r in range(4):
        board.grid[r][5].color = P
    board.resolve_matches()
    assert any(board.grid[r][5].bomb == "col" for r in range(GRID_SIZE))


def test_task3_matched_bomb_clears_its_row():
    board = make_board(BASE)
    board.grid[6][0].color, board.grid[6][0].bomb = G, "row"
    board.grid[6][1].color = G
    board.grid[6][2].color = G
    row6 = [board.grid[6][c] for c in range(GRID_SIZE)]
    points = board.resolve_matches()
    assert all(g not in board.grid[r] for g in row6 for r in range(GRID_SIZE)), "whole row should be cleared"
    assert points >= GRID_SIZE * 10


def test_task3_bomb_chain():
    board = make_board(BASE)
    board.grid[6][0].color, board.grid[6][0].bomb = G, "row"
    board.grid[6][1].color = G
    board.grid[6][2].color = G
    board.grid[6][5].bomb = "col"  # caught in the row blast -> clears column 5 too
    col5 = [board.grid[r][5] for r in range(GRID_SIZE)]
    board.resolve_matches()
    remaining = {id(g) for row in board.grid for g in row}
    assert not any(id(g) in remaining for g in col5)


def test_task4_hint_is_a_valid_swap():
    for _ in range(20):
        board = Board(0, 0)
        (p1, p2) = board.find_hint()
        assert board.is_adjacent(p1, p2)
        board.swap_gems(p1, p2)
        assert board.find_matches()


def test_task4_engine_shows_hint_after_idle():
    from game.game_engine import GameEngine, HINT_DELAY_MS
    engine = GameEngine(600, 650)
    engine.update()
    assert engine.hint is None
    engine.last_input_time -= HINT_DELAY_MS + 1
    engine.update()
    assert engine.hint is not None
    engine.handle_click((0, 0))
    assert engine.hint is None


def test_demo_board():
    random.seed(0)  # refills are random; a lucky cascade could legitimately detonate the new bomb
    board = Board(0, 0)
    board.load_demo()
    assert board.grid[6][0].bomb == "row"
    assert not board.find_matches()
    assert board.process_swap((1, 2), (2, 2))
    while board.is_animating():  # swaps are ignored while gems are still falling
        board.update()
    assert board.grid[6][0].bomb == "row"
    assert board.process_swap((6, 2), (7, 2))


if __name__ == "__main__":
    random.seed(int(os.environ.get("SEED", 57)))
    pygame.init()
    pygame.display.set_mode((600, 650))
    tests = [(n, f) for n, f in globals().items() if n.startswith("test_")]
    for name, fn in tests:
        fn()
        print(f"PASS  {name}")
    print(f"\nAll {len(tests)} tests passed.")
