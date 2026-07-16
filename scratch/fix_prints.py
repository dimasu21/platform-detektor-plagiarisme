import re
import sys

files = [
    r'd:\projectpribadi\platform-plagiarisme\text_highlighter.py',
    r'd:\projectpribadi\platform-plagiarisme\highlight_visualizer.py',
    r'd:\projectpribadi\platform-plagiarisme\rabin_karp.py',
]

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add logging import if not present
    if 'import logging' not in content:
        # Add after first import line
        content = 'import logging\n' + content
    
    if 'logger = logging.getLogger' not in content:
        # Add logger after imports block
        lines = content.split('\n')
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                insert_idx = i + 1
            elif insert_idx > 0 and line.strip() and not line.startswith('import ') and not line.startswith('from '):
                break
        lines.insert(insert_idx, '')
        lines.insert(insert_idx + 1, 'logger = logging.getLogger(__name__)')
        content = '\n'.join(lines)

    # Replace print( with logger.debug(
    content = content.replace('print(f"', 'logger.debug(f"')
    content = content.replace('print("', 'logger.debug("')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f'Fixed: {filepath}')
