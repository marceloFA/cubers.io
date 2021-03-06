""" Functions for retrieving a random-state scramble for sliding tile puzzles. This is based on
https://github.com/asarandi/n-puzzle, heavily modified and streamlined for our use case. """
# pylint: disable=invalid-name,too-many-nested-blocks

from collections import deque
from itertools import groupby
from math import inf
from random import shuffle

# -------------------------------------------------------------------------------------------------

__EMPTY_TILE = 0

__MOVE_INVERSE_MAP = {
    'D': 'U',
    'U': 'D',
    'L': 'R',
    'R': 'L'
}

def get_sliding_tile_puzzle_scramble(n):
    """ Retrieves a random-state scramble for an `n` x `n` sliding tile puzzle.

    This assumes the solved state for the puzzle is in numerical order, with the blank space in the
    bottom-right corner. """

    # The solved state is the full range of tiles in numerical order, with the empty tile at the end
    solved_state = list(range(1, n**2)) + [__EMPTY_TILE]

    # Keep generating a random state of the puzzle until one is found that's solvable.
    puzzle = list(range(n**2))
    shuffle(puzzle)
    while not __is_solvable(puzzle, solved_state, n):
        shuffle(puzzle)

    # Make sure everything's a tuple, because the swaps that happen later end up making the puzzle
    # intermediate states as tuples.
    puzzle       = tuple(puzzle)
    solved_state = tuple(solved_state)

    # Find a solution to the scrambled puzzle using an IDA* search with Linear Conflicts heuristic.
    # This can take a while; grab a cup of coffee.
    steps_to_solved = __ida_star_search(puzzle, solved_state, n)
    if not steps_to_solved:
        raise Exception("Couldn't find a solution! This shouldn't happen.")

    return __convert_steps_to_scramble(steps_to_solved)


def __convert_steps_to_scramble(steps):
    """ Takes the sequence of puzzle states from scrambled to solved, and ultimately returns a
    nicely-formatted scramble to reach the scrambled state from solve.

    For each puzzle state transition, figure out which move was applied (U, D, L, R), and then
    take the inverse of the solution as the scramble. Reduce this (U U --> U2) so it reads a
    little more nicely. """

    def __get_move_between(state1, state2):
        """ Figure out which move was applied between two adjacent puzzle states """

        # Figure out the indices of tiles which were swapped between the states
        swapped_ixs = list()
        for i, val in enumerate(state1):
            if val != state2[i]:
                swapped_ixs.append(i)

        # It should just be a single pair of tiles that swapped, otherwise something is wrong
        if len(swapped_ixs) != 2:
            msg = "It seems like {} pieces swapped, which shouldn't be possible!"
            raise Exception(msg.format(len(swapped_ixs)))

        # Figure out which index represents the blank tile in the state2 state of the puzzle
        ix1, ix2 = swapped_ixs[0], swapped_ixs[1]
        if state2[ix1] == 0:
            blank_ix, number_ix = ix1, ix2
        else:
            blank_ix, number_ix = ix2, ix1

        # If the index difference between the swapped tiles is 1, the move was either L or R.
        # It's R if the blank tile is left of the numbered tile that moved.
        # It's L if the blank tile is right of the numbered tile that moved.
        if abs(blank_ix - number_ix) == 1:
            return 'R' if blank_ix < number_ix else 'L'

        # Otherwise the move must have been U or D.
        # It's D if the blank tile is above (lower in index) than the numbered tile that moved.
        # It's U if the blank tile is below (higher in index) than the numbered tile that moved.
        return 'D' if blank_ix < number_ix else 'U'

    # Iterate each adjacent pair of puzzle steps and figure out the move that was performed.
    # Inverse that move and stick it at the front of the list. The result is the inverted solution.
    inverse = list()
    for i in range(len(steps) - 1):
        start_pos = steps[i]
        final_pos = steps[i+1]
        move = __get_move_between(start_pos, final_pos)
        inverse.insert(0, __MOVE_INVERSE_MAP[move])

    def __smart_reduce(grouping):
        group_sum = sum(1 for _ in grouping)
        return '' if group_sum == 1 else group_sum

    # Turn the inversed solution into a nicely-formatted string.
    # This is the scramble we'll surface to the user.
    return ' '.join(f"{x}{__smart_reduce(y)}" for x, y in groupby(inverse))


def __count_inversions(puzzle, solved, size):
    """ Counts the number of inversions in the scrambled puzzle. An inversion is if, for any two
    tiles in the puzzle, the numerically higher tile appears before a numerically lower tile.

    Ex: [1, 3, 2, 4] --> 1 inversion  (3 is before 2)
    Ex: [3, 1, 4, 2] --> 3 inversions (3 is before 2 and 1, 4 is before 2) """

    inversions = 0
    for i in range(size * size - 1):
        for j in range(i + 1, size * size):
            vi = puzzle[i]
            vj = puzzle[j]
            if solved.index(vi) > solved.index(vj):
                inversions += 1

    return inversions


