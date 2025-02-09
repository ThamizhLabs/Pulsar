# Sudoku Solver Microservice

A highly performant, server-based microservice designed for solving Sudoku puzzles efficiently. This solution is built to cater to various solving methods, offering flexibility depending on the complexity of the puzzle and the required performance.

## Solvers
The microservice supports different solving techniques, each optimized for different use cases.

### 1. **Custom Solver**
- **Overview**: Solves the Sudoku puzzle using human-like techniques, mimicking the process of logical deduction commonly used by people when solving puzzles.
- **Use Case**: Ideal for small to medium complexity puzzles where a simpler, intuitive approach is sufficient.

### 2. **Serial Solver with Backtracking**
- **Overview**: Implements the backtracking algorithm in a sequential manner, trying all possible solutions until a valid one is found.
- **Use Case**: Suitable for medium-difficulty puzzles where exhaustive search is needed but computational resources are limited.
- **Performance**: May be slower for large puzzles due to the sequential nature of the algorithm.

### 3. **Parallel Solver with Backtracking**
- **Overview**: Utilizes the power of **multiprocessing** to parallelize the backtracking process, significantly improving performance for larger or more complex puzzles.
- **Use Case**: Best for high-difficulty puzzles or real-time puzzle-solving applications where faster results are needed.
- **Performance**: Greatly optimized for multi-core systems, allowing faster puzzle-solving due to parallel computation.

### 4. **SAT Solver**
- **Overview**: This advanced solver leverages **SAT (Boolean Satisfiability Problem)** solving techniques. The puzzle is represented as a set of Boolean equations, and the solver uses a SAT solver to find a valid solution.
- **Use Case**: Ideal for complex puzzles, where traditional solving techniques are inefficient. This solver can handle puzzles of any size and complexity.
- **Performance**: Most efficient for large or difficult puzzles due to the mathematical rigor of SAT solvers.

## Architecture

The microservice is structured to ensure scalability, efficiency, and flexibility. It runs as an independent process that listens for puzzle-solving requests via HTTP. Upon receiving a request, it selects the appropriate solver and processes the puzzle in the background.

- **Flask Microservice**: A lightweight, yet powerful web framework to handle incoming HTTP requests.
- **Multiprocessing for Parallel Solver**: For computational efficiency, especially with large datasets, multiprocessing is used to parallelize the backtracking algorithm in the Parallel Solver.
- **WebSocket-based Real-Time Communication**: Utilizes Flask-SocketIO for fast, real-time communication between the client and the solver.

## Setup

### Prerequisites

- Python 3.9
- Flask
- Flask-SocketIO
- Required Python libraries (listed in `env.yml`)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/ThamizhLabs/Pulsar.git
   cd sudoku-solver
   ```

2. Install dependencies:

   ```bash
   conda env create -f env.yml
   ```

3. Run the microservice:

   ```bash
   python src\main\scripts\run_pulsar.py
   ```

   The service will start on localhost:5000, and you can send puzzle-solving requests via HTTP or WebSocket.
## Example Request
HTTP POST to solve a puzzle using the Custom Algorithm:

   ```bash
   curl -X POST http://localhost:5000/solve
   -H "Content-Type: application/json"
   -d '{"puzzle": [[5, 3, 0, 0, 7, 0, 0, 0, 0], [6, 0, 0, 1, 9, 5, 0, 0, 0], ...]}'
   ```
The response will contain the solved puzzle in the same format.