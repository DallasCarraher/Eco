// Diagnostic-only in-process state ownership. Include after vu_micro.cpp.
// Code/TOP/ITOP and registered functions must remain immutable for the session.
#pragma once
#include <array>
#include <algorithm>

namespace vu_checkpoint {
using namespace ps2;
struct Image {
    std::array<std::uint8_t, sizeof(Vu0Regs)> registers{};
    std::array<std::uint8_t, 16384> memory{};
    vuops::FlagPipe pipe;
    std::vector<std::uint8_t> packets;
    void save() {
        std::memcpy(registers.data(), &vu::regs(1), registers.size());
        std::memcpy(memory.data(), g_vu1_mem, memory.size());
        std::memcpy(&pipe, &vuops::g_dispatch_flags, sizeof pipe);
    }
    void install() const {
        std::memcpy(&vu::regs(1), registers.data(), registers.size());
        std::memcpy(g_vu1_mem, memory.data(), memory.size());
        std::memcpy(&vuops::g_dispatch_flags, &pipe, sizeof pipe);
    }
};
// Preserve the host context, including on errors; each path owns its own image.
struct Context {
    Image host;
    bool active = vuops::g_dispatch_flags_active;
    bool dry = vu::g_reference_dry;
    std::vector<std::uint8_t>* packets = vu::g_check_packets;
    std::int64_t* capture = vu::g_capture;
    vu::FastCheckpoint* point = vu::g_fast_checkpoint;
    explicit Context(Image& image) {
        host.save(); image.install();
        vuops::g_dispatch_flags_active = true;
        vu::g_reference_dry = true;
        vu::g_check_packets = &image.packets;
        vu::g_capture = nullptr;
        vu::g_fast_checkpoint = nullptr;
    }
    ~Context() {
        host.install(); vuops::g_dispatch_flags_active = active;
        vu::g_reference_dry = dry; vu::g_check_packets = packets;
        vu::g_capture = capture; vu::g_fast_checkpoint = point;
    }
};
inline bool pipe_equal(const vuops::FlagPipe& a, const vuops::FlagPipe& b) {
    if (a.t!=b.t || a.mh!=b.mh || a.ch!=b.ch || a.q_pending!=b.q_pending ||
        a.q_value!=b.q_value || a.q_ready!=b.q_ready) return false;
    for (unsigned i=0;i<8;++i)
        if (a.mac_ts[i]!=b.mac_ts[i] || a.mac_v[i]!=b.mac_v[i] ||
            a.status_v[i]!=b.status_v[i] || a.clip_ts[i]!=b.clip_ts[i] ||
            a.clip_v[i]!=b.clip_v[i]) return false;
    return true;
}
inline bool equal(const Image& a, const Image& b) {
    return a.registers==b.registers && a.memory==b.memory &&
           a.packets==b.packets && pipe_equal(a.pipe,b.pipe);
}
struct Interpreter {
    Image image;
    vu::FastCheckpoint cursor;
    explicit Interpreter(const Image& start): image(start) {}
    void advance(unsigned cumulative_instructions) {
        Context context(image);
        cursor.limit = cumulative_instructions;
        vu::g_fast_checkpoint = &cursor;
        vu::run_fast(1, cursor.resume ? cursor.pc : entry);
        image.save();
    }
    unsigned entry = 0;
};
// Only existing function-return boundaries are supported. No mid-fragment
// capture or fallback is implied. The production limit is not changed.
struct Compiled {
    Image image;
    unsigned pc, continuations = 0, issued = 0;
    bool started = false, complete = false;
    const unsigned aggregate_limit;
    enum class Stop { checkpoint, complete, continuation_limit, instruction_limit, unsupported_boundary };
    Stop stop = Stop::checkpoint;
    explicit Compiled(const Image& start, unsigned entry, unsigned ceiling = 8192)
        : image(start), pc(entry), aggregate_limit(ceiling) {}
    void advance(unsigned chunk) {
        if (!chunk || complete || stop==Stop::unsupported_boundary || stop==Stop::instruction_limit) return;
        Context context(image);
        unsigned used=0;
        while (!complete) {
            if (started && continuations>=aggregate_limit) {stop=Stop::continuation_limit;break;}
            if (started && used>=chunk) {stop=Stop::checkpoint;break;}
            auto fn=vu::lookup(pc);
            if (!fn) {stop=Stop::unsupported_boundary;break;}
            std::int64_t escape=-1;
            vu::g_capture=&escape;
            const auto before=vuops::g_dispatch_flags.t;
            fn(vu::regs(1),g_vu1_mem);
            vu::g_capture=nullptr;
            issued+=vuops::g_dispatch_flags.t-before;
            if (started) {++continuations;++used;}
            started=true;
            complete=escape<0;
            pc=complete ? vu::regs(1).tpc : static_cast<unsigned>(escape);
            if (issued>1'000'000 || (issued==1'000'000 && !complete)) {stop=Stop::instruction_limit;complete=false;break;}
            stop=complete ? Stop::complete : Stop::checkpoint;
        }
        image.save();
    }
};
} // namespace vu_checkpoint
