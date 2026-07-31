// Finds functions that access both queue count (+0x2c) and capacity (+0x48).
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

public class TraceQueueCapacityField extends GhidraScript {
    private static class Matches {
        Function function;
        Map<Address, String> count = new LinkedHashMap<>();
        Map<Address, String> capacity = new LinkedHashMap<>();
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            throw new IllegalArgumentException("Expected one output report path");
        }

        Map<Address, Matches> matches = new LinkedHashMap<>();
        for (Instruction instruction : currentProgram.getListing().getInstructions(true)) {
            Function function = getFunctionContaining(instruction.getAddress());
            if (function == null) continue;
            String text = instruction.toString().toLowerCase();
            boolean count = hasDisplacement(text, "2c");
            boolean capacity = hasDisplacement(text, "48");
            if (!count && !capacity) continue;

            Matches entry = matches.computeIfAbsent(
                function.getEntryPoint(),
                ignored -> {
                    Matches value = new Matches();
                    value.function = function;
                    return value;
                }
            );
            if (count) entry.count.put(instruction.getAddress(), instruction.toString());
            if (capacity) {
                entry.capacity.put(instruction.getAddress(), instruction.toString());
            }
        }

        try (BufferedWriter writer = new BufferedWriter(new FileWriter(new File(args[0])))) {
            DecompInterface decompiler = new DecompInterface();
            try {
                decompiler.openProgram(currentProgram);
                int selected = 0;
                for (Matches entry : matches.values()) {
                    if (entry.count.isEmpty() || entry.capacity.isEmpty()) continue;
                    selected++;
                }
                writer.write("functions accessing both +0x2c and +0x48: " + selected + "\n\n");

                for (Matches entry : matches.values()) {
                    if (entry.count.isEmpty() || entry.capacity.isEmpty()) continue;
                    writer.write("=== " + describe(entry.function) + " ===\n");
                    writer.write("+0x2c instructions:\n");
                    writeInstructions(writer, entry.count);
                    writer.write("+0x48 instructions:\n");
                    writeInstructions(writer, entry.capacity);
                    writeDecompilation(writer, decompiler, entry.function);
                }
            }
            finally {
                decompiler.dispose();
            }
        }
    }

    private boolean hasDisplacement(String text, String hex) {
        return text.contains("+0x" + hex + "]") ||
            text.contains("+0x0" + hex + "]") ||
            text.contains(" + 0x" + hex);
    }

    private void writeInstructions(
            BufferedWriter writer, Map<Address, String> instructions) throws Exception {
        for (Map.Entry<Address, String> entry : instructions.entrySet()) {
            writer.write("  " + entry.getKey() + "  " + entry.getValue() + "\n");
        }
    }

    private void writeDecompilation(
            BufferedWriter writer, DecompInterface decompiler, Function function)
            throws Exception {
        DecompileResults result = decompiler.decompileFunction(function, 180, monitor);
        if (!result.decompileCompleted() || result.getDecompiledFunction() == null) {
            writer.write("Unavailable: " + result.getErrorMessage() + "\n\n");
            return;
        }
        writer.write(result.getDecompiledFunction().getC());
        writer.write("\n\n");
    }

    private String describe(Function function) {
        return function.getName() + " @ " + function.getEntryPoint();
    }
}
