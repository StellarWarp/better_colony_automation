// Traces code references to the registered planet_building_capacity_add modifier object.
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
import ghidra.program.model.symbol.Reference;

public class TraceBuildingCapacityStorage extends GhidraScript {
    private static final String STORAGE_ADDRESS = "14342a670";
    private static final int STORAGE_SIZE = 0x120;

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            throw new IllegalArgumentException("Expected one output report path");
        }

        try (BufferedWriter writer = new BufferedWriter(new FileWriter(new File(args[0])))) {
            Address storage = toAddr(STORAGE_ADDRESS);
            Map<Address, Function> sources = new LinkedHashMap<>();
            for (int offset = 0; offset < STORAGE_SIZE; offset++) {
                Address field = storage.add(offset);
                for (Reference reference : getReferencesTo(field)) {
                    Address source = reference.getFromAddress();
                    sources.put(source, getFunctionContaining(source));
                }
            }

            writer.write("storage: " + storage + "\n");
            writer.write("code/data references: " + sources.size() + "\n\n");
            DecompInterface decompiler = new DecompInterface();
            try {
                decompiler.openProgram(currentProgram);
                for (Map.Entry<Address, Function> entry : sources.entrySet()) {
                    Address source = entry.getKey();
                    Function function = entry.getValue();
                    writer.write("=== " + source + " in " + describe(function) + " ===\n");
                    writeInstructionWindow(writer, source, 8, 10);
                    if (function != null && !function.getEntryPoint().equals(toAddr("140173c30"))) {
                        writeDecompilation(writer, decompiler, function);
                    }
                    writer.write("\n");
                }
            }
            finally {
                decompiler.dispose();
            }
        }
    }

    private void writeInstructionWindow(
            BufferedWriter writer, Address center, int before, int after) throws Exception {
        Instruction instruction = getInstructionAt(center);
        if (instruction == null) {
            instruction = getInstructionContaining(center);
        }
        if (instruction == null) {
            writer.write("No instruction at " + center + "\n");
            return;
        }
        Instruction start = instruction;
        for (int index = 0; index < before; index++) {
            Instruction previous = getInstructionBefore(start);
            if (previous == null) break;
            start = previous;
        }
        Instruction current = start;
        for (int index = 0; current != null && index <= before + after; index++) {
            writer.write(String.format(
                "%s  %-30s  %s\n",
                current.getAddress(),
                bytesToHex(current.getBytes()),
                current.toString()
            ));
            current = getInstructionAfter(current);
        }
    }

    private void writeDecompilation(
            BufferedWriter writer, DecompInterface decompiler, Function function) throws Exception {
        writer.write("\n--- Decompilation: " + describe(function) + " ---\n");
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
