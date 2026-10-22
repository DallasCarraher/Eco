// One bounded in-process comparison session. No game boot or durable resume.
#include "../runtime/src/vu_micro.cpp"
#include "vu_checkpoint.hpp"
#include <iostream>
void register_generated_vu();
int main(int argc,char**argv) {
    using namespace ps2;
    using namespace vu_checkpoint;
    if(argc!=4 && argc!=6) {std::cerr<<"usage: replay_vu_checkpoint INPUT_PREFIX NEW_OUTPUT_DIRECTORY CHUNK_CONTINUATIONS [--continuations 8192|16384]\n";return 2;}
    char* end=nullptr;const auto chunk=std::strtoul(argv[3],&end,10);
    if(!end || *end || chunk<1 || chunk>8192)return 2;
    unsigned aggregate_limit=8192;
    if(argc==6) {
        if(std::string(argv[4])!="--continuations")return 2;
        const auto value=std::strtoul(argv[5],&end,10);
        // Explicit diagnostic policies, never an unbounded arbitrary ceiling.
        // The production guard remains 8192 and the default is unchanged.
        if(!end || *end || (value!=8192 && value!=16384))return 2;
        aggregate_limit=static_cast<unsigned>(value);
    }
    const std::string input=argv[1];const std::filesystem::path output=argv[2];
    if(!std::filesystem::create_directory(output))return 2;
    auto load=[&](const char* suffix,void* dst,std::size_t size){
        std::ifstream f(input+suffix,std::ios::binary);
        if(!f.read(static_cast<char*>(dst),size) || f.peek()!=std::ifstream::traits_type::eof())throw std::runtime_error("invalid snapshot size");
    };
    try {
        vu::reset();load("-code.bin",g_vu1_code,16384);load("-before.bin",&vu::regs(1),sizeof(Vu0Regs));load("-memory.bin",g_vu1_mem,16384);
        unsigned entry,top,itop;std::int64_t unused;
        if(!(std::ifstream(input+"-meta.txt")>>entry>>top>>itop>>unused) || (entry&7u) || entry>=16384)return 2;
        vu::set_tops(top,itop);vu::code_changed(1);register_generated_vu();
        vuops::FlagDispatch flags(vu::regs(1));load("-pipe.bin",&vuops::g_dispatch_flags,sizeof(vuops::FlagPipe));
        Image initial;initial.save();Compiled compiled(initial,entry,aggregate_limit);Interpreter interpreted(initial);interpreted.entry=entry;
        std::ofstream checkpoints(output/"checkpoints.jsonl");
        if(!checkpoints)throw std::runtime_error("output failure");
        bool match=true;unsigned count=0;
        while(true) {
            compiled.advance(static_cast<unsigned>(chunk));
            if(compiled.stop==Compiled::Stop::unsupported_boundary || compiled.stop==Compiled::Stop::instruction_limit)break;
            if(!compiled.issued)break;
            interpreted.advance(compiled.issued);++count;
            match=equal(compiled.image,interpreted.image) && compiled.pc==interpreted.cursor.pc &&
                interpreted.cursor.steps==compiled.issued && compiled.complete==interpreted.cursor.complete &&
                interpreted.cursor.stop!=vu::FastStop::invalid_resume && interpreted.cursor.stop!=vu::FastStop::instruction_limit;
            checkpoints<<"{\"chunk\":"<<count<<",\"continuations\":"<<compiled.continuations<<",\"issued\":"<<compiled.issued
                <<",\"pc\":"<<compiled.pc<<",\"npc\":"<<interpreted.cursor.npc<<",\"ending\":"<<(interpreted.cursor.ending?"true":"false")
                <<",\"exact_match\":"<<(match?"true":"false")<<"}\n";checkpoints.flush();
            if(!checkpoints)throw std::runtime_error("output failure");
            if(!match || compiled.complete || compiled.stop==Compiled::Stop::continuation_limit)break;
        }
        checkpoints.close();
        if(!checkpoints)throw std::runtime_error("output failure");
        const bool supported=compiled.stop!=Compiled::Stop::unsupported_boundary && compiled.stop!=Compiled::Stop::instruction_limit;
        const bool full=match && supported && compiled.complete && interpreted.cursor.complete;
        const std::string state=!supported?"unsupported_or_instruction_limit":!match?"mismatch":full?"complete_match":"matched_partial";
        auto dump=[&](const std::string& name,const void* data,std::size_t size){std::ofstream f(output/name,std::ios::binary);if(size)f.write(static_cast<const char*>(data),size);f.close();if(!f)throw std::runtime_error("output failure");};
        auto image=[&](const std::string& name,const Image& v){
            dump(name+"-regs.bin",v.registers.data(),v.registers.size());dump(name+"-mem.bin",v.memory.data(),v.memory.size());dump(name+"-packets.bin",v.packets.data(),v.packets.size());
            std::ofstream pipe(output/(name+"-pipe.txt"));const auto &p=v.pipe;
            pipe<<p.t<<' '<<p.mh<<' '<<p.ch<<' '<<p.q_pending<<' '<<p.q_value<<' '<<p.q_ready<<'\n';
            for(unsigned i=0;i<8;++i)pipe<<p.mac_ts[i]<<' '<<p.mac_v[i]<<' '<<p.status_v[i]<<' '<<p.clip_ts[i]<<' '<<p.clip_v[i]<<'\n';
            pipe.close();if(!pipe)throw std::runtime_error("output failure");
        };
        image("compiled",compiled.image);image("interpreted",interpreted.image);
        std::ofstream status(output/"status.json");
        status<<"{\"state\":\""<<state<<"\",\"full_invocation_compared\":"<<(full?"true":"false")<<",\"chunks\":"<<count
            <<",\"continuations\":"<<compiled.continuations<<",\"issued\":"<<compiled.issued<<",\"next_pc\":"<<compiled.pc
            <<",\"aggregate_continuation_limit\":"<<aggregate_limit<<",\"aggregate_instruction_limit\":1000000}\n";
        status.close();if(!status)throw std::runtime_error("output failure");
        std::cout<<state<<": "<<count<<" checkpoints, "<<compiled.continuations<<" continuations, "<<compiled.issued<<" issued, PC "<<std::hex<<compiled.pc<<"\n";
        return full?0:match&&supported?4:1;
    } catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 2;}
}
