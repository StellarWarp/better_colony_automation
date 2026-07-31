// Finds construction UI/data-binding strings and decompiles their xref functions.
// @category Stellaris

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.symbol.Reference;

public class TraceConstructionUiStrings extends GhidraScript {
    private static final String[] NEEDLES = {
        "planet_build_queue_item_entry",
        "building_capacity",
        "BUILD_QUEUE"
    };

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            throw new IllegalArgumentException("Expected one output report path");
        }
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(new File(args[0])))) {
            DecompInterface decompiler = new DecompInterface();
            try {
                decompiler.openProgram(currentProgram);
                for (String needle : NEEDLES) {
                    trace(writer, decompiler, needle);
                }
            }
            finally {
                decompiler.dispose();
            }
        }
    }

    private void trace(
            BufferedWriter writer, DecompInterface decompiler, String needle) throws Exception {
        Memory memory = currentProgram.getMemory();
        byte[] bytes = needle.getBytes(StandardCharsets.US_ASCII);
        Address cursor = currentProgram.getMinAddress();
        Address end = currentProgram.getMaxAddress();
        Map<Address, Function> functions = new LinkedHashMap<>();
        writer.write("=== String: " + needle + " ===\n");

        while (cursor != null && cursor.compareTo(end) <= 0) {
            Address match = memory.findBytes(cursor, end, bytes, null, true, monitor);
            if (match == null) break;
            if (needle.equals("building_capacity") ||
                    isTerminatedMatch(memory, match, bytes.length)) {
                writer.write("match " + match + "\n");
                if (needle.equals("building_capacity")) {
                    writer.write("  context " + readPrintable(memory, match.subtract(48), 160) +
                        "\n");
                }
                for (Reference reference : getReferencesTo(match)) {
                    Function function = getFunctionContaining(reference.getFromAddress());
                    writer.write("  xref " + reference.getFromAddress() + " in " +
                        describe(function) + "\n");
                    if (function != null) {
                        functions.put(function.getEntryPoint(), function);
                    }
                }
            }
            cursor = match.add(1);
        }
        writer.write("\n");
        for (Function function : functions.values()) {
            writeDecompilation(writer, decompiler, function);
        }
    }

    private boolean isTerminatedMatch(Memory memory, Address match, int length) throws Exception {
        boolean left = match.equals(currentProgram.getMinAddress()) ||
            memory.getByte(match.subtract(1)) == 0;
        boolean right = memory.getByte(match.add(length)) == 0;
        return left && right;
    }

    private String readPrintable(Memory memory, Address start, int length) throws Exception {
        StringBuilder result = new StringBuilder();
        for (int index = 0; index < length; index++) {
            int value = memory.getByte(start.add(index)) & 0xff;
            result.append(value >= 0x20 && value < 0x7f ? (char)value : '.');
        }
        return result.toString();
    }

    private void writeDecompilation(
            BufferedWriter writer, DecompInterface decompiler, Function function)
            throws Exception {
        writer.write("--- " + describe(function) + " ---\n");
        DecompileResults result = decompiler.decompileFunction(function, 180, monitor);
        if (!result.decompileCompleted() || result.getDecompiledFunction() == null) {
            writer.write("Unavailable: " + result.getErrorMessage() + "\n\n");
            return;
        }
        writer.write(result.getDecompiledFunction().getC());
        writer.write("\n\n");
    }

    private String describe(Function function) {
        return function == null
            ? "<no function>"
            : function.getName() + " @ " + function.getEntryPoint();
    }
}
