#!/usr/bin/env python3
"""Original Q handoff regression: old Q before readiness, new Q after WAITQ.

No game input. Uses the existing seven-cycle DIV policy and exact powers of two.
A real alternate direct-branch route makes the shared reader's incoming Q timing
explicitly dynamic. Both routes are tested; neither Eco path is an oracle.
"""
import os
from pathlib import Path
import subprocess
import tempfile
from repro_vu_dispatch_flags import ROOT, run

GENERATOR = r'''
#define main vurecomp_main
#include "recomp/vurecomp.cpp"
#undef main
#include "runtime/src/vu_jit.hpp"
#include <cstddef>
int main(int argc,char **argv) {
 fs::path out=argv[1];Program p{0x20001,0,std::vector<std::uint8_t>(16384)};
 auto put=[&](unsigned pc,unsigned lo,unsigned hi=0x2FF){std::memcpy(p.code.data()+pc,&lo,4);std::memcpy(p.code.data()+pc+4,&hi,4);};
 const unsigned nop=0x8000033C,div=(0x40u<<25)|(2u<<16)|(1u<<11)|(14u<<6)|0x3Cu;
 put(0,div);
 put(8,(0x29u<<25)|(1u<<11)|29u);put(16,nop); // optional direct-branch route
 put(24,(0x24u<<25)|(9u<<11));put(32,nop);   // register dispatch route
 put(0x80,nop,(8u<<21)|(1u<<11)|(3u<<6)|0x1Cu);
 put(0x88,0x800003BF); // WAITQ
 put(0x90,nop,(8u<<21)|(1u<<11)|(5u<<6)|0x1Cu|0x40000000u);put(0x98,nop);
 put(0x100,(div&~(31u<<16))|(4u<<16));
 put(0x108,(0x20u<<25)|0x7EEu);put(0x110,nop);
 if(ps2::vu::q_read_kind(p.code.data(),16383,0x80)!=ps2::vu::kQDynamic) return 2;
 std::ofstream(out/"code.bin",std::ios::binary).write((char*)p.code.data(),p.code.size());
 std::ofstream native(out/"native.cpp");native<<"#include \"ps2/vu_ops.hpp\"\nusing namespace ps2;using namespace ps2::vuops;\n";
 for(unsigned part=0;part<2;++part){
  p.key=0x20001+part;p.entry=part?0x80:0;std::string name;native<<generate(p,name);
  std::vector<std::uint8_t> bytes;if(!ps2::vu::jit::translate(p.code.data(),p.entry,{0x1000,true},bytes))return 2;
  std::ofstream(out/std::format("{}.wasm",part),std::ios::binary).write((char*)bytes.data(),bytes.size());
 }
 std::ofstream(out/"offsets.json")<<std::format("{{\"vi\":{},\"vf\":{},\"q\":{},\"size\":{},\"t\":{},\"pending\":{},\"value\":{},\"ready\":{},\"pipeSize\":{}}}",
 offsetof(ps2::Vu0Regs,vi),offsetof(ps2::Vu0Regs,vf),offsetof(ps2::Vu0Regs,q),sizeof(ps2::Vu0Regs),
 offsetof(ps2::vuops::FlagPipe,t),offsetof(ps2::vuops::FlagPipe,q_pending),offsetof(ps2::vuops::FlagPipe,q_value),offsetof(ps2::vuops::FlagPipe,q_ready),sizeof(ps2::vuops::FlagPipe));
}
'''
DRIVER = r'''
#include "runtime/src/vu_micro.cpp"
#include <iostream>
void vu1_0000000000020001(ps2::Vu0Regs&,std::uint8_t*);
void vu1_0000000000020002(ps2::Vu0Regs&,std::uint8_t*);
int main(int argc,char **argv){
 using namespace ps2;if(argc!=3)return 2;
 if(!std::ifstream(argv[1],std::ios::binary).read((char*)g_vu1_code,16384))return 2;
 vu::code_changed(1);const auto key=[](unsigned pc){return vu::program_key(g_vu1_code,vu::reachable(g_vu1_code,16383,pc),pc);};
 vu::Program programs[]={{key(0),vu1_0000000000020001},{key(0x80),vu1_0000000000020002}};
 vu::register_programs(programs,std::string(argv[2])=="fallback"?1:2);
 auto init=[](unsigned route){vu::reset();auto &r=vu::regs(1);r.vi[1]=route;r.vi[9]=16;r.q=0x3F800000;r.vf[1].w[0]=0x3F800000;r.vf[2].w[0]=0x40000000;r.vf[4].w[0]=0x40800000;};
 bool ok=true;
 init(0);{
  vuops::FlagDispatch scope(vu::regs(1));std::int64_t escape=-1;vu::g_capture=&escape;
  vu1_0000000000020001(vu::regs(1),g_vu1_mem);vu::g_capture=nullptr;
  const auto &pipe=vuops::g_dispatch_flags;
  std::cout<<"dispatch Q: "<<std::hex<<vu::regs(1).q<<" pending "<<pipe.q_pending<<" clock/ready "<<std::dec<<pipe.t<<"/"<<pipe.q_ready<<"\n";
  ok=ok&&escape==0x80&&vu::regs(1).q==0x3F800000&&pipe.q_pending&&pipe.t<pipe.q_ready;
 }
 for(unsigned route=0;route<2;++route){
  const unsigned first=route?0x3F000000:0x3F800000,second=route?0x3E800000:0x3F000000;
  for(unsigned compiled=0;compiled<2;++compiled){
   init(route);if(compiled)vu::run(1,0);else vu::run_fast(1,0);
   const auto &r=vu::regs(1);
   std::cout<<(compiled?argv[2]:"interpreter")<<" route "<<route<<": "<<std::hex<<r.vf[3].w[0]<<","<<r.vf[5].w[0]<<" expected "<<first<<","<<second<<"\n";
   ok=ok&&r.vf[3].w[0]==first&&r.vf[5].w[0]==second;
  }
 }
 return ok?0:1;
}
'''
WASM = r'''
const fs=require('node:fs'),path=require('node:path'),dir=process.argv[2];
const o=JSON.parse(fs.readFileSync(path.join(dir,'offsets.json')));
const memory=new WebAssembly.Memory({initial:1,maximum:65536,shared:true}),v=new DataView(memory.buffer),r=0x3000,fl=0x1000;let escape=-1;
const runs=[0,1].map(part=>{
 const mod=new WebAssembly.Module(fs.readFileSync(path.join(dir,`${part}.wasm`))),env={memory};
 for(const imp of WebAssembly.Module.imports(mod))if(imp.kind==='function')env[imp.name]=()=>{throw Error(`unexpected import ${imp.name}`)};
 // Isolate JIT prologue ownership: the host dispatch itself preserves the pipe.
 env.interpret=(regs,pc)=>{escape=pc;};
 return new WebAssembly.Instance(mod,{env}).exports.run;
});
let ok=true;
for(let route=0;route<2;++route){
 new Uint8Array(memory.buffer,r,o.size).fill(0);new Uint8Array(memory.buffer,fl,o.pipeSize).fill(0);
 v.setUint32(fl+o.t,16,true);v.setUint16(r+o.vi+2,route,true);v.setUint16(r+o.vi+18,16,true);
 v.setUint32(r+o.q,0x3F800000,true);v.setUint32(r+o.vf+12,0x3F800000,true);
 for(const [reg,value]of [[1,0x3F800000],[2,0x40000000],[4,0x40800000]])v.setUint32(r+o.vf+reg*16,value,true);
 escape=-1;runs[0](r,0x4000);
 if(escape>=0){if(escape!==0x80)throw Error(`bad dispatch ${escape}`);runs[1](r,0x4000);}
 const a=v.getUint32(r+o.vf+3*16,true),b=v.getUint32(r+o.vf+5*16,true),first=route?0x3F000000:0x3F800000,second=route?0x3E800000:0x3F000000;
 console.log(`Wasm route ${route}: ${a.toString(16)},${b.toString(16)} expected ${first.toString(16)},${second.toString(16)}`);
 ok=ok&&a===first&&b===second;
}
process.exit(ok?0:1);
'''


