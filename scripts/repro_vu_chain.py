#!/usr/bin/env python3
"""Original production whole-chain outcomes and live-state handoff regression.

Run under the shared serial allocation. No game input, new private output only.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import subprocess
from repro_vu_checkpoint import GENERATOR, ROOT

DRIVER = r'''
#define gif chain_test_gif
#include "runtime/src/vu_micro.cpp"
#undef gif
#include <iostream>
std::vector<std::vector<std::uint8_t>> delivered;
std::vector<std::size_t> capture_sizes;
namespace ps2::chain_test_gif {
void transfer(int path,const std::uint8_t* data,std::uint32_t qwc) {
 if(path!=1)std::abort();
 delivered.emplace_back(data,data+qwc*16);capture_sizes.push_back(vu::g_check_packets ? vu::g_check_packets->size() : 0);
}
}
void vu1_0000000000040001(ps2::Vu0Regs&,std::uint8_t*);
void vu1_0000000000040002(ps2::Vu0Regs&,std::uint8_t*);
// Simulate a compiled fragment which returns a real end after exceeding the
// diagnostic instruction budget. A budget outcome must not restart that end PC.
void atomic_end(ps2::Vu0Regs& r,std::uint8_t*) {ps2::vuops::g_dispatch_flags.t+=1000001;r.tpc=0x100;}
bool inject_mismatch = true;
void corrupt(ps2::Vu0Regs& r,std::uint8_t* mem) {vu1_0000000000040001(r,mem);if(inject_mismatch)r.vi[14]=99;}
int main(int argc,char**argv) {
 using namespace ps2;
 if(argc!=4 || !std::ifstream(argv[1],std::ios::binary).read((char*)g_vu1_code,16384))return 2;
 const std::string mode=argv[2],out=argv[3];vu::code_changed(1);
 auto key=[](unsigned pc){return vu::program_key(g_vu1_code,vu::reachable(g_vu1_code,16383,pc),pc);};
 vu::Program programs[]={{key(0),mode=="overshoot"?atomic_end:(mode=="mismatch" || mode=="mixed")?corrupt:vu1_0000000000040001},{key(0x80),vu1_0000000000040002}};
 vu::register_programs(programs,mode=="unsupported"?1:2);
 const bool longer=mode=="budget" || mode=="extended" || mode=="plain-long" || mode=="fresh" || mode=="mixed" || mode=="dry-budget" || mode=="plain-dry-long" || mode=="active-budget" || mode=="plain-active-long";
 const bool active_pipe=mode=="active" || mode=="active-budget" || mode=="plain-active" || mode=="plain-active-long";
 const bool dry=mode=="dry" || mode=="dry-budget" || mode=="plain-dry" || mode=="plain-dry-long";
 const bool capture=mode!="no-capture" && mode!="plain-no-capture";
 const bool prefilled=mode=="prefilled" || mode=="plain-prefilled";
 std::vector<std::uint8_t> packets;vu::g_check_packets=&packets;vu::g_reference_dry=false;
 auto init=[&](unsigned count){
  vu::reset();packets.clear();delivered.clear();capture_sizes.clear();std::memset(g_vu1_mem,0,16384);auto&r=vu::regs(1);r.vi[9]=16;r.vi[10]=count;r.vi[13]=1;r.q=0x3F800000;r.vf[1].w[0]=0x3F800000;r.vf[2].w[0]=0x40000000;
  const std::uint64_t tag=0x8000,one=0x1111,two=0x2222;std::memcpy(g_vu1_mem,&tag,8);std::memcpy(g_vu1_mem+8,&one,8);std::memcpy(g_vu1_mem+16,&tag,8);std::memcpy(g_vu1_mem+24,&two,8);
 };
 auto valid=[&](){
  const unsigned prefix=prefilled?3:0;
  const bool packet_ok=capture ? packets.size()==prefix+40 && packets[prefix+12]==0x11 && packets[prefix+32]==0x22 && (!prefilled || (packets[0]==0xA1 && packets[1]==0xB2 && packets[2]==0xC3)) : packets.empty();
  // A checked prefix captures privately until handoff; normal execution sees
  // the enclosing capture directly. Both must submit exactly the same bytes.
  const bool private_capture=!mode.starts_with("plain");
  const bool delivery_ok=dry ? delivered.empty() && capture_sizes.empty() : delivered.size()==2 && delivered[0].size()==16 && delivered[1].size()==16 && delivered[0][8]==0x11 && delivered[1][8]==0x22 && capture_sizes[0]==(private_capture?20:capture?prefix+20:0) && capture_sizes[1]==(private_capture?40:capture?prefix+40:0);
  return vu::regs(1).vi[10]==0 && vu::regs(1).q==0x3F000000 && vu::regs(1).vf[5].w[0]==0x3F000000 && vu::regs(1).tpc==0xF8 && packet_ok && delivery_ok;
 };
 // A checkpoint context must restore all enclosing diagnostic state on both
 // normal scope exit and exception unwinding, including an inactive pipe.
 init(2);
 for(bool active: {false,true}) for(bool outer_dry: {false,true}) {
  vuops::g_dispatch_flags_active=active;vu::g_reference_dry=outer_dry;
  vuops::g_dispatch_flags.t=73;vuops::g_dispatch_flags.q_pending=true;
  vuops::g_dispatch_flags.q_ready=100;vuops::g_dispatch_flags.q_value=0x3F400000;
  std::int64_t escape=123;vu::FastCheckpoint point;point.pc=24;
  vu::g_capture=&escape;vu::g_fast_checkpoint=&point;
  packets={0xA1,0xB2,0xC3};vu_checkpoint::Image host;host.save();
  auto isolated=host;isolated.registers[0]^=1;isolated.memory[100]^=1;isolated.pipe.t=999;
  try {
   vu_checkpoint::Context context(isolated);
   vu_checkpoint::Image installed;installed.save();
   if(!vu_checkpoint::equal(installed,isolated) || !vu::g_reference_dry || !vuops::g_dispatch_flags_active || vu::g_check_packets!=&isolated.packets || vu::g_capture || vu::g_fast_checkpoint)return 1;
   vu::regs(1).q=0;g_vu1_mem[100]=42;vuops::g_dispatch_flags.t=1234;
   isolated.packets.push_back(0xDD);
   if(outer_dry)throw std::runtime_error("original unwind fixture");
  }catch(const std::runtime_error&){}
  vu_checkpoint::Image restored;restored.save();
  if(!vu_checkpoint::equal(host,restored) || vuops::g_dispatch_flags_active!=active || vu::g_reference_dry!=outer_dry || vu::g_check_packets!=&packets || vu::g_capture!=&escape || escape!=123 || vu::g_fast_checkpoint!=&point || point.pc!=24 || packets!=std::vector<std::uint8_t>({0xA1,0xB2,0xC3}))return 1;
  vu::g_capture=nullptr;vu::g_fast_checkpoint=nullptr;
 }
 vuops::g_dispatch_flags_active=false;
 vu::g_reference_dry=dry;vu::g_check_packets=capture?&packets:nullptr;
 inject_mismatch=mode!="mixed";
 init(longer?10000:2);if(prefilled)packets={0xA1,0xB2,0xC3};
 const auto outer_pipe=vuops::g_dispatch_flags;
 if(active_pipe) {
  vuops::FlagDispatch scope(vu::regs(1));vuops::g_dispatch_flags=outer_pipe;
  vu::run_chain(0);
  const auto& pipe=vuops::g_dispatch_flags;
  std::ofstream semantic(out+"-pipe.txt");
  semantic<<pipe.t<<' '<<pipe.mh<<' '<<pipe.ch<<' '<<pipe.q_pending<<' '<<pipe.q_value<<' '<<pipe.q_ready<<'\n';
  for(unsigned i=0;i<8;++i)semantic<<pipe.mac_ts[i]<<' '<<pipe.mac_v[i]<<' '<<pipe.status_v[i]<<' '<<pipe.clip_ts[i]<<' '<<pipe.clip_v[i]<<'\n';
 } else vu::run(1,0);
 if(vuops::g_dispatch_flags_active || !vu_checkpoint::pipe_equal(outer_pipe,vuops::g_dispatch_flags) || vu::g_reference_dry!=dry || vu::g_check_packets!=(capture?&packets:nullptr) || vu::g_capture || vu::g_fast_checkpoint)return 1;
 if(mode=="overshoot") {
  if(vu::regs(1).tpc!=0x100 || vu::regs(1).vi[10]!=2 || !packets.empty() || !delivered.empty()) {
   std::cerr<<"completed atomic fragment was resumed after budget exhaustion\n";return 1;
  }
  vu::g_check_packets=nullptr;return 0;
 }
 if(!valid() || vu::regs(1).vi[14]!=(mode=="mismatch"?99:0)){std::cerr<<"live result/packet ordering changed\n";return 1;}
 auto dump=[&](const char*s,const void*p,unsigned n){std::ofstream(out+s,std::ios::binary).write((const char*)p,n);};
 dump("-regs.bin",&vu::regs(1),sizeof(Vu0Regs));dump("-mem.bin",g_vu1_mem,16384);dump("-packets.bin",packets.data(),packets.size());
 if(mode=="fresh" || mode=="mixed"){init(2);inject_mismatch=true;vu::run(1,0);if(!valid() || (mode=="mixed" && vu::regs(1).vi[14]!=99))return 1;}
 vu::g_check_packets=nullptr;vu::g_reference_dry=false;
 std::cout<<"live chain completed, exact Q/counter/end/packet assertions passed\n";
}
'''
OUTCOMES = re.compile(r'^\[vu-chain-outcomes\] attempted (\d+) complete (\d+) mismatch (\d+) budget_exhausted (\d+) unsupported (\d+) unchecked_tail_dispatches (\d+) checkpoints (\d+) continuations (\d+)$', re.M)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--wgpu', type=Path, required=True)
    parser.add_argument('--case', choices=('all', 'budget', 'overshoot'), default='all')
    args = parser.parse_args()
    d = args.output.resolve()
    if d.exists() or not d.is_relative_to(ROOT/'local'):
        parser.error('output must be a new private local directory')
    d.mkdir(parents=True)
    (d/'tmp').mkdir()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    env = {k:v for k,v in os.environ.items() if not k.startswith('PS2_')}
    env['TMPDIR'] = str(d/'tmp')
    commands = []
    def run(*argv):
        commands.append(list(map(str, argv)))
        (d/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
        subprocess.run(commands[-1], cwd=ROOT, env=env, check=True, timeout=900)
    inputs = [Path(__file__), ROOT/'runtime/src/vu_micro.cpp', ROOT/'runtime/src/vu_checkpoint.hpp', ROOT/'scripts/repro_vu_checkpoint.py', args.runtime.resolve(), args.wgpu.resolve()]
    (d/'inputs.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}, indent=2)+'\n')
    (d/'generator.cpp').write_text(GENERATOR)
    (d/'driver.cpp').write_text(DRIVER)
    run('clang++','-std=c++20','-O2','-I.','-Iruntime/include',d/'generator.cpp','-o',d/'generator')
    run(d/'generator',d)
    run('clang++','-std=c++20','-O2','-I.','-Iruntime/include','-Iruntime/src',d/'driver.cpp',d/'native.cpp',args.runtime.resolve(),args.wgpu.resolve(),'-framework','Metal','-framework','QuartzCore','-framework','Foundation','-framework','CoreFoundation','-framework','IOKit','-framework','IOSurface','-lobjc','-o',d/'native')
    results = {}
    modes = (args.case,) if args.case != 'all' else ('plain-short','plain-long','plain-dry','plain-dry-long','plain-no-capture','plain-prefilled','plain-active','plain-active-long','complete','budget','extended','unsupported','mismatch','fresh','mixed','invalid','overshoot','dry','dry-budget','no-capture','prefilled','active','active-budget')
    for mode in modes:
        case = d/mode
        case.mkdir()
        settings = dict(env)
        if not mode.startswith('plain'):
            settings['PS2_VU_CHECK'] = 'all'
        if mode == 'extended':
            settings['PS2_VU_CHECK_CONTINUATIONS'] = '16384'
        if mode == 'invalid':
            settings['PS2_VU_CHECK_CONTINUATIONS'] = '32768'
        cmd = [str(d/'native'),str(d/'code.bin'),mode,str(case/'final')]
        with (case/'log.txt').open('w') as log:
            proc = subprocess.run(cmd, cwd=case, env=settings, stdout=log, stderr=subprocess.STDOUT, timeout=900)
        text = (case/'log.txt').read_text()
        assert proc.returncode == 0, (mode, proc.returncode, text[-2000:])
        if not mode.startswith('plain'):
            match = OUTCOMES.findall(text)
            assert len(match) == 1, (mode, 'missing bounded-outcome summary', text[-2000:])
            values = list(map(int, match[0]))
            expected = {'complete':(1,1,0,0,0), 'budget':(1,0,0,1,0), 'extended':(1,1,0,0,0), 'unsupported':(1,0,0,0,1), 'mismatch':(1,0,1,0,0), 'fresh':(2,1,0,1,0), 'mixed':(2,0,1,1,0), 'invalid':(1,0,0,0,1), 'overshoot':(1,0,0,1,0), 'dry':(1,1,0,0,0), 'dry-budget':(1,0,0,1,0), 'no-capture':(1,1,0,0,0), 'prefilled':(1,1,0,0,0), 'active':(1,1,0,0,0), 'active-budget':(1,0,0,1,0)}[mode]
            assert tuple(values[:5]) == expected, (mode, values)
            assert (values[5] > 0) == (mode in ('budget','unsupported','fresh','mixed','invalid','dry-budget','active-budget')), (mode, values)
            if mode == 'mixed':
                assert (case/'vu-chain-incomplete-before.bin').is_file() and (case/'vu-chain-mismatch-before.bin').is_file()
                assert 'outcome=mismatch' in text
            results[mode] = values
    if args.case == 'all':
        for mode, plain in [('complete','plain-short'),('unsupported','plain-short'),('budget','plain-long'),('extended','plain-long'),('fresh','plain-long'),('mixed','plain-long'),('invalid','plain-short'),('dry','plain-dry'),('dry-budget','plain-dry-long'),('no-capture','plain-no-capture'),('prefilled','plain-prefilled'),('active','plain-active'),('active-budget','plain-active-long')]:
            for suffix in ('regs.bin','mem.bin','packets.bin') + (('pipe.txt',) if mode.startswith('active') else ()):
                assert (d/mode/('final-'+suffix)).read_bytes() == (d/plain/('final-'+suffix)).read_bytes(), (mode, suffix)
    (d/'results.json').write_text(json.dumps(results, indent=2)+'\n')
    print('Production whole-chain complete/mismatch/budget/unsupported outcomes and exact live handoff passed')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
