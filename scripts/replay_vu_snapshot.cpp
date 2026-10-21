// Standalone diagnostic using internal interpreter/capture state.
// Link the generated VU table object explicitly (the runtime has a weak stub).
// Inputs and outputs use the current host ABI; keep game-derived files local.
#include "../runtime/src/vu_micro.cpp"
#include <iostream>
void register_generated_vu();
int main(int argc, char **argv) {
    if (argc != 4 || (std::string(argv[2]) != "compiled" && std::string(argv[2]) != "interpreted")) {
        std::fputs("usage: replay_vu_snapshot <snapshot-prefix> <compiled|interpreted> <output-prefix>\n", stderr);
        return 2;
    }
    const std::string prefix = argv[1];
    const auto load = [&](const char *suffix, void *dst, std::size_t size) {
        if (!std::ifstream(prefix + suffix, std::ios::binary).read(static_cast<char *>(dst), size)) std::abort();
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
    // Older root snapshots predate persistent flag history and start fresh.
    if (std::filesystem::exists(prefix + "-pipe.bin"))
        load("-pipe.bin", &ps2::vuops::g_dispatch_flags, sizeof(ps2::vuops::FlagPipe));
    if (std::string(argv[2]) == "compiled") {
        auto fn = ps2::vu::lookup(pc);
        if (!fn) return 3;
        ps2::vu::g_capture = &actual_escape;
        fn(ps2::vu::regs(1), ps2::g_vu1_mem);
        for (unsigned segments=0; actual_escape>=0; ++segments) {
            if (segments>=8192) return 4;
            const auto next=static_cast<std::uint32_t>(actual_escape);
            actual_escape=-1;
            if (auto fn=ps2::vu::lookup(next)) fn(ps2::vu::regs(1),ps2::g_vu1_mem);
            else ps2::vu::run_fast(1,next);
        }
        ps2::vu::g_capture = nullptr;
    } else {
        ps2::vu::run_fast(1, pc);
    }
    std::cerr << "escape " << actual_escape << " expected " << expected_escape << "\n";
    std::ofstream(std::string(argv[3])+"-regs.bin", std::ios::binary).write(reinterpret_cast<char *>(&ps2::vu::regs(1)), sizeof(ps2::Vu0Regs));
    std::ofstream(std::string(argv[3])+"-mem.bin", std::ios::binary).write(reinterpret_cast<char *>(ps2::g_vu1_mem), 16384);
    std::ofstream(std::string(argv[3])+"-packets.bin", std::ios::binary).write(reinterpret_cast<char *>(packets.data()), packets.size());
}
