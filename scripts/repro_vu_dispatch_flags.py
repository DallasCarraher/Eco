#!/usr/bin/env python3
"""Original issue-4 dispatch flags regression. Failed assertions exit nonzero.

Requires CMake, C++20 clang++ with std::format, and Node with Wasm tail calls.
No game data. Private temporary builds. Checks delayed flags across compiled
and fallback dispatch, fresh invocations, reset and VU0 isolation. Expected
FSAND reads stay (0, 2); see docs/ISSUE4-VU.md for their original derivation.
"""
import os
import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]

GENERATOR = r'''
#define main vurecomp_main
#include "recomp/vurecomp.cpp"
#undef main
#include "runtime/src/vu_jit.hpp"
#include <cstddef>
int main(int argc, char **argv) {
    fs::path out=argv[1];
    std::ofstream native(out/"native.cpp");
    native << "#include \"ps2/vu_ops.hpp\"\nusing namespace ps2; using namespace ps2::vuops;\n";
    for(int kind=0;kind<3;++kind) {
        Program p{0x10001,0,std::vector<std::uint8_t>(16384)};
        const auto put=[&](unsigned pc,unsigned lo,unsigned hi=0x2FF) {
            std::memcpy(p.code.data()+pc,&lo,4);std::memcpy(p.code.data()+pc+4,&hi,4);
        };
        const unsigned nop=0x8000033C;
        put(0,(0x24u<<25)|(9u<<11));
        if(kind<2) {
            // SUB.x 1 - 2 in the jump delay slot; status/MAC latency is four.
            put(8,nop,(8u<<21)|(2u<<16)|(1u<<11)|(3u<<6)|0x2Cu);
            put(0x80,nop);put(0x88,nop);
            const auto read=[&](unsigned it) {return kind==0?(0x16u<<25)|(it<<16)|2u:(0x1Au<<25)|(7u<<11)|(it<<16);};
            put(0x90,read(1));put(0x98,read(2),0x400002FF);put(0xA0,nop);
        } else {
            // CLIP sees x=1 > |w=0|. Its three-cycle history also crosses JR.
            put(8,nop,(2u<<16)|(1u<<11)|(7u<<6)|0x3Fu);
            put(0x80,nop);put(0x88,(0x1Cu<<25)|(1u<<16));
            put(0x90,(0x1Cu<<25)|(2u<<16),0x400002FF);put(0x98,nop);
        }
        std::ofstream(out/std::format("code{}.bin",kind),std::ios::binary).write((char*)p.code.data(),p.code.size());
        for(int part=0;part<2;++part) {
            p.key=0x10001+kind*2+part;p.entry=part?0x80:0;
            std::string name;native<<generate(p,name);
            std::vector<std::uint8_t> wasm;
            if(!ps2::vu::jit::translate(p.code.data(),p.entry,{0x1000,true},wasm)) return 2;
            std::ofstream(out/std::format("{}-{}.wasm",kind,part),std::ios::binary).write((char*)wasm.data(),wasm.size());
        }
    }
    // Original finite loop requiring more than the diagnostic continuation cap.
    Program loop{0x10007,0,std::vector<std::uint8_t>(16384)};
    const auto put=[&](unsigned pc,unsigned lo,unsigned hi=0x2FF) {
        std::memcpy(loop.code.data()+pc,&lo,4);std::memcpy(loop.code.data()+pc+4,&hi,4);
    };
    const unsigned nop=0x8000033C;
    put(0,(0x24u<<25)|(9u<<11));put(8,nop);
    put(0x80,(0x09u<<25)|(10u<<16)|(10u<<11)|1u);put(0x88,nop);
    put(0x90,(0x28u<<25)|(10u<<11)|5u);put(0x98,nop);
    put(0xA0,(0x24u<<25)|(9u<<11));put(0xA8,nop);
    put(0xC0,nop,0x400002FF);put(0xC8,nop);
    std::ofstream(out/"code3.bin",std::ios::binary).write((char*)loop.code.data(),loop.code.size());
    for(unsigned part=0;part<2;++part) {
        loop.key=0x10007+part;loop.entry=part?0x80:0;
        std::string name;native<<generate(loop,name);
    }
    std::ofstream(out/"offsets.json") << std::format("{{\"vi\":{},\"vf\":{},\"rawStatus\":{},\"rawMac\":{},\"rawClip\":{},\"size\":{}}}",offsetof(ps2::Vu0Regs,vi),offsetof(ps2::Vu0Regs,vf),offsetof(ps2::Vu0Regs,status),offsetof(ps2::Vu0Regs,mac),offsetof(ps2::Vu0Regs,clip),sizeof(ps2::Vu0Regs));
    std::ofstream(out/"pipe.json") << std::format("{{\"t\":{},\"mh\":{},\"ts\":{},\"status\":{},\"mac\":{},\"ch\":{},\"clipTs\":{},\"clip\":{},\"size\":{}}}",offsetof(ps2::vuops::FlagPipe,t),offsetof(ps2::vuops::FlagPipe,mh),offsetof(ps2::vuops::FlagPipe,mac_ts),offsetof(ps2::vuops::FlagPipe,status_v),offsetof(ps2::vuops::FlagPipe,mac_v),offsetof(ps2::vuops::FlagPipe,ch),offsetof(ps2::vuops::FlagPipe,clip_ts),offsetof(ps2::vuops::FlagPipe,clip_v),sizeof(ps2::vuops::FlagPipe));
}
'''
DRIVER = r'''
#include "runtime/src/vu_micro.cpp"
#include <iostream>
void vu1_0000000000010001(ps2::Vu0Regs&,std::uint8_t*);
void vu1_0000000000010002(ps2::Vu0Regs&,std::uint8_t*);
void vu1_0000000000010003(ps2::Vu0Regs&,std::uint8_t*);
void vu1_0000000000010004(ps2::Vu0Regs&,std::uint8_t*);
void vu1_0000000000010005(ps2::Vu0Regs&,std::uint8_t*);
void vu1_0000000000010006(ps2::Vu0Regs&,std::uint8_t*);
void vu1_0000000000010007(ps2::Vu0Regs&,std::uint8_t*);
void vu1_0000000000010008(ps2::Vu0Regs&,std::uint8_t*);
int main(int argc,char **argv) {
 using namespace ps2;
 if(argc!=4 || !std::ifstream(argv[1],std::ios::binary).read((char*)g_vu1_code,16384)) return 2;
 const unsigned kind=std::stoul(argv[3]),expected=kind==0?2:kind==1?128:1;
 if(kind>2) return 2;
 vu::ProgramFn producers[]={vu1_0000000000010001,vu1_0000000000010003,vu1_0000000000010005};
 vu::ProgramFn consumers[]={vu1_0000000000010002,vu1_0000000000010004,vu1_0000000000010006};
 auto init=[] {vu::reset(); std::memset(g_vu1_mem,0,16384);auto &r=vu::regs(1);r.vi[7]=0x80;r.vi[9]=0x10;r.vf[1].w[0]=0x3F800000;r.vf[2].w[0]=0x40000000;};
 auto expect=[](const char *name,unsigned a,unsigned b) {
  auto &r=vu::regs(1);
  if(r.vi[1]!=a||r.vi[2]!=b) {std::cerr<<name<<": "<<r.vi[1]<<","<<r.vi[2]<<" expected "<<a<<","<<b<<"\n";return false;}
  return true;
 };
 init();vu::code_changed(1);vu::run_fast(1,0);
 if(!expect("continuous interpreter",0,expected)) return 1;
 const auto key=[](unsigned pc) {return vu::program_key(g_vu1_code,vu::reachable(g_vu1_code,16383,pc),pc);};
 vu::Program programs[]={{key(0),producers[kind]},{key(0x80),consumers[kind]}};
 const bool fallback=std::string(argv[2])=="fallback";
 vu::register_programs(programs,fallback?1:2);
 // Enough invocations to exercise legacy sampling as well as complete-chain checks.
 for(unsigned repeat=0;repeat<128;++repeat) {
  init();vu::run(1,0);
  if(!expect("dispatch chain",0,expected)) return 1;
 }
 // A new microprogram seeds history from committed raw flags. It must not
 // inherit delayed timestamps from the preceding logical invocation.
 vu::run(1,0x80);if(!expect("next invocation",expected,expected)) return 1;
 init();vu::run(1,0x80);if(!expect("reset invocation",0,0)) return 1;
 // VU0 must not mutate an active VU1 history on the same host thread.
 {
  vuops::FlagDispatch scope(vu::regs(1));
  const auto saved=vuops::g_dispatch_flags;
  std::memcpy(g_vu0_code,g_vu1_code,4096);vu::code_changed(0);
  vu::run_fast(0,0x80);
  if(std::memcmp(&saved,&vuops::g_dispatch_flags,sizeof saved)) return 1;
 }
 if(kind==0) {
  const auto input=std::filesystem::path(argv[1]).parent_path()/"code3.bin";
  if(!std::ifstream(input,std::ios::binary).read((char*)g_vu1_code,16384)) return 2;
  vu::code_changed(1);
  const auto init_loop=[] {vu::reset();std::memset(g_vu1_mem,0,16384);vu::regs(1).vi[9]=0x10;vu::regs(1).vi[10]=10000;};
  Vu0Regs compiled;std::uint32_t issued;
  init_loop();
  {
   vuops::FlagDispatch scope(vu::regs(1));std::int64_t escape=-1;vu::g_capture=&escape;
   vu1_0000000000010007(vu::regs(1),g_vu1_mem);
   for(unsigned n=0;n<8192;++n) {if(escape!=0x80){std::cerr<<"loop escape "<<escape<<" at "<<n<<"\n";return 1;}escape=-1;vu1_0000000000010008(vu::regs(1),g_vu1_mem);}
   vu::g_capture=nullptr;std::memcpy(&compiled,&vu::regs(1),sizeof compiled);issued=vuops::g_dispatch_flags.t-16;
   if(escape!=0x80 || compiled.vi[10]!=1808 || issued!=49154) {std::cerr<<"compiled loop checkpoint: escape "<<escape<<" counter "<<compiled.vi[10]<<" issued "<<issued<<"\n";return 1;}
  }
  init_loop();
  {
   vuops::FlagDispatch scope(vu::regs(1));vu::FastCheckpoint point;point.limit=issued;vu::g_fast_checkpoint=&point;
   vu::run_fast(1,0);vu::g_fast_checkpoint=nullptr;
   if(point.complete || point.steps!=issued || point.pc!=0x80 || point.npc!=0x88 || point.ending || !point.branch_live || point.branch_before[10]!=1808 ||
      std::memcmp(&compiled,&vu::regs(1),sizeof compiled)) {for(unsigned k=0;k<sizeof compiled/4;++k){std::uint32_t a,b;std::memcpy(&a,(char*)&compiled+4*k,4);std::memcpy(&b,(char*)&vu::regs(1)+4*k,4);if(a!=b)std::cerr<<"reg word "<<k<<": "<<a<<"/"<<b<<"\n";}std::cerr<<"interpreter checkpoint: complete "<<point.complete<<" steps "<<point.steps<<" pc "<<point.pc<<" npc "<<point.npc<<" counter "<<vu::regs(1).vi[10]<<"\n";return 1;}
  }
  init_loop();vu::FastCheckpoint full;vu::g_fast_checkpoint=&full;vu::run_fast(1,0);vu::g_fast_checkpoint=nullptr;
  if(!full.complete || full.steps!=60002 || vu::regs(1).vi[10]!=0) {std::cerr<<"interpreter full loop: "<<full.complete<<" counter "<<vu::regs(1).vi[10]<<" steps "<<full.steps<<"\n";return 1;}
  // A checkpoint after DIV must preserve pending Q rather than flush it.
  std::memset(g_vu1_code,0,16384);
  const unsigned divide=(0x40u<<25)|(2u<<16)|(1u<<11)|(14u<<6)|0x3Cu,unop=0x2FF;
  std::memcpy(g_vu1_code,&divide,4);std::memcpy(g_vu1_code+4,&unop,4);
  vu::code_changed(1);init();vu::regs(1).q=0x3F800000;
  {
   vuops::FlagDispatch scope(vu::regs(1));vu::FastCheckpoint point;point.limit=1;vu::g_fast_checkpoint=&point;
   vu::run_fast(1,0);vu::g_fast_checkpoint=nullptr;
   const auto &pipe=vuops::g_dispatch_flags;
   if(point.complete || point.pc!=8 || point.npc!=16 || point.steps!=1 || !pipe.q_pending ||
      pipe.q_value!=0x3F000000 || vu::regs(1).q!=0x3F800000) return 1;
  }
  std::cout<<"finite 10000-iteration loop: 8192-continuation prefix aligned at 49154 instructions; uninterrupted interpreter completes\n";
 }
 std::cout<<(fallback?"compiled -> interpreter":"compiled -> compiled")
          <<" flag kind "<<kind<<": 128 delayed reads, fresh invocation, reset, VU0 isolation passed\n";
}
'''
WASM = r'''
const fs=require('node:fs'),path=require('node:path');const dir=process.argv[2];
const pipe=JSON.parse(fs.readFileSync(path.join(dir,'pipe.json')));
const off=JSON.parse(fs.readFileSync(path.join(dir,'offsets.json')));
const memory=new WebAssembly.Memory({initial:1,maximum:65536,shared:true});
const v=new DataView(memory.buffer),r=0x3000,fl=0x1000;let escape=-1;
function resetPipe(){
 new Uint8Array(memory.buffer,fl,pipe.size).fill(0);
 v.setUint32(fl+pipe.t,16,true);
 for(const [raw,ring] of [[off.rawStatus,pipe.status],[off.rawMac,pipe.mac],[off.rawClip,pipe.clip]])
  for(let i=0;i<8;++i)v.setUint32(fl+ring+4*i,v.getUint32(r+raw,true),true);
}
function init(){
 new Uint8Array(memory.buffer,r,off.size).fill(0);
 v.setUint16(r+off.vi+18,0x10,true);v.setUint16(r+off.vi+14,0x80,true);
 v.setUint32(r+off.vf+12,0x3F800000,true);
 v.setUint32(r+off.vf+16,0x3F800000,true);v.setUint32(r+off.vf+32,0x40000000,true);
 resetPipe();
}
for(let kind=0;kind<3;++kind){
const expected=kind===0?2:kind===1?128:1;
const runs=[];
for(let i=0;i<2;++i){
 const mod=new WebAssembly.Module(fs.readFileSync(path.join(dir,`${kind}-${i}.wasm`)));
 const env={memory};for(const imp of WebAssembly.Module.imports(mod)){
  if(imp.kind!=='function')continue;
  env[imp.name]=()=>{throw Error(`unexpected import ${imp.name}`)};
 }
 env.interpret=(unit,pc)=>{escape=pc;};
 const read=(fl,head,ts,ring,latency)=>{
  const t=v.getUint32(fl+pipe.t,true),h=v.getUint32(fl+head,true);
  for(let k=1;k<=8;++k){const i=(h-k)&7;
   if(v.getUint32(fl+ts+4*i,true)+latency<=t)return v.getUint32(fl+ring+4*i,true);
  }
  return v.getUint32(fl+ring+4*((h-8)&7),true);
 };
 env.status=fl=>read(fl,pipe.mh,pipe.ts,pipe.status,4);
 env.mac=fl=>read(fl,pipe.mh,pipe.ts,pipe.mac,4);
 env.clip=fl=>read(fl,pipe.ch,pipe.clipTs,pipe.clip,3);
 runs.push(new WebAssembly.Instance(mod,{env}).exports.run);
}
function expect(name,a,b){
 const x=v.getUint16(r+off.vi+2,true),y=v.getUint16(r+off.vi+4,true);
 if(x!==a||y!==b)throw Error(`${name}: ${x},${y} expected ${a},${b}`);
}
for(let repeat=0;repeat<128;++repeat){
 init();escape=-1;runs[0](r,0x4000);
 if(escape!==0x80)throw Error(`unexpected dispatch ${escape}`);
 runs[1](r,0x4000);expect('dispatch',0,expected);
}
resetPipe();runs[1](r,0x4000);expect('next invocation',expected,expected);
init();runs[1](r,0x4000);expect('reset invocation',0,0);
console.log(`Wasm flag kind ${kind}: 128 delayed reads, fresh invocation, reset passed`);
}
'''

