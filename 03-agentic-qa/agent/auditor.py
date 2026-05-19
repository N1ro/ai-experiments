import os
from tree_sitter_languages import get_language, get_parser

class TreeSitterAuditor:
    def __init__(self, language='python'):
        self.language = get_language(language)
        self.parser = get_parser(language)

    def extract_definitions(self, file_path):
        """Extract all function and class method definitions."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = self.parser.parse(bytes(content, 'utf-8'))
        
        # Tree-sitter query to find function definitions
        query = self.language.query("""
            (function_definition
                name: (identifier) @func_name)
        """)
        
        definitions = []
        captures = query.captures(tree.root_node)
        for node, tag in captures:
            if tag == 'func_name':
                definitions.append({
                    "name": node.text.decode('utf-8'),
                    "file": file_path,
                    "line": node.start_point[0] + 1,
                    "type": "function"
                })
        
        return definitions

    def extract_calls(self, file_path):
        """Extract all function calls from a file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = self.parser.parse(bytes(content, 'utf-8'))
        
        # Query to find call expressions
        query = self.language.query("""
            (call
                function: [
                    (identifier) @call_name
                    (attribute attribute: (identifier) @call_name)
                ])
        """)
        
        calls = set()
        captures = query.captures(tree.root_node)
        for node, tag in captures:
            if tag == 'call_name':
                calls.add(node.text.decode('utf-8'))
        
        return calls

    def find_gaps(self, repo_path):
        """Cross-reference definitions vs calls to find untested code."""
        all_definitions = []
        all_calls = set()
        
        source_files = []
        test_files = []
        
        skip = {".git", "__pycache__", ".pytest_cache", "venv", ".venv", "node_modules"}
        
        for root, dirs, filenames in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in skip]
            for f in filenames:
                if f.endswith(".py"):
                    full_path = os.path.join(root, f)
                    if "test" in f or "/tests/" in full_path:
                        test_files.append(full_path)
                    else:
                        source_files.append(full_path)
        
        # 1. Map all definitions in source
        for f in source_files:
            all_definitions.extend(self.extract_definitions(f))
        
        # 2. Map all calls in tests
        for f in test_files:
            all_calls.update(self.extract_calls(f))
            
        # 3. Identify the gaps
        gaps = []
        for defn in all_definitions:
            if defn['name'] not in all_calls:
                gaps.append(defn)
                
        return gaps
