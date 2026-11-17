// aff3ct_vec: bit-exact DVB-RCS2 turbo encoder vectors straight from the AFF3CT modules (no channel, no decoder).
//   usage: aff3ct_vec <out_dir> <seed> K:N [K:N ...]     K = encoder input bits (CRC included), N = coded bits
//   per case writes <out_dir>/lib_K<K>_N<N>.txt with lines "name: v v v ...":
//     lut, lut_inv     Interleaver_core_ARP_DVB_RCS2(K/2): lut[i] = (P i + Q(i mod 4) + 3) mod (K/2), lut_inv[lut[i]] = i
//     per frame f:     info_f (K-32 bits) -> crc_f (K bits, CRC_polynomial "32-GZIP" appended = encoder input)
//                      -> enc_f (3K bits, Encoder_turbo_DB) -> pct_f (N bits, Puncturer_turbo_DB)
//   frames: 0, 1 random (mt19937(seed + K)), 2 impulse (info[0] = 1), 3 all ones
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <string>
#include <vector>

#include <aff3ct.hpp>

using namespace aff3ct;
using B = int32_t;

template<typename T>
static void put(std::ofstream& f, const std::string& name, const std::vector<T>& v, size_t n)
{
    f << name << ":";
    for (size_t i = 0; i < n; i++)
        f << " " << +v[i];
    f << "\n";
}

int main(int argc, char** argv)
{
    if (argc < 4)
    {
        std::cerr << "usage: aff3ct_vec <out_dir> <seed> K:N [K:N ...]" << std::endl;
        return 2;
    }
    const std::string out = argv[1];
    const unsigned seed = (unsigned)std::stoul(argv[2]);
    int fails = 0;
    for (int a = 3; a < argc; a++)
    {
        const std::string kn = argv[a];
        const int K = std::stoi(kn.substr(0, kn.find(':')));
        const int N = std::stoi(kn.substr(kn.find(':') + 1));
        const int C = 32, Ki = K - C;
        const std::string path = out + "/lib_K" + std::to_string(K) + "_N" + std::to_string(N) + ".txt";
        try
        {
            tools::Interleaver_core_ARP_DVB_RCS2<uint32_t> core(K / 2);           // throws if K/2 not in its table
            module::Interleaver<B, uint32_t> itl(core);
            module::Encoder_RSC_DB<B> sub(K, 2 * K, "DVB-RCS2", true);
            module::Encoder_turbo_DB<B> enc(K, 3 * K, sub, sub, itl);
            module::Puncturer_turbo_DB<B, float> pct(K, N);
            module::CRC_polynomial<B> crc(Ki, "32-GZIP", C);

            std::ofstream f(path);
            f << "# aff3ct_vec K=" << K << " N=" << N << " couples=" << K / 2 << " crc=32-GZIP seed=" << seed << "\n";
            put(f, "lut", core.get_lut(), K / 2);
            put(f, "lut_inv", core.get_lut_inv(), K / 2);

            std::mt19937 rng(seed + (unsigned)K);
            std::bernoulli_distribution bit(0.5);
            for (int fr = 0; fr < 4; fr++)
            {
                std::vector<B> info(Ki, 0), U(K, 0), X(3 * K, 0), P(N, 0);
                for (int i = 0; i < Ki; i++)
                    info[i] = fr < 2 ? (B)bit(rng) : (fr == 3 ? 1 : (i == 0));
                crc.build(info.data(), U.data());
                enc.encode(U.data(), X.data());
                pct.puncture(X.data(), P.data());
                const std::string s = std::to_string(fr);
                put(f, "info_" + s, info, Ki);
                put(f, "crc_" + s, U, K);
                put(f, "enc_" + s, X, 3 * K);
                put(f, "pct_" + s, P, N);
            }
            std::cout << "wrote " << path << std::endl;
        }
        catch (const std::exception& e)
        {
            std::cout << "FAILED K=" << K << " N=" << N << ": " << e.what() << std::endl;
            fails++;
        }
    }
    return fails ? 1 : 0;
}
