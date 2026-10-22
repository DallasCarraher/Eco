#!/usr/bin/env python3
"""Check a PCSX2 2.8.2 framebuffer-dump configuration without launching it.

This is a configuration gate, not proof that the executable can capture or that
an image is aligned. Output contains private paths and must remain under local/.
"""
import argparse
import configparser
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check(config, private_root):
    errors = []
    gs = 'EmuCore/GS'
    for key in ('DumpGSData', 'SaveFrame'):
        if not config.getboolean(gs, key, fallback=False):
            errors.append(f'{key} must be enabled')
    # PCSX2 2.8.2 GSOptions::LoadSave disables DumpGSData when EITHER is empty,
    # including when the selected renderer uses only the other directory.
    for key in ('HWDumpDirectory', 'SWDumpDirectory'):
        value = config.get(gs, key, fallback='')
        path = Path(value).resolve() if value else None
        if not value or not Path(value).is_absolute():
            errors.append(f'{key} must be an absolute private directory')
        elif not path.is_relative_to(private_root) or not path.is_dir():
            errors.append(f'{key} must exist inside the private root')
    count = config.getint(gs, 'SaveFrameCount', fallback=-1)
    stride = config.getint(gs, 'SaveFrameBy', fallback=0)
    if not 0 < count <= 2400 or not 0 < stride <= count:
        errors.append('frame range must be finite: count 1..2400, stride 1..count')
    if config.getint(gs, 'SaveDrawCount', fallback=0) != -1:
        errors.append('SaveDrawCount must be -1 so draw count does not truncate the frame range')
    if config.getboolean('UI', 'StartPaused', fallback=True):
        errors.append('unattended dump pass must not start paused')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--private-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    private = args.private_root.resolve()
    output = args.output.resolve()
    source = args.config.resolve()
    if (not private.is_relative_to(ROOT/'local') or not source.is_relative_to(private)
            or not output.is_relative_to(private) or output.exists()):
        parser.error('config/output must be private; output must be a new directory')
    config = configparser.ConfigParser(interpolation=None)
    config.optionxform = str
    with source.open() as stream:
        config.read_file(stream)
    try:
        errors = check(config, private)
    except ValueError as error:
        errors = ['invalid configuration value: '+str(error)]
    output.mkdir(parents=True)
    (output/'preflight.json').write_text(json.dumps({
        'config': str(source), 'private_root': str(private), 'errors': errors,
        'configuration_gate_passed': not errors, 'emulator_launched': False,
        'capture_capability_verified': False, 'alignment_verified': False,
    }, indent=2)+'\n')
    print('Configuration gate '+('failed' if errors else 'passed')+'; emulator not launched')
    return 2 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
