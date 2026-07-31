// Finds executable instructions that use the planet_building_capacity_add modifier ID.
// @category Stellaris

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.util.LinkedHashMap;
import java.util.Map;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.mem.MemoryBlock;

public class TraceBuildingCapacityId extends GhidraScript {
    private static final long MODIFIER_ID = 0x2a93;

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            throw new IllegalArgumentException("Expected one output report path");
        }

        Map<Address, Function> matches = new LinkedHashMap<>();
        byte[] needle = {(byte) 0x93, 0x2a, 0x00, 0x00};
        for (MemoryBlock block : currentProgram.getMemory().getBlocks()) {
            if (!block.isExecute()) continue;
            Address cursor = block.getStart();
            while (cursor != null && cursor.compareTo(block.getEnd()) <= 0) {
                Address match = currentProgram.getMemory().findBytes(
                    cursor, block.getEnd(), needle, null, true, monitor);
                if (match == null) break;
                Instruction instruction = getInstructionContaining(match);
                if (instruction != null) {
                    matches.put(
                        instruction.getAddress(),
                        getFunctionContaining(instruction.getAddress())
                    );
                }
                cursor = match.add(1);
            }
        }

        try (BufferedWriter writer = new BufferedWriter(new FileWriter(new File(args[0])))) {
            writer.write(String.format("modifier id: 0x%X\n", MODIFIER_ID));
            writer.write("instruction matches: " + matches.size() + "\n\n");
            DecompInterface decompiler = new DecompInterface();
            try {
                decompiler.openProgram(currentProgram);
                for (Map.Entry<Address, Function> entry : matches.entrySet()) {
                    Address address = entry.getKey();
                    Function function = entry.getValue();
                    Instruction instruction = getInstructionAt(address);
                    writer.write("=== " + address + " in " + describe(function) + " ===\n");
                    writer.write(bytesToHex(instruction.getBytes()) + "  " + instruction + "\n");
                    if (function != null) writeDecompilation(writer, decompiler, function);
                    writer.write("\n");
                }
            }
            finally {
                decompiler.dispose();
            }
        }
    }

    private void writeDecompilation(
            BufferedWriter writer, DecompInterface decompiler, Function function) throws Exception {
        DecompileResults result = decompiler.decompileFunction(function, 180, monitor);
        if (!result.decompileCompleted() || result.getDecompiledFunction() == null) {
            writer.write("Unavailable: " + result.getErrorMessage() + "\n");
        }
        else {
            writer.write(result.getDecompiledFunction().getC());
            writer.write("\n");
        }
    }

    private String bytesToHex(byte[] bytes) {
        StringBuilder result = new StringBuilder();
        for (byte value : bytes) result.append(String.format("%02X", value & 0xff));
        return result.toString();
    }

    private String describe(Function function) {
        return function == null
            ? "<no function>"
            : function.getName() + " @ " + function.getEntryPoint();
    }
}
