#!/usr/bin/env python3
"""Code file for testing Copy-MarkdownContent with source code."""

def process_markdown(content):
    """Process and format markdown content."""
    lines = content.split('\n')
    formatted = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#'):
            formatted.append(stripped)
        elif stripped:
            formatted.append(f'  {stripped}')

    return '\n'.join(formatted)


class TestCase:
    """Test case for validating script output."""

    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.results = []

    def add_result(self, status, message):
        """Record a test result."""
        self.results.append({
            'status': status,
            'message': message
        })

    def report(self):
        """Generate test report."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r['status'] == 'pass')
        return f"{self.name}: {passed}/{total} tests passed"


if __name__ == '__main__':
    test = TestCase('markdown_test', 'Test markdown processing')
    test.add_result('pass', 'Processing works correctly')
    print(test.report())
