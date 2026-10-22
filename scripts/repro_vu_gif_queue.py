#!/usr/bin/env python3
"""Original VU integration through real GIF transfer and render-queue storage.

No game input or renderer. Run under the shared serial allocation, with a new
private output directory. Supplied archives remain read-only.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess

from repro_vu_checkpoint import GENERATOR, ROOT
from repro_vu_chain import OUTCOMES

DRIVER = r'''
#include "runtime/src/vu_micro.cpp"
#include "runtime/src/gs/queue.hpp"
#include <iostream>

void vu1_0000000000040001(ps2::Vu0Regs&,std::uint8_t*);
void vu1_0000000000040002(ps2::Vu0Regs&,std::uint8_t*);
#define CHECK(x) do { if (!(x)) { std::cerr << "failed line " << __LINE__ << ": " << #x << '\n'; return 1; } } while (0)

// Overwrite the stack region formerly used by xgkick's temporary buffer too.
__attribute__((noinline)) unsigned scrub_stack() {
    volatile std::uint8_t scratch[32768];
    for (unsigned i=0;i<sizeof scratch;++i) scratch[i]=0xCC;
    return scratch[0];
}

int main(int argc,char** argv) {
    using namespace ps2;
    CHECK(argc==4);
    CHECK(std::ifstream(argv[1],std::ios::binary).read((char*)g_vu1_code,16384));
    const std::string mode=argv[2],out=argv[3];
    const bool longer=mode=="plain-long" || mode=="budget";
    vu::reset();vu::code_changed(1);
    auto key=[](unsigned pc) { return vu::program_key(g_vu1_code,vu::reachable(g_vu1_code,16383,pc),pc); };
    vu::Program programs[]={{key(0),vu1_0000000000040001},{key(0x80),vu1_0000000000040002}};
    vu::register_programs(programs,2);
    std::memset(g_vu1_mem,0,16384);
    auto& r=vu::regs(1);
    r.vi[9]=16;r.vi[10]=longer?10000:2;r.vi[13]=1;r.q=0x3F800000;
    r.vf[1].w[0]=0x3F800000;r.vf[2].w[0]=0x40000000;
    const std::uint64_t tag=0x8000,one=0x1111,two=0x2222;
    std::memcpy(g_vu1_mem,&tag,8);std::memcpy(g_vu1_mem+8,&one,8);
    std::memcpy(g_vu1_mem+16,&tag,8);std::memcpy(g_vu1_mem+24,&two,8);

    // Exercise the production producer routing. No consumer runs until after
    // dispatch and memory/stack poisoning, so deferred pointers cannot pass.
    gs::queue::render().start(4096);
    gs::queue::role()=gs::queue::Role::Vu;
    CHECK(gs::queue::active() && &gs::queue::outbox()==&gs::queue::render());
    std::vector<std::uint8_t> packets;
    vu::g_check_packets=&packets;vu::g_reference_dry=false;
    auto dump=[&](const char* suffix,const void* data,std::size_t bytes) {
        std::ofstream file(out+suffix,std::ios::binary);
        if (!file || !file.write(static_cast<const char*>(data),bytes)) throw std::runtime_error("output failure");
    };
    {
        vuops::FlagDispatch flags(r);
        vuops::g_dispatch_flags.t=73;
        vuops::g_dispatch_flags.q_pending=true;
        vuops::g_dispatch_flags.q_ready=100;
        vuops::g_dispatch_flags.q_value=0x3F400000;
        vu::run_chain(0);
        CHECK(vuops::g_dispatch_flags_active && !vu::g_reference_dry && vu::g_check_packets==&packets);
        CHECK(!vu::g_capture && !vu::g_fast_checkpoint && !vu::g_chaining && !vu::g_check_tail);
        CHECK(r.vi[10]==0 && r.q==0x3F000000 && r.vf[5].w[0]==0x3F000000 && r.tpc==0xF8);
        CHECK(packets.size()==40);
        dump("-regs.bin",&r,sizeof r);dump("-mem.bin",g_vu1_mem,16384);
        dump("-packets.bin",packets.data(),packets.size());
        const auto& pipe=vuops::g_dispatch_flags;
        std::ofstream semantic(out+"-pipe.txt");
        semantic<<pipe.t<<' '<<pipe.mh<<' '<<pipe.ch<<' '<<pipe.q_pending<<' '<<pipe.q_value<<' '<<pipe.q_ready<<'\n';
        for(unsigned i=0;i<8;++i) semantic<<pipe.mac_ts[i]<<' '<<pipe.mac_v[i]<<' '<<pipe.status_v[i]<<' '<<pipe.clip_ts[i]<<' '<<pipe.clip_v[i]<<'\n';
        semantic.close();CHECK(semantic);
    }
    CHECK(!vuops::g_dispatch_flags_active);
    std::memset(g_vu1_mem,0xEE,16384);CHECK(scrub_stack()==0xCC);
    // Discard capture storage as well; the real queue must own its bytes.
    std::fill(packets.begin(),packets.end(),0xDD);std::vector<std::uint8_t>().swap(packets);
    vu::g_check_packets=nullptr;
    std::vector<std::uint8_t> queued;
    gs::queue::Header header;const std::uint8_t* payload=nullptr;
    for(unsigned index=0;index<2;++index) {
        CHECK(gs::queue::render().peek(header,payload));
        CHECK(header.type==gs::queue::kGif && header.arg0==1 && header.arg1==1 && header.bytes==16);
        const std::uint64_t expected[2]={tag,index?two:one};
        CHECK(std::memcmp(payload,expected,16)==0);
        queued.insert(queued.end(),payload,payload+header.bytes);
        gs::queue::render().pop(header);
    }
    CHECK(!gs::queue::render().peek(header,payload));
    dump("-queue.bin",queued.data(),queued.size());
    std::cout<<"real GIF queue: two exact ordered owned packets, final Q/state assertions passed\n";
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--wgpu', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'local'):
        parser.error('output must be a new private local directory')
    output.mkdir(parents=True)
    (output/'tmp').mkdir()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    env = {k: v for k, v in os.environ.items() if not k.startswith('PS2_')}
    env['TMPDIR'] = str(output/'tmp')
    inputs = [Path(__file__), ROOT/'scripts/repro_vu_checkpoint.py', ROOT/'scripts/repro_vu_chain.py',
              ROOT/'runtime/src/vu_micro.cpp', ROOT/'runtime/src/vu_checkpoint.hpp',
              ROOT/'runtime/src/gs/gif.cpp', ROOT/'runtime/src/gs/queue.cpp',
              ROOT/'runtime/include/ps2/vu_ops.hpp', ROOT/'recomp/vurecomp.cpp',
              args.runtime.resolve(), args.wgpu.resolve()]
    (output/'inputs.json').write_text(json.dumps({str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                               for p in inputs}, indent=2)+'\n')
    commands = []

    def run(argv, cwd=ROOT, settings=env, log=None):
        argv = list(map(str, argv))
        commands.append({'argv': argv, 'cwd': str(cwd),
                         'diagnostic_environment': {k: v for k, v in settings.items() if k.startswith('PS2_')}})
        (output/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
        return subprocess.run(argv, cwd=cwd, env=settings, check=True, timeout=900,
                              stdout=log, stderr=subprocess.STDOUT)

    (output/'generator.cpp').write_text(GENERATOR)
    (output/'driver.cpp').write_text(DRIVER)
    run(['clang++', '-std=c++20', '-O2', '-I.', '-Iruntime/include', output/'generator.cpp', '-o', output/'generator'])
    run([output/'generator', output])
    run(['clang++', '-std=c++20', '-O2', '-I.', '-Iruntime/include', '-Iruntime/src',
         output/'driver.cpp', output/'native.cpp', 'runtime/src/gs/gif.cpp', 'runtime/src/gs/queue.cpp',
         args.runtime.resolve(), args.wgpu.resolve(), '-framework', 'Metal', '-framework', 'QuartzCore',
         '-framework', 'Foundation', '-framework', 'CoreFoundation', '-framework', 'IOKit',
         '-framework', 'IOSurface', '-lobjc', '-o', output/'native'])
    results = {}
    for mode in ('plain-short', 'plain-long', 'complete', 'budget'):
        case = output/mode
        case.mkdir()
        settings = dict(env)
        if not mode.startswith('plain'):
            settings['PS2_VU_CHECK'] = 'all'
        with (case/'log.txt').open('w') as log:
            run([output/'native', output/'code.bin', mode, case/'final'], cwd=case, settings=settings, log=log)
        text = (case/'log.txt').read_text()
        if not mode.startswith('plain'):
            records = OUTCOMES.findall(text)
            assert len(records) == 1, (mode, text)
            counts = list(map(int, records[0]))
            expected = [1, 1, 0, 0, 0, 0, 1, 2] if mode == 'complete' else [1, 0, 0, 1, 0, 1808, 32, 8192]
            assert counts == expected, (mode, counts)
            results[mode] = counts
    for mode, plain in (('complete', 'plain-short'), ('budget', 'plain-long')):
        for suffix in ('regs.bin', 'mem.bin', 'packets.bin', 'pipe.txt', 'queue.bin'):
            assert (output/mode/('final-'+suffix)).read_bytes() == (output/plain/('final-'+suffix)).read_bytes(), (mode, suffix)
    (output/'results.json').write_text(json.dumps({'outcomes': results, 'cases_passed': 4,
                                                'real_gif_queue': True, 'packets_per_case': 2}, indent=2)+'\n')
    print('Real GIF queue: four cases passed; exact state, pipe, packet ownership and ordering')


if __name__ == '__main__':
    main()