def main():
    results = []
    with tempfile.TemporaryDirectory(prefix='eco-vu-q-') as temp:
        d = Path(temp)
        (d/'generator.cpp').write_text(GENERATOR)
        run('clang++','-std=c++20','-O2','-I.','-Iruntime/include',str(d/'generator.cpp'),'runtime/src/vu_jit.cpp','-o',str(d/'generator'))
        run(str(d/'generator'),str(d))
        run('cmake','-S',str(ROOT),'-B',str(d/'build'),'-DCMAKE_BUILD_TYPE=Release','-DPS2_WGPU_DIR=/nonexistent')
        run('cmake','--build',str(d/'build'),'--target','ps2runtime','-j','4')
        (d/'driver.cpp').write_text(DRIVER)
        run('clang++','-std=c++20','-O2','-I.','-Iruntime/include','-Iruntime/src',str(d/'driver.cpp'),str(d/'native.cpp'),str(d/'build/libps2runtime.a'),'-o',str(d/'native'))
        env = {k:v for k,v in os.environ.items() if not k.startswith('PS2_')}
        for mode in ('compiled','fallback'):
            results.append(subprocess.run([str(d/'native'),str(d/'code.bin'),mode],cwd=ROOT,env=env,timeout=900).returncode)
        (d/'wasm.cjs').write_text('try {\n'+WASM+'\n} catch(e) { console.error(e); process.exit(2); }')
        results.append(subprocess.run(['node',str(d/'wasm.cjs'),str(d)],cwd=ROOT,timeout=900).returncode)
    if any(code not in (0,1) for code in results):
        raise RuntimeError('reproducer failed to execute')
    return int(any(results))

if __name__ == '__main__':
    raise SystemExit(main())
