#!/usr/bin/env python3
"""Original finite checkpoint regression. No game inputs; private new output only.

Run under the shared serial allocation. Links the supplied read-only runtime
archive, without rebuilding it. All build commands and identities are recorded.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = r'''
#define main vurecomp_main
#include "recomp/vurecomp.cpp"
#undef main
int main(int argc, char** argv) {
 fs::path out=argv[1];Program p{0x40001,0,std::vector<std::uint8_t>(16384)};
 auto put=[&](unsigned pc,unsigned lo,unsigned hi=0x2FF){std::memcpy(p.code.data()+pc,&lo,4);std::memcpy(p.code.data()+pc+4,&hi,4);};
 const unsigned nop=0x8000033C,div=(0x40u<<25)|(2u<<16)|(1u<<11)|(14u<<6)|0x3Cu;
 const unsigned kick=(0x40u<<25)|(27u<<6)|0x3Cu;
 put(0,kick|(12u<<11));
 put(8,(0x24u<<25)|(9u<<11));
 put(16,nop,(8u<<21)|(2u<<16)|(1u<<11)|(4u<<6)|0x2Cu);
 put(0x80,nop,(8u<<21)|(1u<<11)|(3u<<6)|0x1Cu);
 put(0x88,0x800003BF);
 put(0x90,nop,(8u<<21)|(1u<<11)|(5u<<6)|0x1Cu);
 put(0x98,(0x09u<<25)|(10u<<16)|(10u<<11)|1u);
 put(0xA0,nop);
 put(0xA8,(0x28u<<25)|(10u<<11)|6u);
 put(0xB0,nop);
 put(0xB8,div);
 put(0xC0,(0x24u<<25)|(9u<<11));put(0xC8,nop);
 put(0xE0,kick|(13u<<11));put(0xE8,nop,0x400002FF);put(0xF0,nop);
 std::ofstream(out/"code.bin",std::ios::binary).write((char*)p.code.data(),p.code.size());
 std::ofstream native(out/"native.cpp");native<<"#include \"ps2/vu_ops.hpp\"\nusing namespace ps2;using namespace ps2::vuops;\n";
 for(unsigned part=0;part<2;++part){p.key=0x40001+part;p.entry=part?0x80:0;std::string name;native<<generate(p,name);}
}
'''
DRIVER = r'''
#include "runtime/src/vu_micro.cpp"
#include "scripts/vu_checkpoint.hpp"
#include <iostream>
using namespace ps2;
using namespace vu_checkpoint;
void vu1_0000000000040001(Vu0Regs&,std::uint8_t*);
void vu1_0000000000040002(Vu0Regs&,std::uint8_t*);
#define CHECK(x) do {if(!(x)){std::cerr<<"failed line "<<__LINE__<<": "<<#x<<"\n";return 1;}}while(0)
Image initial(unsigned counter=10000) {
 vu::reset();std::memset(g_vu1_mem,0,16384);
 auto &r=vu::regs(1);r.vi[9]=16;r.vi[10]=counter;r.vi[12]=0;r.vi[13]=1;
 r.q=0x3F800000;r.vf[1].w[0]=0x3F800000;r.vf[2].w[0]=0x40000000;
 const std::uint64_t tag=0x8000,one=0x1111,two=0x2222;
 std::memcpy(g_vu1_mem,&tag,8);std::memcpy(g_vu1_mem+8,&one,8);
 std::memcpy(g_vu1_mem+16,&tag,8);std::memcpy(g_vu1_mem+24,&two,8);
 vuops::FlagDispatch scope(r);Image image;image.save();return image;
}
int main(int argc,char**argv) {
 if(argc!=2 || !std::ifstream(argv[1],std::ios::binary).read((char*)g_vu1_code,16384))return 2;
 vu::code_changed(1);
 auto key=[](unsigned pc){return vu::program_key(g_vu1_code,vu::reachable(g_vu1_code,16383,pc),pc);};
 vu::Program programs[]={{key(0),vu1_0000000000040001},{key(0x80),vu1_0000000000040002}};
 vu::register_programs(programs,2);
 const auto start=initial();Interpreter full(start);full.advance(0);
 CHECK(full.cursor.complete && full.cursor.steps==100003);
 {Context context(full.image);CHECK(vu::regs(1).vi[10]==0);CHECK(vu::regs(1).vf[3].w[0]==0x3F000000);CHECK(vu::regs(1).vf[5].w[0]==0x3F000000);}
 CHECK(full.image.packets.size()==40);
 CHECK(full.image.packets[12]==0x11 && full.image.packets[32]==0x22);
 auto altered=full.image;altered.pipe.q_ready^=1;CHECK(!equal(altered,full.image));
 altered=full.image;altered.pipe.q_pending=!altered.pipe.q_pending;CHECK(!equal(altered,full.image));
 altered=full.image;altered.pipe.q_value^=1;CHECK(!equal(altered,full.image));
 altered=full.image;altered.pipe.status_v[0]^=1;CHECK(!equal(altered,full.image));
 altered=full.image;std::swap(altered.packets[12],altered.packets[32]);CHECK(!equal(altered,full.image));
 Compiled captured(start,0);captured.advance(1);
 {Context context(captured.image);g_vu1_mem[8]=0;captured.image.save();}
 CHECK(captured.image.packets[12]==0x11 && captured.image.memory[8]==0);
 // Uninterrupted compiled dispatch loop vs uninterrupted interpreter; synthetic
 // ceiling is fixed at construction, never exposed to the saved-input CLI.
 Compiled whole(start,0,10001);whole.advance(10001);
 CHECK(whole.complete && whole.continuations==10000 && whole.issued==100003);
 CHECK(equal(whole.image,full.image));
 for(unsigned chunk: {1u,7u,257u}) {
  Compiled compiled(start,0,10001);Interpreter reference(start);
  while(!compiled.complete){compiled.advance(chunk);CHECK(compiled.stop==Compiled::Stop::checkpoint || compiled.complete);reference.advance(compiled.issued);CHECK(reference.cursor.steps==compiled.issued);CHECK(reference.cursor.pc==compiled.pc);CHECK(equal(compiled.image,reference.image));}
  CHECK(equal(compiled.image,whole.image));CHECK(reference.cursor.complete);
 }
 // The default aggregate guard remains exhausted across repeated chunks.
 Compiled bounded(start,0);while(bounded.continuations<8192)bounded.advance(257);
 CHECK(!bounded.complete && bounded.stop==Compiled::Stop::continuation_limit);
 const auto before=bounded.image;const auto issued=bounded.issued;bounded.advance(257);
 CHECK(bounded.continuations==8192 && bounded.issued==issued && equal(before,bounded.image));
 {Context context(bounded.image);CHECK(vu::regs(1).vi[10]==1808);}
 // Stop every single instruction: root jump/delay slot, flags, DIV, pending Q,
 // VI history, direct conditional branch, E and end delay slot. Independent old
 // Q assertion is made before the first WAITQ after DIV.
 Interpreter small(initial(2));Interpreter small_full(small.image);small_full.advance(0);
 bool saw_q=false,saw_end=false,saw_npc=false;
 for(unsigned target=1;!small.cursor.complete;++target){
  small.advance(target);CHECK(small.cursor.steps==target);
  if(small.image.pipe.q_pending && !saw_q){Context context(small.image);CHECK(vu::regs(1).q==0x3F800000);CHECK(small.image.pipe.q_value==0x3F000000);saw_q=true;}
  saw_end|=small.cursor.ending;saw_npc|=small.cursor.npc!=small.cursor.pc+8;
  // Copy cursor and image to a fresh owner, with a destroyed host Context.
  auto copy=small;small=copy;
 }
 CHECK(saw_q && saw_end && saw_npc && equal(small.image,small_full.image));
 // Control-history fixture: immediately testing a decremented VI must see old
 // VI=1, leave the branch untaken, and execute the marker at PC 24.
 std::memset(g_vu1_code,0,16384);
 auto put=[](unsigned pc,unsigned lo,unsigned hi=0x2FF){std::memcpy(g_vu1_code+pc,&lo,4);std::memcpy(g_vu1_code+pc+4,&hi,4);};
 const unsigned nop=0x8000033C;
 put(0,(0x09u<<25)|(10u<<16)|(10u<<11)|1u);
 put(8,(0x28u<<25)|(10u<<11)|2u);put(16,nop);
 put(24,(0x08u<<25)|(11u<<16)|1u);put(32,nop,0x400002FF);put(40,nop);
 vu::code_changed(1);Interpreter history(initial(1));history.advance(1);
 CHECK(history.cursor.branch_live && history.cursor.branch_before[10]==1);
 Interpreter lost=history;lost.cursor.branch_live=false;
 history.advance(0);lost.advance(0);
 {Context context(history.image);CHECK(vu::regs(1).vi[11]==1);}
 CHECK(!equal(history.image,lost.image));
 // A pending branch target and pending end survive separate resumes.
 put(0,(0x20u<<25)|3u);vu::code_changed(1);
 Interpreter branch(initial(1));branch.advance(1);CHECK(branch.cursor.pc==8 && branch.cursor.npc==32);
 auto bad=branch;bad.cursor.npc=16;branch.advance(0);bad.advance(0);CHECK(!equal(branch.image,bad.image));
 Interpreter ending(initial(1));ending.entry=32;ending.advance(1);CHECK(ending.cursor.ending && !ending.cursor.complete);ending.advance(2);CHECK(ending.cursor.complete && ending.cursor.steps==2);
 // Infinite original branch loop: cumulative instruction budget cannot reset.
 put(0,(0x20u<<25)|0x7FFu);put(8,nop);vu::code_changed(1);
 Interpreter infinite(initial());infinite.advance(500000);infinite.advance(0);
 CHECK(!infinite.cursor.complete && infinite.cursor.stop==vu::FastStop::instruction_limit && infinite.cursor.steps==1000000);
 const auto exhausted=infinite.image;infinite.advance(0);CHECK(equal(exhausted,infinite.image) && infinite.cursor.steps==1000000);
 Compiled unsupported(initial(),0);unsupported.advance(1);CHECK(!unsupported.complete && unsupported.stop==Compiled::Stop::unsupported_boundary);
 infinite.cursor.npc=3;infinite.advance(0);CHECK(infinite.cursor.stop==vu::FastStop::invalid_resume);
 std::cout<<"checkpoint: 10000 continuations/100003 instructions complete; chunks 1/7/257 exact; branch, end, pending Q, packet order and cumulative guards passed\n";
}
'''


FALLBACK_DRIVER = r'''
#define main replay_main
#include REPLAY_SOURCE
#undef main
void vu1_0000000000040001(ps2::Vu0Regs&,std::uint8_t*);
void register_fixture() {
 using namespace ps2;
 vu::Program p{vu::program_key(g_vu1_code,vu::reachable(g_vu1_code,16383,0),0),vu1_0000000000040001};
 vu::register_programs(&p,1);
}
int main(int argc,char**argv) {
 using namespace ps2;
 if(argc!=3)return 2;
 const std::string prefix=std::string(argv[2])+"/fallback-input",out=std::string(argv[2])+"/fallback-output";
 vu::reset();if(!std::ifstream(argv[1],std::ios::binary).read((char*)g_vu1_code,16384))return 2;
 const unsigned branch=(0x20u<<25)|0x7FFu,nop=0x8000033C,unop=0x2FF;
 std::memcpy(g_vu1_code+0x80,&branch,4);std::memcpy(g_vu1_code+0x84,&unop,4);
 std::memcpy(g_vu1_code+0x88,&nop,4);std::memcpy(g_vu1_code+0x8C,&unop,4);
 auto &r=vu::regs(1);r.vi[9]=16;r.vf[1].w[0]=0x3F800000;r.vf[2].w[0]=0x40000000;
 std::memset(g_vu1_mem,0,16384);const std::uint64_t tag=0x8000;std::memcpy(g_vu1_mem,&tag,8);
 auto dump=[&](const char*s,const void*p,unsigned n){std::ofstream(prefix+s,std::ios::binary).write((const char*)p,n);};
 dump("-code.bin",g_vu1_code,16384);dump("-before.bin",&r,sizeof r);dump("-memory.bin",g_vu1_mem,16384);
 std::ofstream(prefix+"-meta.txt")<<"0 0 0 -1\n";
 char* args[]={argv[0],const_cast<char*>(prefix.c_str()),const_cast<char*>("compiled-prefix"),const_cast<char*>(out.c_str())};
 register_fixture();
 const auto result=replay_main(4,args);
 std::ifstream status(out+"-status.json");std::string text((std::istreambuf_iterator<char>(status)),{});
 std::cout<<text;
 return result==4 && text.find("instruction_limit")!=std::string::npos ? 0:1;
}
'''

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--wgpu', type=Path, required=True)
    a = p.parse_args()
    d = a.output.resolve()
    if d.exists() or not d.is_relative_to(ROOT/'local'):
        p.error('output must be a new private local directory')
    d.mkdir(parents=True)
    commands = []
    (d/'tmp').mkdir()
    env = {k: v for k, v in os.environ.items() if not k.startswith('PS2_')}
    env['TMPDIR'] = str(d/'tmp')
    inputs = [a.runtime.resolve(), a.wgpu.resolve(), Path(__file__), ROOT/'scripts/vu_checkpoint.hpp', ROOT/'runtime/src/vu_micro.cpp', ROOT/'scripts/replay_vu_snapshot.cpp']
    (d/'inputs.json').write_text(json.dumps({str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}, indent=2)+'\n')
    def run(*argv):
        commands.append(list(map(str, argv)))
        (d/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
        subprocess.run(commands[-1], cwd=ROOT, env=env, check=True, timeout=900)
    (d/'generator.cpp').write_text(GENERATOR)
    (d/'driver.cpp').write_text(DRIVER)
    run('clang++','-std=c++20','-O2','-I.','-Iruntime/include',d/'generator.cpp','-o',d/'generator')
    run(d/'generator', d)
    run('clang++','-std=c++20','-O2','-I.','-Iruntime/include','-Iruntime/src',d/'driver.cpp',d/'native.cpp',a.runtime.resolve(),a.wgpu.resolve(),'-framework','Metal','-framework','QuartzCore','-framework','Foundation','-framework','CoreFoundation','-framework','IOKit','-framework','IOSurface','-lobjc','-o',d/'native')
    run(d/'native',d/'code.bin')
    (d/'fallback.cpp').write_text(FALLBACK_DRIVER)
    run('clang++','-std=c++20','-O2','-I.','-Iruntime/include','-Iruntime/src',
        '-DREPLAY_SOURCE="'+str(ROOT/'scripts/replay_vu_snapshot.cpp')+'"',
        d/'fallback.cpp',d/'native.cpp',a.runtime.resolve(),a.wgpu.resolve(),
        '-framework','Metal','-framework','QuartzCore','-framework','Foundation',
        '-framework','CoreFoundation','-framework','IOKit','-framework','IOSurface',
        '-lobjc','-o',d/'fallback')
    run(d/'fallback',d/'code.bin',d)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
