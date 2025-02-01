def flatten_index_equal_depth(depth, *args):
    dimensions = len(args)

    val = 0
    for x in range(dimensions):
        val += (args[x] * (depth ** x))

    return val + 1


def get_index_equal_depth(dimensions, depth, val):
    val -= 1
    indices = tuple()
    for x in range(dimensions):
        (depth ** (dimensions - 1 - x))
        indices += (int(val / (depth ** x)) % depth, )

    return indices
