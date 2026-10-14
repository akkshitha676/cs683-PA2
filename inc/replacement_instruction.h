#ifndef TASK2A_REPLACEMENT_INSTRUCTION_H
#define TASK2A_REPLACEMENT_INSTRUCTION_H

#include "cache.h"

// An L2 miss originally issued for data can acquire an instruction consumer
// while in flight. The merged/fill flags preserve that consumer's evidence.
inline uint8_t replacement_instruction_flag(uint8_t cache_type,
                                            const PACKET &packet)
{
    if (cache_type != IS_L2C)
        return packet.instruction;

    // Instruction translations refer to page-table entries, not code bytes.
    // RFO can contain code bytes when an instruction request merges into it.
    if (packet.type != LOAD && packet.type != PREFETCH && packet.type != RFO)
        return 0;

    return packet.instruction || packet.instr_merged || packet.fill_l1i;
}

#endif
