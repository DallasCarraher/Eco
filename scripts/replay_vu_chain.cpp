// Frozen-input adapter for the production whole-chain diagnostic and dispatcher.
// No game boot, live GS submission or model/API calls. Outputs stay ignored.
#include "../runtime/src/vu_micro.cpp"
#include <iostream>
void register_generated_vu();
int main(int argc, char** argv) {
    using namespace ps2;
    if (argc != 4 || (std::string(argv[3]) != "8192" && std::string(argv[3]) != "16384")) {
        std::cerr << "usage: replay_vu_chain INPUT_PREFIX NEW_OUTPUT_DIRECTORY 8192|16384\n";
        return 2;
    }
    setenv("PS2_VU_CHECK", "all", 1);
    setenv("PS2_VU_CHECK_CONTINUATIONS", argv[3], 1);
    const std::string input = argv[1];
    const std::filesystem::path output = argv[2];
    if (!std::filesystem::create_directory(output)) return 2;
    const auto load = [&](const char* suffix, void* dst, std::size_t size) {
        std::ifstream file(input + suffix, std::ios::binary);
        if (!file.read(static_cast<char*>(dst), size) || file.peek() != std::ifstream::traits_type::eof())
            throw std::runtime_error("invalid snapshot size");
    };
    const auto dump = [&](const char* suffix, const void* data, std::size_t size) {
        std::ofstream file(output / (std::string("live-") + suffix), std::ios::binary);
        if (!file || (size && !file.write(static_cast<const char*>(data), size)))
            throw std::runtime_error("output failure");
    };
    try {
        vu::reset();
        load("-code.bin", g_vu1_code, 16384);
        load("-before.bin", &vu::regs(1), sizeof(Vu0Regs));
        load("-memory.bin", g_vu1_mem, 16384);
        unsigned entry, top, itop; std::int64_t unused;
        if (!(std::ifstream(input + "-meta.txt") >> entry >> top >> itop >> unused) ||
            entry >= 16384 || (entry & 7u)) return 2;
        vu::set_tops(top, itop); vu::code_changed(1); register_generated_vu();
        vuops::FlagDispatch flags(vu::regs(1));
        load("-pipe.bin", &vuops::g_dispatch_flags, sizeof(vuops::FlagPipe));
        const auto clock = vuops::g_dispatch_flags.t;
        std::vector<std::uint8_t> packets;
        vu::g_reference_dry = true; vu::g_check_packets = &packets;
        // This is the same logical chain loop used by interpret(), with the
        // archived initial pipe installed inside its owning FlagDispatch.
        vu::run_chain(entry);
        const auto result = vu::g_last_chain_check;
        dump("regs.bin", &vu::regs(1), sizeof(Vu0Regs));
        dump("mem.bin", g_vu1_mem, 16384);
        dump("packets.bin", packets.data(), packets.size());
        const auto& pipe = vuops::g_dispatch_flags;
        std::ofstream semantic(output / "live-pipe.txt");
        semantic << pipe.t << ' ' << pipe.mh << ' ' << pipe.ch << ' ' << pipe.q_pending << ' ' << pipe.q_value << ' ' << pipe.q_ready << '\n';
        for (unsigned i=0; i<8; ++i)
            semantic << pipe.mac_ts[i] << ' ' << pipe.mac_v[i] << ' ' << pipe.status_v[i] << ' ' << pipe.clip_ts[i] << ' ' << pipe.clip_v[i] << '\n';
        const bool full = result.outcome == vu_checkpoint::Outcome::complete_match;
        std::ofstream status(output / "status.json");
        status << "{\"outcome\":\"" << vu_checkpoint::name(result.outcome) << "\",\"reason\":\"" << result.reason
               << "\",\"full_invocation_compared\":" << (full ? "true" : "false")
               << ",\"comparison_continuations\":" << result.continuations << ",\"compiled_issue_delta\":" << result.issued
               << ",\"checkpoints\":" << result.checkpoints << ",\"comparison_next_pc\":" << result.next_pc
               << ",\"live_issue_delta\":" << pipe.t-clock << ",\"live_tpc\":" << vu::regs(1).tpc
               << ",\"aggregate_continuation_limit\":" << argv[3] << "}\n";
        semantic.close(); status.close();
        if (!semantic || !status) throw std::runtime_error("output failure");
        vu::g_check_packets = nullptr;
        return full ? 0 : result.outcome == vu_checkpoint::Outcome::mismatch ? 1 : 4;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n'; return 2;
    }
}
