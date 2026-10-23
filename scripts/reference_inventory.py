#!/usr/bin/env python3
"""Read-only reference prerequisite inventory; never launches an emulator.

Writes private metadata only to a new directory under local/. No firmware,
disc, settings, executable or image is copied or modified.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8*1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--eco-report', type=Path, required=True)
    parser.add_argument('--iso', type=Path, required=True)
    parser.add_argument('--emulator', type=Path)
    parser.add_argument('--bios', type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'local'):
        parser.error('output must be a new private local directory')
    for file in (args.eco_report, args.iso):
        if not file.is_file():
            parser.error(f'input file missing: {file}')
    output.mkdir(parents=True)
    home = Path.home()
    checked = [Path('/Applications'), home/'Applications', home/'Downloads', home/'Documents',
               home/'Library/Application Support', Path('/opt/homebrew/Caskroom/pcsx2'),
               home/'Documents/PCSX2', home/'.config/PCSX2',
               home/'Library/Application Support/PCSX2']
    candidates = set()
    for directory in checked:
        if directory.is_dir():
            for entry in directory.iterdir():
                if 'pcsx2' in entry.name.lower():
                    candidates.add(str(entry))
    commands = {name: shutil.which(name) for name in ('pcsx2', 'pcsx2-qt', 'PCSX2')}
    candidates.update(value for value in commands.values() if value)
    spotlight = {'available': bool(shutil.which('mdfind')), 'results': [], 'error': None}
    if spotlight['available']:
        try:
            probe = subprocess.run(['mdfind', 'kMDItemFSName == "*PCSX2*"c'],
                                   capture_output=True, text=True, timeout=15, check=True)
            spotlight['results'] = probe.stdout.splitlines()
        except (subprocess.SubprocessError, OSError) as error:
            spotlight['error'] = str(error)
    report = json.loads(args.eco_report.read_text())
    disc_hash = sha(args.iso)
    if disc_hash != report['identity']['iso_sha256']:
        raise RuntimeError('disc identity differs from archived Eco measurement')
    anchors = []
    for case_path in sorted(args.eco_report.parent.glob('*/case.json')):
        case = json.loads(case_path.read_text())
        if case['scenario'] != 'boot-idle' or case['variant'] not in ('cpu-compiled', 'cpu-interpreted'):
            continue
        for frame in (480, 510):
            name = f'frames/frame_{frame:05d}.ppm'
            file = case_path.parent/name
            digest = sha(file)
            if digest != case['frame_hashes'][name]:
                raise RuntimeError(f'archived capture identity changed: {file}')
            anchors.append({'variant': case['variant'], 'frame': frame, 'path': str(file.resolve()),
                            'sha256': digest, 'recorded_hash_verified': True})
    if len(anchors) != 4:
        raise RuntimeError('expected four archived CPU anchor captures')
    emulator = None
    if args.emulator:
        executable = args.emulator.resolve()
        bundle = None
        if executable.suffix.lower() == '.app':
            with (executable/'Contents/Info.plist').open('rb') as stream:
                bundle = plistlib.load(stream)
            executable = executable/'Contents/MacOS'/bundle['CFBundleExecutable']
        emulator = {'executable': str(executable), 'sha256': sha(executable),
                    'bundle_version': bundle.get('CFBundleShortVersionString') if bundle else None,
                    'cli_version_verified': False, 'capture_capabilities_verified': False}
    bios = {'path': str(args.bios.resolve()), 'sha256': sha(args.bios)} if args.bios else None
    data = {'timestamp_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'emulator_launched': False, 'capture_performed': False,
            'checked_locations': {str(p): p.exists() for p in checked},
            'path_commands': commands, 'candidates': sorted(candidates), 'spotlight': spotlight,
            'selected_emulator': emulator, 'selected_bios': bios,
            'missing_selection': [name for name, value in (('emulator', emulator), ('bios', bios)) if not value],
            'iso': {'path': str(args.iso.resolve()), 'sha256': disc_hash, 'recorded_hash_verified': True},
            'eco_source_commit': report['identity']['source_commit'],
            'eco_report': {'path': str(args.eco_report.resolve()), 'sha256': sha(args.eco_report)},
            'anchors': anchors,
            'limitations': ['search is scoped, not an exhaustive filesystem inventory',
                            'candidate presence does not verify emulator usability',
                            'no independent reference image or visual event alignment exists yet']}
    with (output/'inventory.json').open('x') as stream:
        json.dump(data, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    print('Inventory complete; capture not attempted; missing selected prerequisites: '+', '.join(data['missing_selection']))


if __name__ == '__main__':
    main()
