# Offline evolution scheme
# - We use a population of constant size 10
# - Each robot is evaluated for 20 seconds, though we may vary this number
# - The average speed during this evaluation is the fitness
# - We do parent selection using a binary tournament: select two parents at
#   random, the one with the best fitness is parent 1, repeat for parent 2.
# - Using this mechanism, we generate 10 children
# - After evaluation of the children, we either do:
# -- Plus scheme, sort *all* robots by fitness
# -- Comma scheme, get rid of the parents and continue with children only
from __future__ import absolute_import
import sys
import os

# Add "tol" directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__))+'/../')

import trollius
from trollius import From, Return
from tol.config import Config
from tol.manage import World
from sdfbuilder import Pose
from sdfbuilder.math import Vector3
import random
import csv
import itertools
from tol.logging import logger, output_console
import logging

# Log output to console
output_console()
logger.setLevel(logging.DEBUG)

# Script configuration
# Number of individuals in the population
POPULATION_SIZE = 10

# Number of children created in each generation
NUM_CHILDREN = 10

# Keep the parents or only use children
KEEP_PARENTS = True

# Number of generations to produce
NUM_GENERATIONS = 10

# Number of simulation seconds each individual is evaluated
EVALUATION_TIME = 20

# Maximum number of mating attempts between two parents
MAX_MATING_ATTEMPTS = 5


@trollius.coroutine
def evaluate_pair(world, tree, bbox):
    """
    Evaluates a single robot tree.
    :param world:
    :type world: World
    :param tree:
    :param bbox:
    :return: Evaluated Robot object
    """
    # Pause the world just in case it wasn't already
    yield From(world.pause(True))

    pose = Pose(position=Vector3(0, 0, 0.5 * bbox[2] + 0.25))
    fut = yield From(world.insert_robot(tree, pose))
    robot = yield From(fut)

    # Unpause the world to start evaluation
    yield From(world.pause(False))

    while True:
        if robot.age() >= EVALUATION_TIME:
            break

        yield From(trollius.sleep(0.01))

    fut = yield From(world.delete_robot(robot))
    yield From(world.pause(True))
    yield From(fut)
    raise Return(robot)


@trollius.coroutine
def evaluate_population(world, trees, bboxes):
    """
    :param world:
    :param population:
    :return:
    """
    robots = []
    print("Evaluating population...")
    for tree, bbox in itertools.izip(trees, bboxes):
        print("Evaluating individual...")
        robot = yield From(evaluate_pair(world, tree, bbox))
        robots.append(robot)
        print("Done.")

    print("Done evaluating population.")
    raise Return(robots)


def select_parent(parents):
    """
    Select a parent using a binary tournament.
    :param parents:
    :return:
    """
    p = random.sample(parents, 2)
    return p[0] if p[0].velocity() > p[1].velocity() else p[1]


def select_parents(parents):
    """
    :param parents:
    :return:
    """
    p1 = select_parent(parents)
    p2 = p1
    while p2 == p1:
        p2 = select_parent(parents)

    return p1, p2


@trollius.coroutine
def produce_generation(world, parents):
    """
    Produce the next generation of robots from
    the current.
    :param world:
    :param parents:
    :return:
    """
    print("Producing generation...")
    trees = []
    bboxes = []

    while len(trees) < NUM_CHILDREN:
        print("Producing individual...")
        p1, p2 = select_parents(parents)

        for j in xrange(MAX_MATING_ATTEMPTS):
            pair = yield From(world.attempt_mate(p1, p2))
            if pair:
                trees.append(pair[0])
                bboxes.append(pair[1])
                break
        print("Done.")

    print("Done producing generation.")
    raise Return(trees, bboxes)


def log_generation(gen_out, generation, robots):
    """
    :param gen_out:
    :param robots:
    :return:
    """
    print("================== GENERATION %d ==================" % generation)
    for robot in robots:
        gen_out.writerow([generation, robot.robot.id, robot.velocity()])


@trollius.coroutine
def run():
    conf = Config(
        output_directory='output',
        speed_window=1200
    )

    world = yield From(World.create(conf))

    # Open generations file line buffered
    gen_file = open(os.path.join(world.output_directory, 'generations.csv'), 'wb', buffering=1)
    gen_out = csv.writer(gen_file, delimiter=',')
    gen_out.writerow(['gen', 'robot_id', 'vel'])

    trees, bboxes = yield From(world.generate_population(POPULATION_SIZE))
    robots = yield From(evaluate_population(world, trees, bboxes))
    log_generation(gen_out, 0, robots)

    for generation in xrange(1, NUM_GENERATIONS):
        # Produce the next generation and evaluate them
        child_trees, child_bboxes = yield From(produce_generation(world, robots))
        children = yield From(evaluate_population(world, child_trees, child_bboxes))

        if KEEP_PARENTS:
            robots = children + robots
        else:
            robots = children

        # Sort the bots and reduce to population size
        robots = sorted(robots, key=lambda r: r.velocity(), reverse=True)[:POPULATION_SIZE]
        log_generation(gen_out, generation, robots)

    gen_file.close()


def main():
    try:
        loop = trollius.get_event_loop()
        loop.run_until_complete(run())
    except KeyboardInterrupt:
        print("Got Ctrl+C, shutting down.")


if __name__ == '__main__':
    main()
