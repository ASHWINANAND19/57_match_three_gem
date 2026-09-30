import math
import random
import pygame

GRID_SIZE = 8
TILE_SIZE = 60
GEM_COLORS = [
    (220, 50, 50),   # Red
    (50, 200, 50),   # Green
    (50, 100, 240),  # Blue
    (240, 200, 40),  # Yellow
    (180, 50, 220),  # Purple
    (240, 130, 40),  # Orange
]

POINTS_PER_GEM = 10


class Gem:

    def __init__(self, color, target_row, col):
        self.color = color
        self.target_row = target_row
        self.col = col
        # Start higher up to animate falling down
        self.current_y = (target_row - 2) * TILE_SIZE
        self.target_y = target_row * TILE_SIZE
        self.fall_speed = 12.0
        # Special "Bomb Gem" state: None, "row" (clears its row) or "col" (clears its column)
        self.bomb = None

    def update(self):
        if self.current_y < self.target_y:
            self.current_y += self.fall_speed
            if self.current_y > self.target_y:
                self.current_y = self.target_y

    def is_animating(self):
        return self.current_y < self.target_y


class Board:
    """Manages animated gem grid, gravity drops, score, and game limits."""

    def __init__(self, offset_x, offset_y, target_score=500, max_moves=20):
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.target_score = target_score
        self.max_moves = max_moves
        self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.selected = None
        self.score = 0
        self.moves_remaining = max_moves
        self.last_combo = 0
        self.last_points = 0
        self.reset()

    def reset(self):
        """Reset board grid, score, and move limits."""
        self.score = 0
        self.moves_remaining = self.max_moves
        self.selected = None
        self.last_combo = 0
        self.last_points = 0
        self.fill_board()

    def fill_board(self, preset=None):
        """Fill the grid with a fresh layout that has no ready-made matches but at
        least one valid move. `preset` maps (row, col) -> (color, bomb) for fixed cells."""
        preset = preset or {}
        while True:
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE):
                    if (r, c) in preset:
                        color, bomb = preset[(r, c)]
                    else:
                        color, bomb = self._safe_color(r, c), None
                    gem = Gem(color, r, c)
                    gem.current_y = gem.target_y  # Snap instantly on initial start
                    gem.bomb = bomb
                    self.grid[r][c] = gem
            if not self.find_matches() and self.find_hint():
                return

    def _safe_color(self, r, c):
        """Pick a color that doesn't complete a 3-run with the gems to the left/above."""
        banned = set()
        if c >= 2 and self.grid[r][c - 1].color == self.grid[r][c - 2].color:
            banned.add(self.grid[r][c - 1].color)
        if r >= 2 and self.grid[r - 1][c].color == self.grid[r - 2][c].color:
            banned.add(self.grid[r - 1][c].color)
        return random.choice([col for col in GEM_COLORS if col not in banned])

    def is_animating(self):
        """Returns True if any gem is currently dropping down."""
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c] and self.grid[r][c].is_animating():
                    return True
        return False

    def swap_gems(self, pos1, pos2):
        """Swap positions and target render coordinates of two gems."""
        r1, c1 = pos1
        r2, c2 = pos2

        g1, g2 = self.grid[r1][c1], self.grid[r2][c2]
        self.grid[r1][c1], self.grid[r2][c2] = g2, g1

        if self.grid[r1][c1]:
            self.grid[r1][c1].target_row = r1
            self.grid[r1][c1].target_y = r1 * TILE_SIZE
            self.grid[r1][c1].current_y = r1 * TILE_SIZE

        if self.grid[r2][c2]:
            self.grid[r2][c2].target_row = r2
            self.grid[r2][c2].target_y = r2 * TILE_SIZE
            self.grid[r2][c2].current_y = r2 * TILE_SIZE

    def is_adjacent(self, pos1, pos2):
        r1, c1 = pos1
        r2, c2 = pos2
        return abs(r1 - r2) + abs(c1 - c2) == 1

    def find_runs(self):
        """Scan grid for maximal horizontal/vertical runs of 3+ same-colored gems.
        Returns a list of (cells, direction) where direction is "row" or "col"."""
        runs = []

        # Horizontal runs
        for r in range(GRID_SIZE):
            c = 0
            while c < GRID_SIZE:
                end = c
                while (
                    end + 1 < GRID_SIZE
                    and self.grid[r][c]
                    and self.grid[r][end + 1]
                    and self.grid[r][end + 1].color == self.grid[r][c].color
                ):
                    end += 1
                if self.grid[r][c] and end - c + 1 >= 3:
                    runs.append(([(r, i) for i in range(c, end + 1)], "row"))
                c = end + 1

        # Vertical runs
        for c in range(GRID_SIZE):
            r = 0
            while r < GRID_SIZE:
                end = r
                while (
                    end + 1 < GRID_SIZE
                    and self.grid[r][c]
                    and self.grid[end + 1][c]
                    and self.grid[end + 1][c].color == self.grid[r][c].color
                ):
                    end += 1
                if self.grid[r][c] and end - r + 1 >= 3:
                    runs.append(([(i, c) for i in range(r, end + 1)], "col"))
                r = end + 1

        return runs

    def find_matches(self):
        """Return the set of all grid cells that are part of a 3+ match."""
        matched = set()
        for cells, _ in self.find_runs():
            matched.update(cells)
        return matched

    def drop_and_refill(self):
        # FIX: the column loop was missing, so `c` was undefined (NameError on start).
        for c in range(GRID_SIZE):
            empty_slots = 0
            for r in range(GRID_SIZE - 1, -1, -1):
                if self.grid[r][c] is None:
                    empty_slots += 1
                elif empty_slots > 0:
                    gem = self.grid[r][c]
                    gem.target_row = r + empty_slots
                    gem.target_y = (r + empty_slots) * TILE_SIZE
                    self.grid[r + empty_slots][c] = gem
                    self.grid[r][c] = None

            for r in range(empty_slots):
                color = random.choice(GEM_COLORS)
                gem = Gem(color, r, c)
                gem.current_y = -((empty_slots - r) * TILE_SIZE)
                self.grid[r][c] = gem

    def _detonate(self, cleared, protected):
        """Expand the cleared set with the row/column of every bomb in it (chains too)."""
        queue = [pos for pos in cleared if self.grid[pos[0]][pos[1]].bomb]
        detonated = set()
        while queue:
            r, c = queue.pop()
            if (r, c) in detonated:
                continue
            detonated.add((r, c))
            if self.grid[r][c].bomb == "row":
                blast = [(r, i) for i in range(GRID_SIZE)]
            else:
                blast = [(i, c) for i in range(GRID_SIZE)]
            for pos in blast:
                if pos in protected:
                    continue
                cleared.add(pos)
                if self.grid[pos[0]][pos[1]].bomb and pos not in detonated:
                    queue.append(pos)

    def resolve_matches(self, swap_positions=()):
        """Clear matches repeatedly until the board settles.

        Each cascade level multiplies the points: 1x for the initial match,
        2x for the first drop reaction, 3x for the next, and so on.
        Runs of 4+ leave behind a Bomb Gem; matched bombs clear a whole row/column.
        Returns the points earned.
        """
        combo = 0
        points = 0
        while True:
            runs = self.find_runs()
            if not runs:
                break
            combo += 1

            cleared = set()
            for cells, _ in runs:
                cleared.update(cells)

            # 4+ in a row -> spawn a Bomb Gem (on the swapped gem if it's part of the run)
            new_bombs = {}
            for cells, direction in runs:
                if len(cells) < 4:
                    continue
                candidates = [p for p in cells if not self.grid[p[0]][p[1]].bomb and p not in new_bombs]
                if not candidates:
                    continue
                spot = next((p for p in swap_positions if p in candidates), candidates[len(candidates) // 2])
                new_bombs[spot] = direction

            self._detonate(cleared, protected=new_bombs)
            cleared -= set(new_bombs)

            points += len(cleared) * POINTS_PER_GEM * combo
            for (r, c), direction in new_bombs.items():
                self.grid[r][c].bomb = direction
            for r, c in cleared:
                self.grid[r][c] = None
            self.drop_and_refill()
            swap_positions = ()  # Cascades aren't tied to the player's swap

        self.last_combo = combo
        self.last_points = points
        return points

    def process_swap(self, pos1, pos2):
        if not self.is_adjacent(pos1, pos2) or self.is_game_over() or self.is_animating():
            return False

        self.swap_gems(pos1, pos2)
        matches = self.find_matches()

        if not matches:
            self.swap_gems(pos1, pos2)  # Revert invalid swap (no move is spent)
            return False

        # FIX: only a successful, match-making swap costs a move.
        self.moves_remaining -= 1
        self.score += self.resolve_matches(swap_positions=(pos1, pos2))

        if self.find_hint() is None:
            self.fill_board()  # No moves left on the board -> reshuffle
        return True

    def find_hint(self):
        """Return a pair of adjacent positions whose swap would make a match, or None."""
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                for dr, dc in ((0, 1), (1, 0)):
                    r2, c2 = r + dr, c + dc
                    if r2 >= GRID_SIZE or c2 >= GRID_SIZE:
                        continue
                    g = self.grid
                    g[r][c], g[r2][c2] = g[r2][c2], g[r][c]
                    has_match = bool(self.find_matches())
                    g[r][c], g[r2][c2] = g[r2][c2], g[r][c]
                    if has_match:
                        return (r, c), (r2, c2)
        return None

    def load_demo(self):
        """Demo layout: row 1 has a 4-in-a-row ready (swap (1,2)<->(2,2)) and
        row 6 has a row-bomb ready to be matched (swap (6,2)<->(7,2)). Column 5 is
        stacked so the bomb's blast drops purples into a guaranteed x2 cascade combo."""
        red, green, blue, yellow, purple = GEM_COLORS[:5]
        preset = {
            (1, 0): (red, None), (1, 1): (red, None), (1, 2): (blue, None),
            (1, 3): (red, None), (2, 2): (red, None),
            (6, 0): (green, "row"), (6, 1): (green, None), (6, 2): (yellow, None),
            (7, 2): (green, None),
            (4, 5): (purple, None), (5, 5): (purple, None), (6, 5): (blue, None),
            (7, 5): (purple, None),
        }
        self.selected = None
        self.fill_board(preset)

    def is_game_over(self):
        return self.score >= self.target_score or self.moves_remaining <= 0

    def check_result(self):
        if self.score >= self.target_score:
            return "WIN"
        if self.moves_remaining <= 0:
            return "LOSS"
        return None

    def update(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c]:
                    self.grid[r][c].update()

    def render(self, surface, hint=None):
        board_rect = pygame.Rect(
            self.offset_x, self.offset_y, GRID_SIZE * TILE_SIZE, GRID_SIZE * TILE_SIZE
        )
        pygame.draw.rect(surface, (20, 22, 28), board_rect, border_radius=8)
        pygame.draw.rect(surface, (60, 65, 75), board_rect, width=3, border_radius=8)

        pulse = (math.sin(pygame.time.get_ticks() / 150) + 1) / 2  # 0..1

        # Keep refilling gems (which start above the board) from drawing over the HUD
        surface.set_clip(board_rect)
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                gem = self.grid[r][c]
                if gem:
                    x = self.offset_x + c * TILE_SIZE
                    y = self.offset_y + gem.current_y
                    tile_rect = pygame.Rect(x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4)

                    pygame.draw.rect(surface, gem.color, tile_rect, border_radius=10)
                    pygame.draw.rect(
                        surface, (255, 255, 255), tile_rect, width=1, border_radius=10
                    )
                    if gem.bomb:
                        self._render_bomb(surface, gem, tile_rect, pulse)

                if self.selected == (r, c):
                    sel_x = self.offset_x + c * TILE_SIZE
                    sel_y = self.offset_y + r * TILE_SIZE
                    sel_rect = pygame.Rect(sel_x + 2, sel_y + 2, TILE_SIZE - 4, TILE_SIZE - 4)
                    pygame.draw.rect(
                        surface, (255, 255, 255), sel_rect, width=4, border_radius=10
                    )

        if hint:
            self._render_hint(surface, hint, pulse)
        surface.set_clip(None)

    def _render_bomb(self, surface, gem, tile_rect, pulse):
        """Glowing halo + dark core with an arrow showing the blast direction."""
        glow = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        radius = int(20 + 8 * pulse)
        pygame.draw.circle(glow, (255, 255, 255, int(70 + 110 * pulse)), (TILE_SIZE // 2, TILE_SIZE // 2), radius)
        surface.blit(glow, (tile_rect.x - 2, tile_rect.y - 2))

        cx, cy = tile_rect.center
        pygame.draw.circle(surface, (25, 25, 30), (cx, cy), 13)
        pygame.draw.circle(surface, gem.color, (cx, cy), 13, width=3)
        if gem.bomb == "row":
            pygame.draw.line(surface, (255, 255, 255), (cx - 8, cy), (cx + 8, cy), 3)
            pygame.draw.polygon(surface, (255, 255, 255), [(cx - 11, cy), (cx - 6, cy - 4), (cx - 6, cy + 4)])
            pygame.draw.polygon(surface, (255, 255, 255), [(cx + 11, cy), (cx + 6, cy - 4), (cx + 6, cy + 4)])
        else:
            pygame.draw.line(surface, (255, 255, 255), (cx, cy - 8), (cx, cy + 8), 3)
            pygame.draw.polygon(surface, (255, 255, 255), [(cx, cy - 11), (cx - 4, cy - 6), (cx + 4, cy - 6)])
            pygame.draw.polygon(surface, (255, 255, 255), [(cx, cy + 11), (cx - 4, cy + 6), (cx + 4, cy + 6)])
        pygame.draw.rect(surface, (255, 255, 255), tile_rect, width=2, border_radius=10)

    def _render_hint(self, surface, hint, pulse):
        """Pulsing golden outline over the two hinted gems."""
        overlay = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        alpha = int(90 + 165 * pulse)
        width = 3 + int(3 * pulse)
        pygame.draw.rect(overlay, (255, 230, 90, alpha // 4), overlay.get_rect(), border_radius=12)
        pygame.draw.rect(overlay, (255, 230, 90, alpha), overlay.get_rect(), width=width, border_radius=12)
        for r, c in hint:
            surface.blit(overlay, (self.offset_x + c * TILE_SIZE, self.offset_y + r * TILE_SIZE))
