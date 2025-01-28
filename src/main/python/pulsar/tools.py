from itertools import product
from copy import deepcopy
from datetime import datetime
from multiprocessing import Process, Event, Pool, Manager

from pulsar.Solver import Solver


backtracking_depth_max = 40
backtracking_step = 1
parallel_processes_max = 15


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

    print("Simple solve triggered..")

    grid, actions = get_actions_from_question(puzzle)

    solver = Solver(grid, actions)
    solver.solve()

    if solver.state_invalid:
        print("Puzzle Invalid!")

    if solver.state_solved:
        print("Puzzle Solved!")

    return solver


def apply_backtracking(grid, depth=1):

    actions_list = get_next_set_of_actions(grid, step=backtracking_step)
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


def sequential_solver(puzzle, response_queue):
    stt_time = datetime.now()
    print("Sequential Solver invoked!")
    solver = simple_solve(puzzle)
    print("Distinctive iterations done")

    if (not solver.state_invalid) and (not solver.state_solved):
        print("Simple Solve not enough, applying backtracking..")
        solver = apply_backtracking(solver.grid)
        print("Backtracking iterations done")

    if solver.state_solved:
        print("Solution Found!")
        payload = {'solution': solver.grid, 'duration': (datetime.now() - stt_time).total_seconds()}
    else:
        payload = {'solution': None, 'duration': (datetime.now() - stt_time).total_seconds()}
        print("Could not find solution!!")
    del solver

    try:
        response_queue.put(payload)
        print("Solution put into the response queue!")
    except ValueError:
        print(f"Error occurred while loading response queue")


def parallel_solver(puzzle, response_queue):

    stt_time = datetime.now()
    print("Parallel Solver invoked!")
    solver = simple_solve(puzzle)
    print("Distinctive iterations done")
    if solver.state_solved:
        print("Solution Found!")
        try:
            payload = {'solution': solver.grid, 'duration': 0}
            response_queue.put(payload)
            print("Solution put into the response queue!")
        except ValueError:
            print(f"Error occurred while loading response queue")
        return

    if (not solver.state_invalid) and (not solver.state_solved):
        print("Simple Solve not enough, applying multithreaded backtracking..")
        completion_event = Event()
        p = Process(target=worker_process, args=(1, completion_event, stt_time, deepcopy(solver.grid), response_queue))
        # p.daemon = True
        p.start()
        p.join()

    if response_queue.qsize() <= 0:
        print("Could not find solution!!")
        try:
            payload = {'solution': None, 'duration': (datetime.now() - stt_time).total_seconds()}
            response_queue.put(payload)
            print("Solution put into the response queue!")
        except ValueError:
            print(f"Error occurred while loading response queue")


def worker_process(depth, completion_event, stt_time, grid, response_queue):
    if (completion_event.is_set()) or (depth > backtracking_depth_max):
        # payload = {'solution': None, 'duration': 0}
        # print("Could not find solution!!")
        # try:
        #     response_queue.put(payload)
        #     print("Response put into the response queue!")
        # except ValueError:
        #     print(f"Error occurred while loading response queue")
        return

    actions_list = get_next_set_of_actions(grid, step=backtracking_step)
    process_list = []
    for actions in actions_list:
        solver = Solver(deepcopy(grid), actions)
        solver.solve()

        if solver.state_solved:
            completion_event.set()
            try:
                payload = {'solution': solver.grid, 'duration': (datetime.now() - stt_time).total_seconds()}
                response_queue.put(payload)
                print("Solution put into the response queue!")
            except ValueError:
                print(f"Error occurred while loading response queue")
            return

        if not solver.state_invalid:
            p = Process(target=worker_process, args=(depth+1, completion_event, stt_time, deepcopy(solver.grid), response_queue))
            process_list.append(p)

    for p in process_list:
        p.start()


