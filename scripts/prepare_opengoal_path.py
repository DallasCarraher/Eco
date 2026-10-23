#!/usr/bin/env python3
"""Prepare private real-source inputs for the bounded IR experiment.

The selected function is copied verbatim from the supplied checkout; adapters
replace current-time's display access and suspend's machine-stack hook explicitly.
No recovered source is stored in Eco's tracked files.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

PRELUDE = '''(deftype time-frame (int64) ())
(define-extern eco-current-time (function time-frame))
(define-extern eco-suspend (function none))
(define-extern eco-load-duration (function time-frame))
(defmacro current-time () `(eco-current-time))
(defmacro time-elapsed? (time duration) `(>= (- (current-time) ,time) ,duration))
(defmacro suspend () `(eco-suspend))
'''


def selected_form(source, prefix):
    start = source.index(prefix)
    depth, quoted, escaped, comment = 0, False, False, False
    for index in range(start, len(source)):
        char = source[index]
        if comment:
            if char == '\n':
                comment = False
            continue
        if quoted:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == ';':
            comment = True
        elif char == '"':
            quoted = True
        elif char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
            if depth == 0:
                return source[start:index+1]
    raise ValueError('unterminated selected form')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--opengoal', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.opengoal.resolve()
    output = args.output.resolve()
    output.mkdir(exist_ok=False, parents=True)
    relative = 'goal_src/jak1/levels/misty/misty-obs.gc'
    function = selected_form((root/relative).read_text(), '(defun actor-wait-for-period ')
    fixture = Path(__file__).resolve().parents[1]/'experiments/opengoal/nested.gc'
    source = PRELUDE+function+'\n'+fixture.read_text()
    (output/'path.gc').write_text(source)
    (output/'duration.dat').write_bytes((3).to_bytes(8, 'little'))
    metadata = dict(upstream_revision=subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip(),
                    upstream_dirty=bool(subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain'], text=True)),
                    source_path=relative, function_sha256=hashlib.sha256(function.encode()).hexdigest(),
                    input_sha256=hashlib.sha256(source.encode()).hexdigest(),
                    adapters=['display clock -> eco-current-time', 'machine stack suspend -> eco-suspend'],
                    original_native_reference_verified=False)
    (output/'inputs.json').write_text(json.dumps(metadata, indent=2)+'\n')
    print(output/'path.gc')


if __name__ == '__main__':
    main()
