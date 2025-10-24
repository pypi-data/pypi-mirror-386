# Created on 26/07/2025
# Author: Frank Vega

import argparse
from . import utils
from . import app

def approximate_solutions(inputDirectory, verbose=False, log=False, count=False, bruteForce=False, approximation=False):
    """Finds the approximate vertex cover for several instances.

    Args:
        inputDirectory: Input directory path.
        verbose: Enable verbose output.
        log: Enable file logging.
        count: Measure the size of the vertex cover.
        bruteForce: Enable brute force approach.
        approximation: Enable an approximate approach within a ratio of at most 2.
    """
    
    file_names = utils.get_file_names(inputDirectory)

    if file_names:
        for file_name in file_names:
            inputFile = f"{inputDirectory}/{file_name}"
            print(f"Test: {inputDirectory}/{file_name}")
            app.approximate_solution(inputFile, verbose, log, count, bruteForce, approximation)


def main():
    
    # Define the parameters
    helper = argparse.ArgumentParser(prog="batch_pray", description="Compute the Approximate Vertex Cover for all undirected graphs encoded in DIMACS format and stored in a directory.")
    helper.add_argument('-i', '--inputDirectory', type=str, help='Input directory path', required=True)
    helper.add_argument('-a', '--approximation', action='store_true', help='enable comparison with a polynomial-time approximation approach within a factor of at most 2')
    helper.add_argument('-b', '--bruteForce', action='store_true', help='enable comparison with the exponential-time brute-force approach')
    helper.add_argument('-c', '--count', action='store_true', help='calculate the size of the vertex cover')
    helper.add_argument('-v', '--verbose', action='store_true', help='anable verbose output')
    helper.add_argument('-l', '--log', action='store_true', help='enable file logging')
    helper.add_argument('--version', action='version', version='%(prog)s 0.0.2')

    
    # Initialize the parameters
    args = helper.parse_args()
    approximate_solutions(args.inputDirectory, 
               verbose=args.verbose, 
               log=args.log,
               count=args.count,
               bruteForce=args.bruteForce,
               approximation=args.approximation)


if __name__ == "__main__":
  main()      