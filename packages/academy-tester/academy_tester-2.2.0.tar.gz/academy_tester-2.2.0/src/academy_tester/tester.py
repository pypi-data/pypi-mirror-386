import unittest
import subprocess
from dataclasses import dataclass
from typing import Optional, Union, Iterable
import os, platform
import ast
from typing import Type, Iterator, List


@dataclass
class RunResult:
    output: str
    error: Optional[str] = None

class OutputTester():
    def __init__(self, testcase : unittest.TestCase, filename : str = "task.py"):
        self.cwd = os.getcwd()
        self.filename : str = filename
        self.testcase = testcase

    def test_output(self, output_requirements : Union[str, list[str]], input : Iterable[str] = [], message_addition : str = "") -> None:
        """
            Runs a python file with a set of inputs, and checks if the output has all the required strings.

        Args:
            output_requirements Union[str, list[str]]: The expected output or outputs
            input Iterable[str]: 
        """

        # retrieve output using formatted input
        result = self._run_file(self.filename, input)
        #print(f"result: {result}")

        output_requirements = [output_requirements] if isinstance(output_requirements, str) else output_requirements

        if result.error:
            self.testcase.fail(result.output)
        else:
            for req in output_requirements:
                if not req in result.output:
                    #print(f"output:{result.output}")
                    self.testcase.fail(f"{req} was not found in output for the input: {input}")

    


    def test_count(self, expected_output : str, required_count : int, input : Iterable[str] = []) -> None:
        """
            Counts occurrences of an expected output with a specific input. 
            Only counts one occurence for each line
            Args:
                input (Iterable[str]): User input for the script
                expected_output (str): what to check for in output
        """

        result = self._run_file(self.filename, input)
        
        if not result.error:
            count = 0
            for line in result.output.splitlines():
                if expected_output in line:
                    count += 1

            if count < required_count:
                self.testcase.fail(f"Expected {required_count} instances of {expected_output} in output, got {count}")
            
    
    def test_line_count(self, input : Iterable[str] = []) -> int:
        """
        """
        result : RunResult = self._run_file(self.filename, input)

        return len(result.output.splitlines())

    def _run_file(self, filename : str, input : Iterable[str], timeout : float = 5) -> RunResult:
        """
        Runs a python file and performs any requested inputs
        Essentially a wrapper around subprocess.run

        Args: 
            filename (str): The name of the file to test. Defaults to "task.py"
            input (str): Text inputs for the file. Empty by default
            timeout (float): time allocated for the script to run before it terminates

        Returns:
            Optional[str]: The output from running the file, or None if Exception
        """

        # Get the python version for the platform
        plat = platform.system().lower()
        python_version = "python" if plat == "windows" else "python3"

        # get directory of the requested file
        directory = os.path.join(self.cwd, filename)

        process = subprocess.Popen(
                [python_version, directory],  # Command to run the script
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,  # Capture standard output
                stderr=subprocess.PIPE,  # Capture standard error (optional)
                text=True,  # Ensure output is returned as a string
                encoding="utf-8",      # Ensure UTF-8 encoding
                errors="replace"   # Handle any bad characters gracefully  
            )
        
        
        input = [input] if isinstance(input, str) else input

        

        # Run file with requested inputs and test output
        try:
            # Wait for the process to complete and capture the output
            stdout, stderr = process.communicate(input = "\n".join(input), timeout = timeout)

        except subprocess.TimeoutExpired:
            # Handle the case where the script hangs due to insufficient input
            process.kill()  # Terminate the hanging process
            return RunResult(output = "", error="Script Timed Out")
        

        return RunResult(output = stdout, error = stderr)
    

class ContentTester():
    def __init__(self, testcase : unittest.TestCase, filename : str = "task.py") -> None:
        self.testcase : unittest.TestCase = testcase
        self.filename : str = filename
        self.tree : ast.Module = self._parse()


    def check_tokens(self, token : Union[Type[ast.operator], Type[ast.expr_context], Type[ast.boolop], Type[ast.unaryop], Type[ast.stmt]]) -> int:
        """
        Returns a count for a specific token type in the program

        Args:
            token: an ast token

        Returns:
            count (int): The number of these tokens found in the program
        """
        count = 0
        for node in ast.walk(self.tree):
            if isinstance(node, token):
                count += 1

        return count

    @property
    def get_variables(self) -> dict[str, object]:
        vars : dict[str, object] = {}

        for node in ast.walk(self.tree):
            match node:
                case ast.Assign(
                    targets=[ast.Name(id=name)],
                    value=value
                ):
                    vars[name] = value
        
        return vars

    @property
    def get_lists(self) -> dict[str, list]:
        """
        Returns a dictionary of list names as keys, and a list of the values within as the values
        """
        l : dict[str, list] = {}

        for name, var in self.get_variables.items():
            if isinstance(var, ast.List):
                l[name] = [item.value for item in var.elts if isinstance(item, ast.Constant)]
        
        return l
    
    def get_functions(self) -> List[str]:
        l : List[str] = []

        for node in ast.walk(self.tree):
            match node:
                case ast.Name(
                    id=captured_id,
                    ctx=ast.Load()
                ):
                    l.append(captured_id)

        return l
    
    def get_user_defined_functions(self) -> dict[str, List[str]]:
        l : dict[str, List[str]] = {}

        for node in ast.walk(self.tree):
            match node:
                case ast.FunctionDef(
                    name=name,
                    args = arguments
                ):
                    match arguments:
                        case ast.arguments(
                            args=arg_list
                        ):
                            l[name] = [a.arg for a in arg_list]

        return l

    def get_function_count(self, function_id : str) -> int:
        """
        Gets all the functions with a provided name within the file and returns a count
        
        Args:
            function_id : str = The name of the function you wish to search for

        Returns:
            count : int = How many functions were found in
        """
        count : int = 0

        for node in ast.walk(self.tree):
            match node:
                case ast.Name(
                    id=captured_id,
                    ctx=ast.Load()
                ):
                    if captured_id == function_id:
                        count += 1
        return count


            
    def get_attribute_count(self, attribute_id : str) -> int:
        count = 0
        for node in ast.walk(self.tree):
            match node:
                case ast.Attribute(
                    attr = captured_attr
                ):
                    if captured_attr == attribute_id:
                        count += 1
        return count



    def _parse(self) -> ast.Module:
        """
        Returns an iterator containing all the nodes in the tree
        """

        tree = ast.parse(self.get_file_contents)

        return tree

    @property
    def get_file_contents(self) -> str:
        """
        Returns the contents of the file as a string
        """
        directory = os.path.join(os.getcwd(), self.filename)

        with open(directory, 'r', encoding='utf-8') as f:
            return f.read()