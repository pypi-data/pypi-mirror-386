# ![Wove](wove.png)

[![PyPI](https://img.shields.io/pypi/v/wove)](https://pypi.org/project/wove/)
[![GitHub license](https://img.shields.io/github/license/curvedinf/wove)](LICENSE)
[![coverage](coverage.svg)](https://github.com/curvedinf/wove/actions/workflows/coverage.yml)
[![GitHub last commit](https://img.shields.io/github/last-commit/curvedinf/wove)](https://github.com/curvedinf/wove/commits/main)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/wove)](https://pypi.org/project/wove/)
[![GitHub stars](https://img.shields.io/github/stars/curvedinf/wove)](https://github.com/curvedinf/wove/stargazers)
[![Ko-fi Link](kofi.webp)](https://ko-fi.com/A0A31B6VB6)

[![Python 3.8](https://github.com/curvedinf/wove/actions/workflows/python-3-8.yml/badge.svg)](https://github.com/curvedinf/wove/actions/workflows/python-3-8.yml)
[![Python 3.9](https://github.com/curvedinf/wove/actions/workflows/python-3-9.yml/badge.svg)](https://github.com/curvedinf/wove/actions/workflows/python-3-9.yml)
[![Python 3.10](https://github.com/curvedinf/wove/actions/workflows/python-3-10.yml/badge.svg)](https://github.com/curvedinf/wove/actions/workflows/python-3-10.yml)
[![Python 3.11](https://github.com/curvedinf/wove/actions/workflows/python-3-11.yml/badge.svg)](https://github.com/curvedinf/wove/actions/workflows/python-3-11.yml)
[![Python 3.12](https://github.com/curvedinf/wove/actions/workflows/python-3-12.yml/badge.svg)](https://github.com/curvedinf/wove/actions/workflows/python-3-12.yml)
[![Python 3.13](https://github.com/curvedinf/wove/actions/workflows/python-3-13.yml/badge.svg)](https://github.com/curvedinf/wove/actions/workflows/python-3-13.yml)
[![Python 3.14](https://github.com/curvedinf/wove/actions/workflows/python-3-14.yml/badge.svg)](https://github.com/curvedinf/wove/actions/workflows/python-3-14.yml)
[![Python 3.14 (free-threaded)](https://github.com/curvedinf/wove/actions/workflows/python-3-14t.yml/badge.svg)](https://github.com/curvedinf/wove/actions/workflows/python-3-14t.yml)

Beautiful Python async.

## Table of Contents
- [What is Wove For?](#what-is-wove-for)
- [Installation](#installation)
- [The Basics](#the-basics)
- [Wove's Design Pattern](#woves-design-pattern)
- [Core API](#core-api)
- [More Spice](#more-spice)
- [Advanced Features](#advanced-features)
- [Background Processing](#background-processing)
- [Benchmarks](#benchmarks)
- [More Examples](#more-examples)

## What is Wove For?
Wove is for running high latency async tasks like web requests and database queries concurrently in the same way as 
asyncio, but with a drastically improved user experience.
Improvements compared to asyncio include:
-   **Looks Like Normal Python**: Parallelism and execution order are implicit. You write simple, decorated functions. No manual task objects, no callbacks.
-   **Reads Top-to-Bottom**: The code in a `weave` block is declared in the order it is executed inline in your code instead of in disjointed functions.
-   **Sync or Async**: Mix `async def` and `def` freely. A `weave` block can be inside or outside an async context. Sync functions are run in a background thread pool to avoid blocking the event loop.
-   **Automatic Parallelism**: Wove builds a dependency graph from your task signatures and runs independent tasks concurrently as soon as possible.
-   **High Visibility**: Wove includes debugging tools that allow you to identify where exceptions and deadlocks occur across parallel tasks, and inspect inputs and outputs at each stage of execution.
-   **Normal Python Data**: Wove's task data looks like normal Python variables because it is. This is because of inherent multithreaded data safety produced in the same way as map-reduce.
-   **Minimal Boilerplate**: Get started with just the `with weave() as w:` context manager and the `@w.do` decorator.
-   **Fast**: Wove has low overhead and internally uses `asyncio`, so performance is comparable to using `threading` or `asyncio` directly.
-   **Zero Dependencies**: Wove is pure Python, using only the standard library. It can be easily integrated into any Python project whether the project uses `asyncio` or not.
## Installation
Download wove with pip:
```bash
pip install wove
```
## The Basics
The core of Wove's functionality is the `weave` context manager. It is used in a `with` block to define a list of tasks that will be executed as concurrently and as soon as possible. When Python closes the `weave` block, the tasks are executed immediately based on a dependency graph that Wove builds from the function signatures. Results of a task are passed to any same-named function parameters. The result of the last task that runs are available in `w.result.final`.
```python
import time
from wove import weave
with weave() as w:
    # These first two tasks run concurrently.
    @w.do
    def magic_number():
        time.sleep(1.0)
        return 42
    @w.do
    def important_text():
        time.sleep(1.0)
        return "The meaning of life"
    # This task depends on the first two. It runs only after both are complete.
    @w.do
    def combined(important_text, magic_number):
        return f"{important_text} is {magic_number}!"
    # When the `with` block closes, all tasks are executed.
print(w.result.final)
# >> The meaning of life is 42!
print(f"The magic number was {w.result.magic_number}")
# >> The magic number was 42
print(f'The important text was "{w.result["important_text"]}"')
# >> The important text was "The meaning of life"
```
## Wove's Design Pattern
Wove is designed to be added inline in your existing functions. Since it is not required to be in an `async` block, it is useful for retrofitting into any IO-bound parallelizable process. For instance in a non-async Django view, you can run your database lookups and related code in parallel.
```python
# views.py
import time
from django.shortcuts import render
from wove import weave
from .models import Author, Book

def author_details(request, author_id):
    with weave() as w:
        # `author` and `books` run concurrently
        @w.do
        def author():
            return Author.objects.get(id=author_id)
        @w.do
        def books():
            return list(Book.objects.filter(author_id=author_id))

        # Map the books to a task that updates each of their prices concurrently
        @w.do("books", retries=3)
        def books_with_prices(book):
            book.get_price_from_api()
            return book

        # When everything is done, create the template context
        @w.do
        def context(author, books_with_prices):
            return {
                "author": author,
                "books": books_with_prices,
            }
    return render(request, "author_details.html", w.result.final)
```
We suggest naming `weave` tasks with nouns instead of verbs. Since `weave` tasks are designed to be run immediately like inline code, and not be reused, noun names reinforce the concept that a `weave` task represents its output data instead of its action.
## Core API
The two core Wove tools are:
-   `weave()`: An `async` context manager used in either a `with` or `async with` block that creates the execution environment for your tasks. When the `weave` block ends, all tasks will be executed in the order of their dependency graph. The `weave` object has a `result` attribute that contains the results of all tasks and a `.final` attribute that contains the result of the last task.
-   `@w.do`: A decorator that registers a function as a task to be run within the `weave` block. It can be used on both `def` and `async def` functions interchangeably, with non-async functions being run in a background thread pool to avoid blocking the event loop. It can optionally be passed an iterable, and if so, the task will be run concurrently for each item in the iterable. It can also be passed a string of another task's name, and if so, the task will be run concurrently for each item in the iterable result of the named task.
## More Spice
This example demonstrates Wove's advanced features, including inheritable overridable Weaves, static task mapping, dynamic task mapping, merging an external function, and a complex task graph.
```python
import time
import numpy as np
from wove import Weave, weave, merge

# An external function that will be mapped with `merge`
def quality_check(data):
    return any(np.isnan(data))

# Define a reusable base pipeline
class DataPipeline(Weave):
    @Weave.do(retries=2, timeout=60.0)
    def dataset(self, records: int):
        # Initial data loading - the top of the diamond.
        # `records` is provided by the `weave()` call below.
        time.sleep(0.1)
        return np.linspace(0, 10, records)
    
    @Weave.do("dataset")
    def feature_a(self, item):
        # First parallel processing branch.
        time.sleep(0.2)
        return np.sin(item)
    
    @Weave.do("dataset")
    def feature_b(self, item):
        # Second parallel processing branch.
        time.sleep(0.3)
        return np.cos(item)
    
    @Weave.do
    def merged_features(self, feature_a, feature_b):
        # Merge the results from parallel branches - bottom of the diamond.
        return np.column_stack((feature_a, feature_b))
    
    @Weave.do
    async def report(self, merged_features):
        # Dynamically map an external function using `merge`.
        quality_result = any(await merge(quality_check, merged_features))
        quality_status = "WARN: NaN values detected" if quality_result else "OK"
        # Create a report from the merged features.
        return {
            "mean": float(np.mean(merged_features)),
            "std": float(np.std(merged_features)),
            "shape": merged_features.shape,
            "quality_status": quality_status,
        }
# The class isn't executed right now

# Run a customized version of the pipeline
with weave(DataPipeline, records=1_000) as w:
    # Override one of the feature steps.
    # Any parameters in the parent `do` are defaults here.
    @w.do("dataset")
    def feature_a(item):
        return np.tanh(item)
# The pipeline runs when the `with` block ends

print(f"Pipeline complete. Results: {w.result.final}")
# >> Pipeline complete. Results: {'mean': 0.9302537626956293, 'std': 0.18500793874408072, 'shape': (1000, 2), 'quality_status': 'OK'}
```
## Advanced Features
### Context parameters
The `weave()` context manager has several optional parameters:
-   **`parent_weave: Weave`**: A `Weave` class to inherit tasks from.
-   **`debug: bool`**: If `True`, prints a detailed execution plan to the console before running.
-   **`max_workers: int`**: The maximum number of threads for running synchronous tasks in the background.
-   **`background: bool`**: If `True`, runs the entire weave in a background thread.
-   **`fork: bool`**: If `True` and `background` is `True`, runs the weave in a forked process instead of a thread.
-   **`on_done: callable`**: A callback function to be executed when a background weave is complete.
-   **`**kwargs`**: Any additional keyword arguments passed to `weave()` become initialization data that can be used as task parameters.
### Task parameters
The `@w.do` decorator has several optional parameters for convenience:
-   **`retries: int`**: The number of times to re-run a task if it raises an exception.
-   **`timeout: float`**: The maximum number of seconds a task can run before being cancelled.
-   **`workers: int`**: For mapped tasks only, this limits the number of concurrent instances of the task running at a time.
-   **`limit_per_minute: int`**: For mapped tasks only, this creates an interval between launching new task instances.
### Local Task Mapping
You can map a task to a local iterable by passing the iterable to the `@w.do` decorator. Wove will run instances of the task concurrently for each item in the iterable and collect the results as a list after all instances have completed. The result list will be passed to any dependent tasks through the same-named parameter.
```python
from wove import weave

numbers = [10, 20, 30]
with weave() as w:
    # This block is magically an `async with` block so you can use async functions.
    # Map each item from numbers to the squares function.
    @w.do(numbers)
    async def squares(item):
        return item * item
    # Collect the results.
    @w.do
    def summary(squares):
        return f"Sum of squares: {sum(squares)}"
print(w.result.final)
# Expected output:
# Sum of squares: 1400
```
### Dependent Task Mapping
You can also map a task over the result of another task or over initialization data by passing the dependency's name as a string to the decorator. This is especially useful when an iterable needs to be generated dynamically. If the mapped dependency is a task, Wove ensures the upstream task completes before starting the mapped tasks.
```python
import asyncio
from wove import weave
async def main():
    step = 10
    async with weave(min=10, max=40) as w:
        # Generates the data we want to map over.
        @w.do
        async def numbers(min, max):
            # This scope can read local variables outside the `weave` block, but
            # passing them in as initialization data is cleaner.
            return range(min, max, step)
        # Map each item produced by `numbers` to the `squares` function.
        # Each item's instance of `squares` will run concurrently, and then
        # be collected as a list after all have completed.
        @w.do("numbers")
        async def squares(item):
            return item * item
        # Collects the results.
        # You can mix `async def` and `def` tasks.
        @w.do
        def summary(squares):
            return f"Sum of squares: {sum(squares)}"
    print(w.result.final)
asyncio.run(main())
# Expected output:
# Sum of squares: 1400
```
### Complex Task Graphs
Wove can handle complex task graphs with nested `weave` blocks, `@w.do` decorators, and `merge` functions. Before a `weave` block is executed, wove builds a dependency graph from the function signatures and creates a plan to execute the tasks in the correct order such that tasks run as concurrently and as soon as possible. In addition to typical map-reduce patterns, you can also implement diamond graphs and other complex task graphs. A "diamond" dependency graph is one where multiple concurrent tasks depend on a single upstream task, and a final downstream task depends on all of them.
```python
import asyncio
from wove import weave
async def main():
    async with weave() as w:
        @w.do
        async def user_id():
            return 123
        
        # Both `user_profile` and `user_orders` depend on `user_id`
        # so they will run concurrently after `user_id` completes.
        @w.do
        async def user_profile(user_id):
            print(f"-> Fetching profile for user {user_id}...")
            await asyncio.sleep(0.1)
            return {"name": "Alice"}
        @w.do
        async def user_orders(user_id):
            print(f"-> Fetching orders for user {user_id}...")
            await asyncio.sleep(0.1)
            return [{"order_id": 1, "total": 100}, {"order_id": 2, "total": 50}]
        
        # Automatically wait until both `user_profile` and `user_orders`
        # complete then pass their results to `report`.
        @w.do
        def report(user_profile, user_orders):
            name = user_profile["name"]
            total_spent = sum(order["total"] for order in user_orders)
            return f"Report for {name}: Total spent: ${total_spent}"
    print(w.result.final)
asyncio.run(main())
# Expected output (the first two lines may be swapped):
# -> Fetching profile for user 123...
# -> Fetching orders for user 123...
# Report for Alice: Total spent: $150
```
### Inheritable Weaves
You can define reusable, overridable workflows by inheriting from `wove.Weave`.
```python
# In reports.py
from wove import Weave

class StandardReport(Weave):
    @Weave.do(retries=2, timeout=5.0)
    def user_data(self, user_id: int):
        # `user_id` is passed in from the `weave()` call.
        # Wove checks the function's signature at runtime and passes the appropriate data in.
        print(f"Fetching data for user {user_id}...")
        # ... logic to fetch from a database or API ...
        return {"id": user_id, "name": "Standard User"}

    @Weave.do
    def summary(self, user_data: dict):
        return f"Report for {user_data['name']}"
```
To run the reusable `Weave`, pass the class and any required data to the `weave` context manager.
```python
from wove import weave
from .reports import StandardReport

# Any extra keyword arguments you provide to `weave()` are treated as initialization data.
# The initialization data can be consumed by tasks defined in the `Weave` class.
with weave(StandardReport, user_id=123) as w:
    pass

print(w.result.final)
# >> Fetching data for user 123...
# >> Report for Standard User
```
You can also override tasks inline in your `weave` block. It is okay to change the function signature of your override.
```python
from wove import weave
from .reports import StandardReport

# We also pass in `is_admin` because our override needs it.
with weave(StandardReport, user_id=456, is_admin=True) as w:
    # This override has a different signature than StandardReport's version and Wove handles it.
    @w.do(timeout=10.0)
    def user_data(user_id: int, is_admin: bool):
        if is_admin:
            print(f"Fetching data for ADMIN {user_id}...")
            return {"id": user_id, "name": "Admin"}
        # ... regular logic ...
        return {"id": user_id, "name": "Standard User"}

print(w.result.summary)
# >> Fetching data for ADMIN 456...
# >> Report for Admin
```
### Merging External Functions
Wove provides the `merge` function to dynamically map any callable over an iterable. The callable (typically a function) can be defined inside or outside the `weave` block, and can be `async` or not. A copy of the callable will be run concurrently for each item in the iterable. Used with `await`, a list of results will be returned when all instances have completed.
```python
from wove import weave, merge, flatten

def split(string):
    return string.split(" ")

with weave() as w:
    @w.do
    def strings():
        return ["hello world", "foo bar", "baz qux"]
    @w.do
    async def chopped(strings):
        # Async functions can be within non-async weave blocks.
        # `merge` needs an async function so it can be awaited.
        return flatten(await merge(split, strings))

print(w.result.final)
# >> ['hello', 'world', 'foo', 'bar', 'baz', 'qux']
```
### Error Handling
If any task raises an exception, Wove halts execution, cancels all other running tasks, and re-raises the original exception from the `with weave()` block. This ensures predictable state and allows you to use standard `try...except` blocks.
### Debugging & Introspection
Need to see what's going on under the hood?
-   `with weave(debug=True) as w:`: Prints a detailed, color-coded execution plan to the console before running.
-   `w.execution_plan`: After the block, this dictionary contains the full dependency graph and execution tiers.
-   `w.result.timings`: A dictionary mapping each task name to its execution duration in seconds.
### Data-Shaping Helper Functions
Wove provides a set of simple, composable helper functions for common data manipulation patterns.
-   **`flatten(list_of_lists)`**: Converts a 2D iterable into a 1D list.
-   **`fold(a_list, size)`**: Converts a 1D list into N smaller lists of `size` length.
-   **`batch(a_list, count)`**: Converts a 1D list into `count` smaller lists of N length.
-   **`undict(a_dict)`**: Converts a dictionary into a list of `[key, value]` pairs.
-   **`redict(list_of_pairs)`**: Converts a list of key-value pairs back into a dictionary.
-   **`denone(an_iterable)`**: Removes all `None` values from an iterable.

## Background Processing
Wove supports running the entire weave in the background, either in a separate thread or a forked process. This is useful for fire-and-forget tasks where you don't need to wait for the result immediately.

To enable background processing, set `background=True` in the `weave()` call.
-   **Embedded (threaded) mode (default)**: `weave(background=True)` will run the weave in a new background thread.
-   **Forked mode**: `weave(background=True, fork=True)` will run the weave in a new background process. This is useful for CPU-bound tasks that would otherwise block the main event loop.

You can provide an `on_done` callback to be executed when the background weave is complete. The callback will receive the `WoveResult` object as its only argument.
```python
import time
from wove import weave

def my_callback(result):
    print(f"Background weave complete! Final result: {result.final}")

# Run in a background thread
with weave(background=True, on_done=my_callback) as w:
    @w.do
    def long_running_task():
        time.sleep(2)
        return "Done!"

print("Main program continues to run...")
# After 2 seconds, the callback will be executed.
```

## Benchmarks
Wove has low overhead and internally uses `asyncio`, so its performance is comparable to using `threading` or `asyncio` directly. The benchmark script below is available in the `/examples` directory.
```bash
$ python examples/benchmark.py
 Starting performance benchmarks...
Number of tasks: 200
CPU load iterations per task: 100000
I/O sleep duration per task: 0.1s
===================================
--- Running Threading Benchmark ---
Threading total time: 1.6910 seconds
-----------------------------------
--- Running Asyncio Benchmark ---
Asyncio total time: 1.4953 seconds
-----------------------------------
--- Running Wove Benchmark ---
Wove timing details:
  - planning: 0.0002s
  - tier_1_execution: 1.6428s
  - tier_1_post_execution: 0.0000s
  - tier_1_pre_execution: 0.0007s
  - wove_task: 0.1324s
Wove total time: 1.6585 seconds
-----------------------------------
--- Running Wove Async Benchmark ---
Wove Async timing details:
  - planning: 0.0001s
  - tier_1_execution: 1.6366s
  - tier_1_post_execution: 0.0000s
  - tier_1_pre_execution: 0.0006s
  - wove_async_task: 1.5063s
Wove Async total time: 1.6414 seconds
-----------------------------------
Benchmarks finished.
```
## More Examples
You can find a variety of usecase examples in the `examples/` directory including for machine learning and web development.
