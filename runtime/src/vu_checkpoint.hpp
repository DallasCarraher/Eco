// Internal bounded-comparison implementation, included by vu_micro.cpp.
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
    explicit Context(Image& image, bool dry_run = true) {
        host.save(); image.install();
        vuops::g_dispatch_flags_active = true;
        vu::g_reference_dry = dry_run;
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
    void advance(unsigned chunk, bool live = false) {
        if (!chunk || complete || stop==Stop::unsupported_boundary || stop==Stop::instruction_limit) return;
        Context context(image, !live);
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
            // Coverage can exhaust its budget in a fragment which really ended.
            // Keep that live end state: production must not dispatch its end PC.
            if (issued>1'000'000 || (issued==1'000'000 && !complete)) {stop=Stop::instruction_limit;break;}
            stop=complete ? Stop::complete : Stop::checkpoint;
        }
        image.save();
    }
};

// Shared by the offline tool and production whole-chain diagnostic. No outcome
// implies hardware correctness, and partial/unsupported chains are never passes.
enum class Outcome { complete_match, mismatch, budget_exhausted, unsupported };
inline const char* name(Outcome outcome) {
    switch (outcome) {
    case Outcome::complete_match: return "complete_match";
    case Outcome::mismatch: return "mismatch";
    case Outcome::budget_exhausted: return "budget_exhausted";
    case Outcome::unsupported: return "unsupported";
    }
    return "unsupported";
}
struct Comparison {
    Compiled compiled;
    Interpreter interpreted;
    Outcome outcome = Outcome::unsupported;
    const char* reason = "not_started";
    unsigned checkpoints = 0;
    bool registers_equal = false, memory_equal = false, packets_equal = false;
    bool pipeline_equal = false, control_equal = false;
    Comparison(const Image& start, unsigned entry, unsigned ceiling = 8192)
        : compiled(start, entry, ceiling), interpreted(start) { interpreted.entry = entry; }
    void run(unsigned chunk = 256, bool live = false) {
        if (!chunk) { reason = "invalid_chunk"; return; }
        for (;;) {
            compiled.advance(chunk, live);
            if (compiled.stop == Compiled::Stop::unsupported_boundary) {
                outcome = Outcome::unsupported; reason = "missing_compiled_function"; return;
            }
            if (compiled.stop == Compiled::Stop::instruction_limit) {
                outcome = Outcome::budget_exhausted; reason = "compiled_instruction_limit"; return;
            }
            if (!compiled.issued) { outcome = Outcome::unsupported; reason = "empty_fragment"; return; }
            interpreted.advance(compiled.issued);
            if (interpreted.cursor.stop == vu::FastStop::invalid_resume) {
                outcome = Outcome::unsupported; reason = "invalid_interpreter_cursor"; return;
            }
            if (interpreted.cursor.stop == vu::FastStop::instruction_limit) {
                outcome = Outcome::budget_exhausted; reason = "interpreter_instruction_limit"; return;
            }
            ++checkpoints;
            registers_equal = compiled.image.registers == interpreted.image.registers;
            memory_equal = compiled.image.memory == interpreted.image.memory;
            packets_equal = compiled.image.packets == interpreted.image.packets;
            pipeline_equal = pipe_equal(compiled.image.pipe, interpreted.image.pipe);
            control_equal = compiled.pc == interpreted.cursor.pc && compiled.issued == interpreted.cursor.steps &&
                            compiled.complete == interpreted.cursor.complete;
            if (!(registers_equal && memory_equal && packets_equal && pipeline_equal && control_equal)) {
                outcome = Outcome::mismatch; reason = "endpoint_difference"; return;
            }
            if (compiled.complete) { outcome = Outcome::complete_match; reason = "invocation_end"; return; }
            if (compiled.stop == Compiled::Stop::continuation_limit) {
                outcome = Outcome::budget_exhausted; reason = "continuation_limit"; return;
            }
        }
    }
};
} // namespace vu_checkpoint
