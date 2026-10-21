#!/usr/bin/env python3
"""Original issue-4 reproducer. Exit 1 means the known native/Wasm bug persists.

Requires CMake, a C++20 compiler with std::format, and Node with Wasm tail calls.
No game data. All builds/output are private temporary directories.
Expected FSAND results are (0, 2): the negative SUB's status becomes visible
four issue cycles later, across a register jump. See docs/ISSUE4-VU.md.
"""
import argparse
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
    Program p{0x10001,0,std::vector<std::uint8_t>(16384)};
    const auto put=[&](unsigned pc, unsigned lo, unsigned hi=0x2FF) {
        std::memcpy(p.code.data()+pc,&lo,4); std::memcpy(p.code.data()+pc+4,&hi,4);
    };
    const unsigned nop=0x8000033C;
    // JR vi9; its delay slot computes SUB.x vf3, vf1, vf2 (1 - 2).
    put(0,(0x24u<<25)|(9u<<11));
    put(8,nop,(8u<<21)|(2u<<16)|(1u<<11)|(3u<<6)|0x2Cu);
    put(0x80,nop); put(0x88,nop);
    put(0x90,(0x16u<<25)|(1u<<16)|2u);
    put(0x98,(0x16u<<25)|(2u<<16)|2u,0x400002FF);
    put(0xA0,nop);
    std::ofstream(out/"code.bin",std::ios::binary).write((char*)p.code.data(),p.code.size());
    std::ofstream native(out/"native.cpp");
    native << "#include \"ps2/vu_ops.hpp\"\nusing namespace ps2; using namespace ps2::vuops;\n";
    for(int i=0;i<2;++i) {
        p.key=0x10001+i; p.entry=i?0x80:0;
        std::string name; native << generate(p,name);
        std::vector<std::uint8_t> wasm;
        if(!ps2::vu::jit::translate(p.code.data(),p.entry,{0x1000},wasm)) return 2;
        std::ofstream(out/std::format("{}.wasm",i),std::ios::binary).write((char*)wasm.data(),wasm.size());
    }
    std::ofstream(out/"offsets.json") << std::format("{{\"vi\":{},\"vf\":{}}}",offsetof(ps2::Vu0Regs,vi),offsetof(ps2::Vu0Regs,vf));
    std::ofstream(out/"pipe.json") << std::format("{{\"t\":{},\"mh\":{},\"ts\":{},\"status\":{}}}",offsetof(ps2::vuops::FlagPipe,t),offsetof(ps2::vuops::FlagPipe,mh),offsetof(ps2::vuops::FlagPipe,mac_ts),offsetof(ps2::vuops::FlagPipe,status_v));
}
'''
DRIVER = r'''
#include "runtime/src/vu_micro.cpp"
#include <iostream>
void vu1_0000000000010001(ps2::Vu0Regs&,std::uint8_t*);
void vu1_0000000000010002(ps2::Vu0Regs&,std::uint8_t*);
int main(int argc,char **argv) {
 using namespace ps2;
 std::ifstream(argv[1],std::ios::binary).read((char*)g_vu1_code,16384);
 auto init=[] {vu::reset(); std::memset(g_vu1_mem,0,16384);auto &r=vu::regs(1);r.vi[9]=0x10;r.vf[1].w[0]=0x3F800000;r.vf[2].w[0]=0x40000000;};
 init();vu::code_changed(1);vu::run_fast(1,0);
 auto &r=vu::regs(1);
 std::cout<<"continuous interpreter: "<<r.vi[1]<<","<<r.vi[2]<<" (expected 0,2)\n";
 bool ok=r.vi[1]==0&&r.vi[2]==2;
 init(); std::int64_t escape=-1;vu::g_capture=&escape;
 vu1_0000000000010001(r,g_vu1_mem);vu::g_capture=nullptr;
 if(escape!=0x80) return 2;
 vu1_0000000000010002(r,g_vu1_mem);
 std::cout<<"native dispatch: "<<r.vi[1]<<","<<r.vi[2]<<" (expected 0,2)\n";
 return ok&&r.vi[1]==0&&r.vi[2]==2?0:1;
}
'''
WASM = r'''
const fs=require('node:fs'),path=require('node:path');const dir=process.argv[2];
const pipe=JSON.parse(fs.readFileSync(path.join(dir,'pipe.json')));
const off=JSON.parse(fs.readFileSync(path.join(dir,'offsets.json')));
const memory=new WebAssembly.Memory({initial:1,maximum:65536,shared:true});
const v=new DataView(memory.buffer),r=0x3000;let escape=-1;
v.setUint16(r+off.vi+18,0x10,true);
v.setUint32(r+off.vf+12,0x3F800000,true);
v.setUint32(r+off.vf+16,0x3F800000,true);v.setUint32(r+off.vf+32,0x40000000,true);
for(let i=0;i<2;++i){
 const mod=new WebAssembly.Module(fs.readFileSync(path.join(dir,`${i}.wasm`)));
 const env={memory};for(const imp of WebAssembly.Module.imports(mod)){
  if(imp.kind!=='function')continue;
  env[imp.name]=()=>{throw Error(`unexpected import ${imp.name}`)};
 }
 // The JIT's dispatch helper reports the next micro PC.
 env.interpret=(unit,pc)=>{escape=pc;};
 env.status=(fl)=>{
  const t=v.getUint32(fl+pipe.t,true),mh=v.getUint32(fl+pipe.mh,true);
  for(let k=1;k<=8;++k){const i=(mh-k)&7;
   if(v.getUint32(fl+pipe.ts+4*i,true)+4<=t)return v.getUint32(fl+pipe.status+4*i,true);
  }
  return v.getUint32(fl+pipe.status+4*((mh-8)&7),true);
 };
 const inst=new WebAssembly.Instance(mod,{env});inst.exports.run(r,0x4000);
 if(i===0 && escape!==0x80)throw Error(`unexpected dispatch ${escape}`);
}
const a=v.getUint16(r+off.vi+2,true),b=v.getUint16(r+off.vi+4,true);
console.log(`Wasm dispatch: ${a},${b} (expected 0,2)`);process.exit(a===0&&b===2?0:1);
'''

def run(*args):
    return subprocess.run(args, cwd=ROOT, check=True, timeout=900)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--force-native-flags', action='store_true',
                        help='diagnostic intervention: force native flag writes, retaining the same expected reads')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='eco-vu-dispatch-') as directory:
        d=pathlib.Path(directory)
        generator = GENERATOR
        if args.force_native_flags:
            source = (ROOT/'recomp/vurecomp.cpp').read_text()
            old = 'upper(hi, any_status ? true : (any_flags && out_live))'
            if source.count(old) != 1:
                raise RuntimeError('producer intervention no longer matches code generator')
            (d/'forced.cpp').write_text(source.replace(old, 'upper(hi, true)'))
            generator = generator.replace('#include "recomp/vurecomp.cpp"',
                                          '#include "'+str(d/'forced.cpp')+'"')
        (d/'generator.cpp').write_text(generator)
        run('clang++','-std=c++20','-O2','-I.','-Iruntime/include',str(d/'generator.cpp'),'runtime/src/vu_jit.cpp','-o',str(d/'generator'))
        run(str(d/'generator'),str(d))
        run('cmake','-S',str(ROOT),'-B',str(d/'build'),'-DCMAKE_BUILD_TYPE=Release','-DPS2_WGPU_DIR=/nonexistent')
        run('cmake','--build',str(d/'build'),'--target','ps2runtime','-j','4')
        (d/'driver.cpp').write_text(DRIVER)
        run('clang++','-std=c++20','-O2','-I.','-Iruntime/include','-Iruntime/src',str(d/'driver.cpp'),str(d/'native.cpp'),str(d/'build/libps2runtime.a'),'-o',str(d/'native'))
        native=subprocess.run([str(d/'native'),str(d/'code.bin')],cwd=ROOT,timeout=900).returncode
        (d/'wasm.cjs').write_text('try {\n'+WASM+'\n} catch (e) { console.error(e); process.exit(2); }')
        wasm=subprocess.run(['node',str(d/'wasm.cjs'),str(d)],cwd=ROOT,timeout=900).returncode
        if native not in (0,1) or wasm not in (0,1):
            raise RuntimeError('reproducer failed to execute')
        return int(bool(native or wasm))

if __name__=='__main__':
    raise SystemExit(main())