def __is_solvable(puzzle, solved, size):
    """ Determines if a provided (scrambled) puzzle is solvable into the provided solved state. """

    # Figure out the location of the empty tile in both the scrambled puzzle and solved state
    puzzle_zero_row    = puzzle.index(__EMPTY_TILE) // size
    puzzle_zero_column = puzzle.index(__EMPTY_TILE) % size
    solved_zero_row    = solved.index(__EMPTY_TILE) // size
    solved_zero_column = solved.index(__EMPTY_TILE) % size

    # Find the Manhattan distance between the location of the empty tile in the scrambled puzzle
    # and the solved state
    taxicab = abs(puzzle_zero_row - solved_zero_row) + abs(puzzle_zero_column - solved_zero_column)

    # Compare the inversions in the scrambled puzzle to its parity. If they are the same,
    # the puzzle is solveable. Otherwise, the puzzle cannot be solved.
    return (taxicab % 2) == (__count_inversions(puzzle, solved, size) % 2)


def __manhattan_distance(candidate, solved, size):
    """ A heuristic when solving sliding tile puzzles, which calculates the total
    'Manhattan distance' for the provided state of the puzzle compared to the solved state.
    This is the sum of the Manhattan distance between a tile's position in the scrambled state
    and the solved state, for all tiles except the empty tile. """

    distance = 0
    for i in range(size*size):
        if candidate[i] != 0 and candidate[i] != solved[i]:
            ci = solved.index(candidate[i])
            y = (i // size) - (ci // size)
            x = (i % size) - (ci % size)
            distance += abs(y) + abs(x)
    return distance


def __linear_conflicts(candidate, solved, size):
    """ A heuristic used in when solving sliding tile puzzles, which is added on top of the
    Manhattan distance. A linear conflict is when any two tiles appear in the same correct row
    or column, but are inverted with respect to each other. For example, the first row of a
    15 Puzzle [x, 3, 1, x] has a linear conflict between the 1 and 3 tiles.

    A linear conflict requires at least two moves to resolve. This heuristic counts the number of
    linear conflicts for a given puzzle state, multiplies this value by two, and adds it to
    puzzle's Manhattan distance. """

    def __count_conflicts(candidate_row, solved_row, size, ans=0):
        counts = [0 for x in range(size)]
        for i, tile_1 in enumerate(candidate_row):
            if tile_1 in solved_row and tile_1 != 0:
                for j, tile_2 in enumerate(candidate_row):
                    if tile_2 in solved_row and tile_2 != 0:
                        if tile_1 != tile_2:
                            if (solved_row.index(tile_1) > solved_row.index(tile_2)) and i < j:
                                counts[i] += 1
                            if (solved_row.index(tile_1) < solved_row.index(tile_2)) and i > j:
                                counts[i] += 1
        if max(counts) == 0:
            return ans * 2

        i = counts.index(max(counts))
        candidate_row[i] = -1
        ans += 1
        return __count_conflicts(candidate_row, solved_row, size, ans)

    candidate_rows    = [list() for _ in range(size)]
    candidate_columns = [list() for _ in range(size)]
    solved_rows       = [list() for _ in range(size)]
    solved_columns    = [list() for _ in range(size)]

    for y in range(size):
        for x in range(size):
            idx = (y * size) + x
            candidate_rows[y].append(candidate[idx])
            candidate_columns[x].append(candidate[idx])
            solved_rows[y].append(solved[idx])
            solved_columns[x].append(solved[idx])

    conflicts = 0
    for i in range(size):
        conflicts += __count_conflicts(candidate_rows[i], solved_rows[i], size)
        conflicts += __count_conflicts(candidate_columns[i], solved_columns[i], size)

    return conflicts + __manhattan_distance(candidate, solved, size)


def __clone_and_swap(data, ix1, ix2):
    """ Clones a tuple, swaps the values at the two provided indices, and returns the new tuple. """

    clone = list(data)
    clone[ix1], clone[ix2] = clone[ix2], clone[ix1]
    return tuple(clone)


def __possible_moves(puzzle, size):
    """ For a given puzzle state, return the new states after applying possible moves. """

    moves = list()

    i = puzzle.index(__EMPTY_TILE)
    if i % size > 0:
        left = __clone_and_swap(puzzle, i, i-1)
        moves.append(left)

    if i % size + 1 < size:
        right = __clone_and_swap(puzzle, i, i+1)
        moves.append(right)

    if i - size >= 0:
        up = __clone_and_swap(puzzle, i, i-size)
        moves.append(up)

    if i + size < len(puzzle):
        down = __clone_and_swap(puzzle, i, i+size)
        moves.append(down)

    return moves


def __ida_star_search(puzzle, solved, size):
    """ Performs an IDA* search on the provided (scrambled) puzzle to reach its solved state.
    Returns a list of puzzle states from the starting scrambled state to solved, where each state
    transition is due to a move applied to the puzzle. """

    def __search(path, g, bound, evaluated):
        evaluated += 1
        node = path[0]
        f = g + __linear_conflicts(node, solved, size)
        if f > bound:
            return f, evaluated
        if node == solved:
            return True, evaluated
        ret = inf
        for m in __possible_moves(node, size):
            if m not in path:
                path.appendleft(m)
                t, evaluated = __search(path, g + 1, bound, evaluated)
                if t is True:
                    return True, evaluated
                if t < ret:
                    ret = t
                path.popleft()
        return ret, evaluated

    bound = __linear_conflicts(puzzle, solved, size)
    path = deque([puzzle])
    evaluated = 0
    while path:
        t, evaluated = __search(path, 0, bound, evaluated)
        if t is True:
            path.reverse()
            return path

        if t is inf:
            return list()

        bound = t