def parallel_solver_pooling(puzzle, response_queue):

    stt_time = datetime.now()
    print("Parallel Solver invoked!")
    solver = simple_solve(puzzle)
    print("Distinctive iterations done")
    if solver.state_solved:
        print("Solution Found!")
        try:
            payload = {'solution': solver.grid, 'duration': 0}
            response_queue.put(payload)
            print("Solution put into the response queue!")
        except ValueError:
            print(f"Error occurred while loading response queue")
        return

    if (not solver.state_invalid) and (not solver.state_solved):
        print("Simple Solve not enough, applying multithreaded backtracking..")
        actions_list = get_next_set_of_actions(solver.grid, step=4)

        print(f"Total Iterations: {len(actions_list)}")

        with Manager() as manager:
            solution_found = manager.Event()
            tracker = manager.dict()

            tracker['total_processes'] = len(actions_list)
            tracker['pending_processes'] = len(actions_list)
            tracker['max_processes'] = parallel_processes_max
            tracker['active_processes'] = 0
            tracker['terminated_processes'] = 0
            tracker['backtracking_step'] = backtracking_step
            tracker['solution'] = None

            # with Pool(processes=parallel_processes_max) as pool:  # Adjust the number of processes as needed
            #     tasks = pool.starmap(create_tasks_for_pooling, [(solver.grid, actions, solution_found, tracker) for actions in actions_list])

            tracker['spawn_queue'] = [(deepcopy(solver.grid), actions) for actions in actions_list]

            with Pool(processes=parallel_processes_max) as pool:  # Adjust the number of processes as needed
                while (len(tracker['spawn_queue']) > 0) and (not solution_found.is_set()):
                    # pool.starmap(worker_process_pooling, tracker['spawn_queue'])

                    batch = []
                    while (len(tracker['spawn_queue']) > 0) and (len(batch) <= parallel_processes_max):
                        batch.append(tracker['spawn_queue'].pop())

                    for x in batch:
                        pool.apply_async(worker_process_pooling, args=(*x, 1, solution_found, tracker))

            if solution_found.is_set():
                payload = {'solution': tracker['solution'], 'duration': (datetime.now() - stt_time).total_seconds()}
                response_queue.put(payload)
                print("Solution put into the response queue!")
            else:
                print("Could not find solution!!")
                try:
                    payload = {'solution': None, 'duration': (datetime.now() - stt_time).total_seconds()}
                    response_queue.put(payload)
                    print("Solution put into the response queue!")
                except ValueError:
                    print(f"Error occurred while loading response queue")


# def create_tasks_for_pooling(grid, actions, solution_found, tracker):
#     return deepcopy(grid), actions, 1, solution_found, tracker


def worker_process_pooling(grid, actions, depth, solution_found, tracker):

    if solution_found.is_set() or (depth > backtracking_depth_max):
        if depth == 1:
            print("Solution already found, spawn denied!!")
            print(sel(tracker))
        return None

    if depth == 1:
        tracker['active_processes'] += 1
        if tracker['pending_processes'] > 0:
            tracker['pending_processes'] -= 1

        print(sel(tracker))

    solver = Solver(deepcopy(grid), actions)
    solver.solve()

    if solver.state_solved:
        solution_found.set()
        tracker['solution'] = solver.grid
        if depth == 1:
            tracker['active_processes'] -= 1
            print(sel(tracker))
            print("Solution Found!")
        return

    if not solver.state_invalid:
        actions_list = get_next_set_of_actions(solver.grid, step=tracker['backtracking_step'])

        if (tracker['pending_processes'] <= 0) and (tracker['active_processes'] < tracker['max_processes']):
            tracker['total_processes'] += len(actions_list)
            tracker['pending_processes'] += len(actions_list)
            tasks = [(deepcopy(solver.grid), actions) for actions in actions_list]
            tracker['spawn_queue'].append(tasks)
            print(f"spawning additional processes! {tasks[0]}")
        else:
            for actions in actions_list:
                worker_process_pooling(deepcopy(solver.grid), actions, depth+1, solution_found, tracker)

    if depth == 1:
        tracker['active_processes'] -= 1
        tracker['terminated_processes'] += 1
        print(sel(tracker))
    return None


def sel(tracker):
    return {idx: val for idx, val in tracker.items() if idx != "spawn_queue"}
