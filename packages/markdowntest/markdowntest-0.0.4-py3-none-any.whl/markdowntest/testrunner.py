'''
modeled after https://github.com/gradescope/gradescope-utils/blob/master/gradescope_utils/autograder_utils/json_test_runner.py
'''

from __future__ import print_function
from datetime import datetime
from unittest import result, TextTestRunner


class MarkdownTestResult(result.TestResult):
    def __init__(self, stream, descriptions, verbosity):
        
        super(MarkdownTestResult, self) \
            .__init__(stream, descriptions, verbosity)

        self.stream = stream
        self.descriptions = descriptions
        self.verbosity = verbosity

        self.results = []

    def startTestRun(self):

        self.startTime = datetime.now().strftime('%H:%M:%S on %a, %d %b %Y')

        self.stream.write(
            f"\n\nTests started at {self.startTime}."
        )

        super(MarkdownTestResult, self).startTestRun()

    def getDescription(self, test):
        doc_first_line = test.shortDescription()
        if self.descriptions and doc_first_line:
            return doc_first_line
        else:
            return str(test)
    
    def getTags(self, test):
        return getattr(getattr(test, test._testMethodName), '__tags__', None)

    def getWeight(self, test):
        return getattr(getattr(test, test._testMethodName), '__weight__', None)
    
    def getNumber(self, test):
        return getattr(getattr(test, test._testMethodName), '__number__', None)

    def getVisibility(self, test):
        return getattr(getattr(test, test._testMethodName), '__visibility__', None)

    def startTest(self, test):
        super(MarkdownTestResult, self).startTest(test)

    def getOutput(self):
        if self.buffer:
            out = self._stdout_buffer.getvalue()
        else:
            out = None
        return out

    def buildResult(self, test, err=None):
        failed = err is not None
        weight = self.getWeight(test)
        tags = self.getTags(test)
        number = self.getNumber(test)
        # visibility = self.getVisibility(test)
        output = self.getOutput()

        if err:
            error = {
                "name": err[0].__name__,
                "details": err[1]
            }
        else:
            error = None
                    
        result = {
            "name": test._testMethodName,
            "description": self.getDescription(test),
            "number": "-" if number is None else number,
            "weight": 1 if weight is None else weight,
            "status": "failed" if failed else "passed",
            "error": error,
            "tags": [] if tags is None else tags,
            "output": "" if output is None else output
        }

        return result

    def processResult(self, test, err=None):
        self.results.append(self.buildResult(test, err))

    def addSuccess(self, test):
        super(MarkdownTestResult, self).addSuccess(test)
        self.processResult(test)

    def addError(self, test, err):
        super(MarkdownTestResult, self).addError(test, err)
        self.processResult(test, err)

    def addFailure(self, test, err):
        super(MarkdownTestResult, self).addFailure(test, err)
        self.processResult(test, err)

    def writeOverview(self):
        passed = [r['weight'] for r in self.results if r['status'] == 'passed']
        failed = [r['weight'] for r in self.results if r['status'] == 'failed']

        self.stream.write(f"\n\nStatus | Count | Weight")
        self.stream.write(f"\n--- | --- | ---")
        self.stream.write(f"\nPassed | {len(passed)} | {sum(passed)}")
        self.stream.write(f"\nFailed | {len(failed)} | {sum(failed)}")

        # optional weighted score
        # perc_passed = round(sum(passed) / (sum(passed) + sum(failed)), 4)
        # perc_passed *= 100
        # self.stream.write(f"\n\nWeighted Score = {perc_passed}%")

    def writeResult(self, result):
        self.stream.write(f"\n\n## {result['number']}) ")
        self.stream.write(f"{result['name']} -- ")
        self.stream.write(f"{result['status']}\n")
        self.stream.write(f"**Description:**\n{result['description']}")
        self.stream.write(f" (weight = {result['weight']})\n")
        self.stream.write("\n**Output:**\n```bash\n")
        self.stream.write(f"{result['output']}\n```\n")

        if result['error']:
            self.stream.write("<details>\n<summary>")
            self.stream.write(f"{result['error']['name']}")
            self.stream.write("</summary>\n\n")
            self.stream.write(f"```python\n{result['error']['details']}\n")
            self.stream.write("```\n\n</details>")

    def stopTestRun(self):
        
        self.writeOverview()
        results = sorted(self.results, key=lambda s: s['number'])

        for result in results:
            self.writeResult(result)

        self.stopTime = datetime.now().strftime('%H:%M:%S on %a, %d %b %Y')
        self.stream.write(f"\n\n<br>Tests stopped at {self.stopTime}.")
        
        super(MarkdownTestResult, self).stopTestRun()

class MarkdownTestRunner(TextTestRunner):
    def __init__(self, filestream, descriptions=True, verbosity=2):

        super(MarkdownTestRunner, self).__init__()
        
        self.filestream = filestream    # not to overwrite self.stream?
        self.descriptions = descriptions
        self.verbosity = verbosity

    def _makeResult(self):
        return MarkdownTestResult(
            self.filestream, self.descriptions, self.verbosity)
