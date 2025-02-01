from itertools import product
from copy import deepcopy
from datetime import datetime
from multiprocessing import Pool, Manager

from pulsar.Solver import Solver
from pulsar.SATSolver import SATSolver


backtracking_depth_max = 300
backtracking_step = 1
parallel_processes_max = 10


def get_backtracking_elements(grid, step):
    elements = []
    grid_size = len(grid)
    for size in range(2, (grid_size + 1)):
        for i in range(grid_size):
            for j in range(grid_size):
                if (len(grid[i][j]) > 1) and (len(grid[i][j]) <= size):
                    elements.append({'idx': (i, j), 'vals': grid[i][j]})
                    if len(elements) >= step:
                        return elements
    return elements


def get_next_set_of_actions(tempgrid, step):
    elements = get_backtracking_elements(tempgrid, step)

    iter_element_indices = [x['idx'] for x in elements]
    iter_val_combinations = list(product(*[x['vals'] for x in elements]))

    actions_list = []
    for combo in iter_val_combinations:
        actions = []
        for idx, val in zip(iter_element_indices, combo):
            actions.append({'idx': idx, 'val': val})
        actions_list.append(actions)

    return actions_list


def get_actions_from_question(puzzle):
    actions = []
    size = len(puzzle)
    for i in range(size):
        for j in range(size):
            if puzzle[i][j]:
                action = {'idx': (i, j), 'val': puzzle[i][j]}
                actions.append(action)

    grid = [[[z+1 for z in range(size)] for _ in range(size)] for _ in range(size)]
    return grid, actions


def simple_solve(puzzle):

    grid, actions = get_actions_from_question(puzzle)

    solver = Solver(grid, actions)
    solver.solve()

    if solver.state_invalid:
        print("Puzzle Invalid!")

    return solver


def apply_backtracking(grid, depth=1):

    actions_list = get_next_set_of_actions(grid, step=backtracking_step)
    solver = None
    for actions in actions_list:
        solver = Solver(deepcopy(grid), actions)
        solver.solve()

        if solver.state_solved:
            return solver

        # print(f"Depth= {depth}, Action - {actions} - valid? - { not solver.state_invalid}")
        if not solver.state_invalid:
            if depth <= backtracking_depth_max:
                solver = apply_backtracking(deepcopy(solver.grid), depth + 1)
                if solver.state_solved:
                    return solver
            else:
                print("Depth exceeded")

    return solver


def sequential_solver(puzzle, response_queue, session_id):
    stt_time = datetime.now()
    print("")
    print("Sequential Solver invoked!")
    solver = simple_solve(puzzle)
    print("Distinctive iterations done")

    if (not solver.state_invalid) and (not solver.state_solved):
        print("Simple Solve not enough, applying backtracking..")
        solver = apply_backtracking(solver.grid)
        print("Backtracking iterations done")

    if solver.state_solved:
        print("Solution Found!")
        payload = {'solution': solver.grid,
                   'duration': (datetime.now() - stt_time).total_seconds(),
                   'session': session_id}
    else:
        payload = {'solution': None,
                   'duration': (datetime.now() - stt_time).total_seconds(),
                   'session': session_id}
        print("Could not find solution!!")
    del solver

    try:
        response_queue.put(payload)
    except ValueError:
        print(f"Error occurred while loading response queue")


