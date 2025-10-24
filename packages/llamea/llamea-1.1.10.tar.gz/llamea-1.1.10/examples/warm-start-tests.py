# This is a test for warm start, that tests both the functionalities of warm-starting:
#   Warm starting from Pickled file.
#   Cold starting new instance, and running with latest individual from specified run in archive_path.

import os
import re
import pickle

import numpy as np
from ioh import get_problem, logger

from llamea import Dummy_LLM, LLaMEA, ExperimentLogger
from misc import OverBudgetException, aoc_logger, correct_aoc

if __name__ == "__main__":
    # Execution code starts here
    api_key = os.getenv("GEMINI_API_KEY")
    ai_model = "gemini-1.5-flash"
    experiment_name = "pop1-5"
    llm = Dummy_LLM()

    # We define the evaluation function that executes the generated algorithm (solution.code) on the BBOB test suite.
    # It should set the scores and feedback of the solution based on the performance metric, in this case we use mean AOCC.
    def evaluateBBOB(solution, explogger=None):
        auc_mean = 0
        auc_std = 0

        code = solution.code
        algorithm_name = solution.name
        exec(code, globals())

        error = ""

        aucs = []

        algorithm = None
        for dim in [5]:
            budget = 2000 * dim
            l2 = aoc_logger(budget, upper=1e2, triggers=[logger.trigger.ALWAYS])
            for fid in np.arange(1, 25):
                for iid in [1, 2, 3]:  # , 4, 5]
                    problem = get_problem(fid, iid, dim)
                    problem.attach_logger(l2)

                    for rep in range(3):
                        np.random.seed(rep)
                        try:
                            algorithm = globals()[algorithm_name](
                                budget=budget, dim=dim
                            )
                            algorithm(problem)
                        except OverBudgetException:
                            pass

                        auc = correct_aoc(problem, l2, budget)
                        aucs.append(auc)
                        l2.reset(problem)
                        problem.reset()
        auc_mean = np.mean(aucs)
        auc_std = np.std(aucs)

        feedback = f"The algorithm {algorithm_name} got an average Area over the convergence curve (AOCC, 1.0 is the best) score of {auc_mean:0.2f} with standard deviation {auc_std:0.2f}."

        print(algorithm_name, algorithm, auc_mean, auc_std)
        solution.add_metadata("aucs", aucs)
        solution.set_scores(auc_mean, feedback)

        return solution

    # The task prompt describes the problem to be solved by the LLaMEA algorithm.
    task_prompt = """
    The optimization algorithm should handle a wide range of tasks, which is evaluated on the BBOB test suite of 24 noiseless functions. Your task is to write the optimization algorithm in Python code. The code should contain an `__init__(self, budget, dim)` function and the function `def __call__(self, func)`, which should optimize the black box function `func` using `self.budget` function evaluations.
    The func() can only be called as many times as the budget allows, not more. Each of the optimization functions has a search space between -5.0 (lower bound) and 5.0 (upper bound). The dimensionality can be varied.
    Give an excellent and novel heuristic algorithm to solve this task and also give it a one-line description with the main idea.
    """

    for experiment_i in [1]:
        # A 1+1 strategy
        es = LLaMEA(
            evaluateBBOB,
            n_parents=1,
            n_offspring=1,
            llm=llm,
            task_prompt=task_prompt,
            experiment_name=experiment_name,
            elitism=True,
            HPO=False,
            budget=400,
        )

        """Simple run first.
        Hit ^C, before ending execution, and end program prematurely.
        Then comment following line"""
        es.run()

        """Declare path to warm start from here, the path where the above quitted program was logging."""
        path_to_archive = os.getcwd() + "/exp-08-22_110651-LLaMEA-DUMMY-pop1-5"
        print(f"Dir name = {path_to_archive}")

        """
        Use `warm_start` class function, which returns the qutting instance of previous object if success, else
        return None.
        """

        try:
            es2 = LLaMEA.warm_start(path_to_archive)
            for key, value in es2.__dict__.items():
                print(key, ":", value)
            es2.run()
        except Exception as e:
            print(f"Error un-arciving. {e.__repr__()}")
