import os
import re

repo_dir = r'd:\PROJECT\LOJINEXT\app\database\repositories'
files = [f for f in os.listdir(repo_dir) if f.endswith('.py')]
files.append(r'..\base_repository.py') # Also check base

for f in files:
    filepath = os.path.join(repo_dir, f)
    with open(filepath, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if 'async with self._get_session() as session:' in line:
            # Get the exact indentation
            indent = line[:line.find('async with')]
            new_lines.append(f'{indent}session = self.session\n')
            
            # Now we must un-indent the block
            i += 1
            block_indent = indent + '    '
            while i < len(lines):
                next_line = lines[i]
                if next_line.strip() == '':
                    new_lines.append(next_line)
                    i += 1
                elif next_line.startswith(block_indent):
                    new_lines.append(indent + next_line[len(block_indent):])
                    i += 1
                else:
                    # End of block
                    break
        else:
            new_lines.append(line)
            i += 1
            
    with open(filepath, 'w', encoding='utf-8') as file:
        file.writelines(new_lines)