def run(*args):
    return subprocess.run(args, cwd=ROOT, check=True, timeout=900)


def main():
    with tempfile.TemporaryDirectory(prefix='eco-vu-dispatch-') as directory:
        d = pathlib.Path(directory)
        (d/'generator.cpp').write_text(GENERATOR)
        run('clang++','-std=c++20','-O2','-I.','-Iruntime/include',str(d/'generator.cpp'),'runtime/src/vu_jit.cpp','-o',str(d/'generator'))
        run(str(d/'generator'),str(d))
        run('cmake','-S',str(ROOT),'-B',str(d/'build'),'-DCMAKE_BUILD_TYPE=Release','-DPS2_WGPU_DIR=/nonexistent')
        run('cmake','--build',str(d/'build'),'--target','ps2runtime','-j','4')
        (d/'driver.cpp').write_text(DRIVER)
        run('clang++','-std=c++20','-O2','-I.','-Iruntime/include','-Iruntime/src',str(d/'driver.cpp'),str(d/'native.cpp'),str(d/'build/libps2runtime.a'),'-o',str(d/'native'))
        for kind in range(3):
            for mode in ('compiled', 'fallback'):
                for check in (None, '1', 'all'):
                    env = {k: v for k, v in os.environ.items() if not k.startswith('PS2_')}
                    if check is not None:
                        env['PS2_VU_CHECK'] = check
                    subprocess.run([str(d/'native'), str(d/f'code{kind}.bin'), mode, str(kind)],
                                   cwd=ROOT, env=env, timeout=900, check=True)
        (d/'wasm.cjs').write_text('try {\n'+WASM+'\n} catch (e) { console.error(e); process.exit(2); }')
        run('node',str(d/'wasm.cjs'),str(d))
        return 0

if __name__=='__main__':
    raise SystemExit(main())
