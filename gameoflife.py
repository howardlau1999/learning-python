import argparse
import time
import random
import os
from collections import namedtuple, Counter
parser = argparse.ArgumentParser()
parser.add_argument("--width", default=5, type=int)
parser.add_argument("--height", default=5, type=int)
parser.add_argument("--alives", default=5, type=int)
parser.add_argument("--delay", type=float)
parser.add_argument("--steps", default=10, type=int)
parser.add_argument("--init", type=str)
args = parser.parse_args()

ALIVE = "#"
DEATH = "."

Query = namedtuple("Query", ("r", "c"))
Neighbour = namedtuple("Neighbour", ("dr", "dc"))
Transition = namedtuple("Transition", ("r", "c", "next_state"))
Tick = namedtuple("Tick", "step")

neighbours = [Neighbour(dr, dc) for dr in range(-1, 2)
              for dc in range(-1, 2) if dr or dc]

def count_alive_neighbours(r, c):
    neighbour_states = []
    for neighbour in neighbours:
        state = yield Query(r + neighbour.dr, c + neighbour.dc)
        neighbour_states.append(state)
    return Counter(neighbour_states)[ALIVE]


def game_logic(state, alive_neighbours):
    if state == ALIVE:
        if alive_neighbours < 2:
            return DEATH
        elif alive_neighbours > 3:
            return DEATH
    else:
        if alive_neighbours == 3:
            return ALIVE
    return state

def step_cell(r, c):
    state = yield Query(r, c)
    alive_neighbours = yield from count_alive_neighbours(r, c)
    next_state = game_logic(state, alive_neighbours)
    yield Transition(r, c, next_state)

class GridWorld(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grids = []
        for _ in range(height):
            self.grids.append([DEATH] * width)

    def random_init(self, alive_lives):
        while alive_lives > 0:
            r = random.randint(0, self.height - 1)
            c = random.randint(0, self.width - 1)
            if self.grids[r][c] == DEATH:
                self.grids[r][c] = ALIVE
                alive_lives -= 1

    def from_file(self, filename):
        self.grids = []
        with open(filename) as f:
            line = next(f).strip()
            self.width = len(line)
            self.grids.append(line)
            for line in f:
                line = line.strip()
                if len(line) != self.width:
                    raise RuntimeError("Width does not match")
                self.grids.append(line)
        self.height = len(self.grids)

    def query(self, r, c):
        return self.grids[r % self.height][c % self.width]

    def transition(self, r, c, next_state):
        self.grids[r % self.height][c % self.width] = next_state

    def event_loop(self):
        step = 0
        while True:
            for r in range(self.height):
                for c in range(self.width):
                    yield from step_cell(r, c)
            yield Tick(step)
            step += 1

    def simulate(self, steps=10, delay=None):
        step = 0
        event_loop = self.event_loop()
        event = next(event_loop)
        next_generation = GridWorld(self.width, self.height)
        print("Initial: ")
        print(self)
        if delay is not None:
            time.sleep(delay)
        while step < steps:
            if isinstance(event, Tick):
                step = event.step
                self.grids = next_generation.grids
                next_generation = GridWorld(self.width, self.height)
                os.system("clear")
                print("Step: {step}/{steps}".format(step=step, steps=steps))
                print(self)
                if delay is not None:
                    time.sleep(delay)
                event = next(event_loop)
            elif isinstance(event, Query):
                event = event_loop.send(self.query(*event))
            elif isinstance(event, Transition):
                next_generation.transition(*event)
                event = next(event_loop)
            

    def __str__(self):
        return '\n'.join([''.join(row) for row in self.grids])

def main():
    width = args.width
    height = args.height
    steps = args.steps
    delay = args.delay
    alives = args.alives

    if args.init:
        world = GridWorld(0, 0)
        world.from_file(args.init)
    else:
        world = GridWorld(width, height)
        world.random_init(alives)
    world.simulate(steps, delay)

if __name__ == "__main__":
    main()