def parallel_solver(puzzle, response_queue, session_id):

    stt_time = datetime.now()
    print("")
    print("Parallel Solver invoked!")
    solver = simple_solve(puzzle)
    print("Distinctive iterations done")
    if solver.state_solved:
        print("Solution Found!")
        try:
            payload = {'solution': solver.grid, 'duration': 0, 'session': session_id}
            response_queue.put(payload)
            print("Solution put into the response queue!")
        except ValueError:
            print(f"Error occurred while loading response queue")
        return

    if not solver.state_invalid:
        print("Applying multithreaded backtracking..")
        actions_list = get_next_set_of_actions(solver.grid, step=1)

        with Manager() as manager:
            solution_found = manager.Event()
            tracker = manager.dict()

            tracker['total_processes'] = 0
            tracker['max_processes'] = parallel_processes_max
            tracker['active_processes'] = 0
            tracker['pending_processes'] = 0
            tracker['backtracking_step'] = backtracking_step
            tracker['backtracking_depth_max'] = backtracking_depth_max
            tracker['solution'] = None

            tracker['spawn_queue'] = manager.Queue()

            for idx, actions in enumerate(actions_list):
                tracker['spawn_queue'].put((deepcopy(solver.grid), actions, 1, f'{idx}'))

            with Pool(processes=parallel_processes_max) as pool:

                tracker['active_processes'] += 1
                tracker['total_processes'] += 1
                tracker['pending_processes'] = tracker['spawn_queue'].qsize() - 1
                async_results = [pool.apply_async(worker_process, args=(*tracker['spawn_queue'].get(),
                                                                        solution_found, tracker, True))]

                while not solution_found.is_set() and any(not result.ready() for result in async_results):
                    tracker['active_processes'] = sum(1 for result in async_results if not result.ready())

                    batch = []
                    while (not tracker['spawn_queue'].empty()) and (len(batch) < parallel_processes_max):
                        batch.append(tracker['spawn_queue'].get())

                    tracker['active_processes'] += len(batch)
                    tracker['total_processes'] += len(batch)
                    tracker['pending_processes'] = tracker['spawn_queue'].qsize()

                    for x in batch:
                        async_results.append(pool.apply_async(worker_process,
                                                              args=(*x, solution_found, tracker, True)))

            if solution_found.is_set():
                payload = {'solution': tracker['solution'],
                           'duration': (datetime.now() - stt_time).total_seconds(),
                           'session': session_id}
                response_queue.put(payload)
                print("Solution put into the response queue!")
            else:
                print("Could not find solution!!")
                try:
                    payload = {'solution': None,
                               'duration': (datetime.now() - stt_time).total_seconds(),
                               'session': session_id}
                    response_queue.put(payload)
                    print("Solution put into the response queue!")
                except ValueError:
                    print(f"Error occurred while loading response queue")

    else:
        try:
            payload = {'solution': None,
                       'duration': (datetime.now() - stt_time).total_seconds(),
                       'session': session_id}
            response_queue.put(payload)
            print("Response put into response queue!")
        except ValueError:
            print(f"Error occurred while loading response queue")


def worker_process(grid, actions, depth, pcs_id, solution_found, tracker, spawned):

    if solution_found.is_set():
        if spawned:
            # print("Solution already found, spawn denied!!")
            # print(f"Terminating {pcs_id}")
            printstats(tracker)
        return None

    if depth > tracker['backtracking_depth_max']:
        print(f"Depth exceeded, Killing branch {pcs_id}..")
        # tracker['promising_states'].put(deepcopy(grid), actions)
        if spawned:
            # print(f"Terminating {pcs_id}")
            printstats(tracker)
        return None

    if spawned:
        printstats(tracker)

    solver = Solver(deepcopy(grid), actions)
    solver.solve()

    if solver.state_solved:
        solution_found.set()
        tracker['solution'] = solver.grid
        if spawned:
            # print(f"Terminating {pcs_id}")
            printstats(tracker)
            # print("Solution Found!")
        return

    if not solver.state_invalid:
        actions_list = get_next_set_of_actions(solver.grid, step=tracker['backtracking_step'])

        available_spawns = tracker['max_processes'] - tracker['active_processes']

        # if available_spawns > 0:
        #     print("Sleeping")
        #     time.sleep(0.1)
        #     try:
        #         available_spawns_after = tracker['max_processes'] - tracker['active_processes_queue'].qsize()
        #     except NotImplementedError:
        #         available_spawns_after = tracker['max_processes']

        if tracker['spawn_queue'].empty() and (available_spawns > 0):
            spawn_actions = []
            while (available_spawns > 0) and (len(actions_list) > 0):
                spawn_actions.append(actions_list.pop())
                available_spawns -= 1

            for idx, actions in enumerate(spawn_actions):
                tracker['spawn_queue'].put((deepcopy(solver.grid), actions, depth+1, f'{pcs_id}.{idx}'))

        for actions in actions_list:
            worker_process(deepcopy(solver.grid), actions, depth+1, pcs_id, solution_found, tracker, False)

    if spawned:
        # print(f"Terminating {pcs_id}")
        printstats(tracker)

    return None


def printstats(tracker):
    print({
        'Total': tracker['total_processes'],
        'Active': tracker['active_processes'],
        'Pending': tracker['pending_processes'],
        'backtracking_depth_max': tracker['backtracking_depth_max']
    })


def sat_solver(puzzle, response_queue, session_id):
    stt_time = datetime.now()
    print("")
    print("SAT Solver invoked!")
    solver = SATSolver(puzzle)
    solution = solver.solve()

    payload = {'solution': solution,
               'duration': (datetime.now() - stt_time).total_seconds(),
               'session': session_id}
    try:
        response_queue.put(payload)
        del solver
    except ValueError:
        del solver
        print(f"Error occurred while loading response queue")
