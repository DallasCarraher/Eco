// Standalone diagnostic using internal interpreter/capture state.
// Link the generated VU table object explicitly (the runtime has a weak stub).
// Inputs and outputs use the current host ABI; keep game-derived files local.
#include "../runtime/src/vu_micro.cpp"
#include <iostream>
void register_generated_vu();
int main(int argc, char **argv) {
    if (argc < 4 || argc > 5) {
        std::fputs("usage: replay_vu_snapshot <input-prefix> <compiled|interpreted|compiled-prefix|interpreted-prefix> <output-prefix> [prefix-limit]\n", stderr);
        return 2;
    }
    const std::string prefix = argv[1], mode = argv[2], output = argv[3];
    const bool compiled = mode == "compiled" || mode == "compiled-prefix";
    if ((!compiled && mode != "interpreted" && mode != "interpreted-prefix") ||
        (mode == "interpreted-prefix" && argc != 5) ||
        (argc == 5 && mode != "compiled-prefix" && mode != "interpreted-prefix")) return 2;
    unsigned continuation_limit = 8192;
    ps2::vu::FastCheckpoint checkpoint;
    if (argc == 5) {
        char *end = nullptr;
        const auto value = std::strtoul(argv[4], &end, 10);
        if (!end || *end || !value || value >= 1'000'000) return 2;
        if (mode == "compiled-prefix") {
            if (value > 8192) return 2;
            continuation_limit = static_cast<unsigned>(value);
        } else checkpoint.limit = static_cast<std::uint32_t>(value);
    }
    const auto load = [&](const char *suffix, void *dst, std::size_t size) {
        if (!std::ifstream(prefix + suffix, std::ios::binary).read(static_cast<char *>(dst), size)) std::abort();
    };
    const auto dump = [&](const char *suffix, const void *data, std::size_t size) {
        std::ofstream file(output + suffix, std::ios::binary);
        if (!file || (size && !file.write(static_cast<const char *>(data), size))) std::abort();
    };
    ps2::vu::reset();
    load("-code.bin", ps2::g_vu1_code, 16384);
    load("-before.bin", &ps2::vu::regs(1), sizeof(ps2::Vu0Regs));
    load("-memory.bin", ps2::g_vu1_mem, 16384);
    unsigned pc = 0, top = 0, itop = 0;
    std::int64_t expected_escape = -1, actual_escape = -1;
    if (!(std::ifstream(prefix + "-meta.txt") >> pc >> top >> itop >> expected_escape)) return 2;
    ps2::vu::set_tops(top, itop);
    ps2::vu::code_changed(1);
    register_generated_vu();
    std::vector<std::uint8_t> packets;
    ps2::vu::g_check_packets = &packets;
    ps2::vu::g_reference_dry = true;
    ps2::vuops::FlagDispatch flags(ps2::vu::regs(1));
    if (std::filesystem::exists(prefix + "-pipe.bin"))
        load("-pipe.bin", &ps2::vuops::g_dispatch_flags, sizeof(ps2::vuops::FlagPipe));
    const auto initial_clock = ps2::vuops::g_dispatch_flags.t;
    unsigned continuations = 0;
    bool complete = false;
    bool fallback_incomplete = false;
    std::string reason;
    if (compiled) {
        auto fn = ps2::vu::lookup(pc);
        if (!fn) return 3;
        ps2::vu::g_capture = &actual_escape;
        fn(ps2::vu::regs(1), ps2::g_vu1_mem);
        while (actual_escape >= 0 && continuations < continuation_limit) {
            const auto next = static_cast<std::uint32_t>(actual_escape);
            actual_escape = -1;
            if (auto continuation = ps2::vu::lookup(next)) continuation(ps2::vu::regs(1), ps2::g_vu1_mem);
            else {
                // A negative capture alone is not proof that fallback ended:
                // run_fast also returns at its instruction ceiling.
                checkpoint = ps2::vu::FastCheckpoint{};
                const auto issued = ps2::vuops::g_dispatch_flags.t - initial_clock;
                if (issued >= 1'000'000) {
                    fallback_incomplete = true;
                    actual_escape = next;
                    break;
                }
                checkpoint.limit = 1'000'000 - issued;
                ps2::vu::g_fast_checkpoint = &checkpoint;
                ps2::vu::run_fast(1, next);
                ps2::vu::g_fast_checkpoint = nullptr;
                if (!checkpoint.complete) {
                    fallback_incomplete = true;
                    actual_escape = checkpoint.pc;
                }
            }
            ++continuations;
            if (fallback_incomplete) break;
        }
        ps2::vu::g_capture = nullptr;
        complete = actual_escape < 0 && !fallback_incomplete;
        reason = complete ? "complete" : fallback_incomplete ? "instruction_limit" : "continuation_limit";
        pc = complete ? ps2::vu::regs(1).tpc : static_cast<unsigned>(actual_escape);
    } else {
        ps2::vu::g_fast_checkpoint = &checkpoint;
        ps2::vu::run_fast(1, pc);
        ps2::vu::g_fast_checkpoint = nullptr;
        complete = checkpoint.complete;
        reason = complete ? "complete" : checkpoint.steps == checkpoint.limit ? "instruction_checkpoint" : "instruction_limit";
        pc = checkpoint.pc;
        dump("-branch.bin", &checkpoint, sizeof checkpoint);
    }
    const auto &pipe = ps2::vuops::g_dispatch_flags;
    dump("-regs.bin", &ps2::vu::regs(1), sizeof(ps2::Vu0Regs));
    dump("-mem.bin", ps2::g_vu1_mem, 16384);
    dump("-packets.bin", packets.data(), packets.size());
    dump("-pipe.bin", &pipe, sizeof pipe);
    // Text fields exclude padding from the semantic pipeline comparison.
    std::ofstream semantic(output + "-pipe.txt");
    semantic << pipe.t << ' ' << pipe.mh << ' ' << pipe.ch << ' ' << pipe.q_pending << ' ' << pipe.q_value << ' ' << pipe.q_ready << '\n';
    for (unsigned i=0;i<8;++i)
        semantic << pipe.mac_ts[i] << ' ' << pipe.mac_v[i] << ' ' << pipe.status_v[i] << ' ' << pipe.clip_ts[i] << ' ' << pipe.clip_v[i] << '\n';
    std::ofstream status(output + "-status.json");
    status << "{\"complete\":" << (complete ? "true" : "false") << ",\"reason\":\"" << reason
           << "\",\"next_pc\":" << pc << ",\"issue_clock_delta\":" << pipe.t-initial_clock
           << ",\"continuations\":" << continuations << ",\"steps\":" << checkpoint.steps
           << ",\"npc\":" << checkpoint.npc << ",\"ending\":" << (checkpoint.ending ? "true" : "false") << "}\n";
    std::cerr << reason << ": next PC " << pc << ", issued " << pipe.t-initial_clock << '\n';
    // Exit 4 is a preserved partial observation, never full-invocation agreement.
    return complete ? 0 : 4;
}
