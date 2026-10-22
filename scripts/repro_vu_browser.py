#!/usr/bin/env python3
"""Build and run the original GIF queue fixture in a fresh browser Wasm worker.

Run under the shared serial allocation. No game data or personal browser profile.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from repro_vu_checkpoint import ROOT, GENERATOR
from repro_vu_gif_queue import DRIVER
from repro_vu_chain import OUTCOMES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--empp', type=Path, required=True)
    parser.add_argument('--playwright', type=Path, required=True)
    parser.add_argument('--native-reference', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'local'):
        parser.error('output must be a new private local directory')
    output.mkdir(parents=True)
    (output/'tmp').mkdir()
    env = {k: v for k, v in os.environ.items() if not k.startswith('PS2_')}
    env['TMPDIR'] = str(output/'tmp')
    commands = []

    def run(argv):
        commands.append(list(map(str, argv)))
        (output/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
        subprocess.run(commands[-1], cwd=ROOT, env=env, check=True, timeout=900)

    # The original native evidence must describe the same execution sources.
    native = args.native_reference.resolve()
    sealed = json.loads((native/'inputs.json').read_text())
    for name in ('runtime/src/vu_micro.cpp', 'runtime/src/vu_checkpoint.hpp',
                 'runtime/include/ps2/vu_ops.hpp', 'runtime/src/gs/gif.cpp',
                 'runtime/src/gs/queue.cpp', 'recomp/vurecomp.cpp',
                 'scripts/repro_vu_checkpoint.py', 'scripts/repro_vu_gif_queue.py'):
        p = ROOT/name
        assert hashlib.sha256(p.read_bytes()).hexdigest() == sealed[str(p)], name
    inputs = [Path(__file__), ROOT/'scripts/repro_vu_browser.cjs', ROOT/'CMakeLists.txt',
              ROOT/'scripts/repro_vu_gif_queue.py', ROOT/'scripts/repro_vu_checkpoint.py']
    (output/'inputs.json').write_text(json.dumps({str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                               for p in inputs}, indent=2)+'\n')
    (output/'native-inputs.json').write_text(json.dumps(sealed, indent=2)+'\n')
    (output/'generator.cpp').write_text(GENERATOR)
    run(['clang++', '-std=c++20', '-O2', '-I.', '-Iruntime/include', output/'generator.cpp', '-o', output/'generator'])
    run([output/'generator', output])
    assert (output/'code.bin').read_bytes() == (native/'code.bin').read_bytes()
    assert (output/'native.cpp').read_bytes() == (native/'native.cpp').read_bytes()
    driver = '#include <emscripten/threading.h>\n'+DRIVER
    driver = driver.replace('CHECK(argc==4);', 'CHECK(argc==4);\n    CHECK(!emscripten_is_main_browser_thread() && !emscripten_is_main_runtime_thread());\n    std::cout<<"[fixture-worker] pthread confirmed\\n";')
    (output/'driver.cpp').write_text(driver)
    project = output/'project'
    project.mkdir()
    # The repository's shader-generation commands use CMAKE_SOURCE_DIR.
    # Supply read-only source links in this private top-level fixture project.
    (project/'cmake').symlink_to(ROOT/'cmake', target_is_directory=True)
    (project/'runtime').symlink_to(ROOT/'runtime', target_is_directory=True)
    (project/'CMakeLists.txt').write_text(f'''cmake_minimum_required(VERSION 3.20)
project(vu_browser_fixture CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(PS2_GENERATED "" CACHE PATH "" FORCE)
add_subdirectory("{ROOT}" runtime)
add_executable(vu_worker "{output}/driver.cpp" "{output}/native.cpp")
target_include_directories(vu_worker PRIVATE "{ROOT}" "{ROOT}/runtime/src")
target_link_libraries(vu_worker PRIVATE ps2runtime)
target_compile_options(vu_worker PRIVATE -msimd128 -mtail-call -fwasm-exceptions -sWASM_LEGACY_EXCEPTIONS=0 -pthread)
target_link_options(vu_worker PRIVATE -msimd128 -mtail-call -fwasm-exceptions -pthread
  -sWASM_LEGACY_EXCEPTIONS=0 -sPROXY_TO_PTHREAD=1 -sPTHREAD_POOL_SIZE=1
  -sEXIT_RUNTIME=1 -sFORCE_FILESYSTEM=1 -sSTACK_SIZE=16777216
  -sINITIAL_MEMORY=268435456 -sALLOW_MEMORY_GROWTH=1 -sALLOW_TABLE_GROWTH=1
  "-sENVIRONMENT=web,worker" "-sEXPORTED_RUNTIME_METHODS=FS,ENV,callMain"
  --preload-file "{output}/code.bin@/code.bin")
set_target_properties(vu_worker PROPERTIES SUFFIX ".js")
''')
    toolchain = args.empp.resolve().parent/'cmake/Modules/Platform/Emscripten.cmake'
    run(['cmake', '-S', project, '-B', output/'build', '-DCMAKE_BUILD_TYPE=Release',
         '-DCMAKE_TOOLCHAIN_FILE='+str(toolchain)])
    run(['cmake', '--build', output/'build', '--target', 'vu_worker', '--parallel', '2'])
    run(['node', ROOT/'scripts/repro_vu_browser.cjs', output, args.playwright.resolve()])
    report = json.loads((output/'browser.json').read_text())
    for mode in ('plain-short', 'plain-long', 'complete', 'budget'):
        case = report['cases'][mode]
        assert case.get('exit_code') == 0 and not case['errors'], (mode, case)
        assert '[fixture-worker] pthread confirmed' in case['messages'], mode
        records = OUTCOMES.findall('\n'.join(case['messages']))
        if mode in ('complete', 'budget'):
            expected = [1, 1, 0, 0, 0, 0, 1, 2] if mode == 'complete' else [1, 0, 0, 1, 0, 1808, 32, 8192]
            assert len(records) == 1 and list(map(int, records[0])) == expected, (mode, records)
        for suffix in ('regs.bin', 'mem.bin', 'packets.bin', 'pipe.txt', 'queue.bin'):
            assert (output/mode/('final-'+suffix)).read_bytes() == (native/mode/('final-'+suffix)).read_bytes(), (mode, suffix)
    report['exact_native_outputs'] = True
    (output/'browser.json').write_text(json.dumps(report, indent=2)+'\n')
    print('Browser worker: four cases passed, exact native state/pipe/queue and bounded outcomes')


if __name__ == '__main__':
    main()
