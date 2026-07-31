// Traces the native colony-automation queue guard and building-capacity modifier registration.
// @category Stellaris

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.symbol.Reference;

public class TraceAutomationQueueCapacity extends GhidraScript {
    private static final String CAPACITY_MODIFIER = "planet_building_capacity_add";
    private static final String QUEUE_GUARD = "140e29300";

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
                traceQueueGuardCallSites(writer);
                traceModifierString(writer, decompiler);
            }
            finally {
                decompiler.dispose();
            }
        }
    }

    private void traceQueueGuardCallSites(BufferedWriter writer) throws Exception {
        Address target = toAddr(QUEUE_GUARD);
        writer.write("=== Queue guard call sites: " + target + " ===\n\n");
        for (Reference reference : getReferencesTo(target)) {
            Address source = reference.getFromAddress();
            Function caller = getFunctionContaining(source);
            writer.write("--- " + source + " in " + describe(caller) + " ---\n");
            writeInstructionWindow(writer, source, 10, 12);
            writer.write("\n");
        }
    }

    private void traceModifierString(BufferedWriter writer, DecompInterface decompiler)
            throws Exception {
        writer.write("=== Modifier string: " + CAPACITY_MODIFIER + " ===\n\n");
        Memory memory = currentProgram.getMemory();
        byte[] needle = CAPACITY_MODIFIER.getBytes(StandardCharsets.US_ASCII);
        Address cursor = currentProgram.getMinAddress();
        Address end = currentProgram.getMaxAddress();
        List<Function> decompiled = new ArrayList<>();

        while (cursor != null && cursor.compareTo(end) <= 0) {
            Address match = memory.findBytes(cursor, end, needle, null, true, monitor);
            if (match == null) {
                break;
            }
            writer.write("string address: " + match + "\n");
            for (Reference reference : getReferencesTo(match)) {
                Address source = reference.getFromAddress();
                Function function = getFunctionContaining(source);
                writer.write("xref " + source + " in " + describe(function) + "\n");
                writeInstructionWindow(writer, source, 8, 10);
                if (function != null && !decompiled.contains(function)) {
                    decompiled.add(function);
                    writeDecompilation(writer, decompiler, function);
                }
            }
            cursor = match.add(1);
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
            if (previous == null) {
                break;
            }
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
            writer.write("Unavailable: " + result.getErrorMessage() + "\n\n");
            return;
        }
        writer.write(result.getDecompiledFunction().getC());
        writer.write("\n\n");
    }

    private String bytesToHex(byte[] bytes) {
        StringBuilder result = new StringBuilder();
        for (byte value : bytes) {
            result.append(String.format("%02X", value & 0xff));
        }
        return result.toString();
    }

    private String describe(Function function) {
        return function == null
            ? "<no function>"
            : function.getName() + " @ " + function.getEntryPoint();
    }
}
