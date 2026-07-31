// Traces callers and callees around planet construction scheduling candidates.
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

public class TraceConstructionScheduler extends GhidraScript {
    private static final String[] TARGETS = {
        "140c37890",
        "140b39900",
        "1408033bc"
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
                for (String targetAddress : TARGETS) {
                    traceTarget(writer, decompiler, toAddr(targetAddress));
                }
            }
            finally {
                decompiler.dispose();
            }
        }
    }

    private void traceTarget(
            BufferedWriter writer, DecompInterface decompiler, Address targetAddress)
            throws Exception {
        Function target = getFunctionContaining(targetAddress);
        writer.write("=== Target: " + describe(target) + " ===\n\n");
        writeDecompilation(writer, decompiler, target);

        Map<Address, Function> callers = new LinkedHashMap<>();
        writer.write("--- References to target ---\n");
        for (Reference reference : getReferencesTo(target.getEntryPoint())) {
            Address source = reference.getFromAddress();
            Function caller = getFunctionContaining(source);
            writer.write(source + " in " + describe(caller) +
                " [" + reference.getReferenceType() + "]\n");
            writeInstructionWindow(writer, source, 8, 10);
            writer.write("\n");
            if (caller != null) {
                callers.put(caller.getEntryPoint(), caller);
            }
        }

        writer.write("--- Direct callers ---\n\n");
        for (Function caller : callers.values()) {
            writeDecompilation(writer, decompiler, caller);
        }

        writer.write("--- Direct called functions ---\n\n");
        Map<Address, Function> callees = new LinkedHashMap<>();
        Instruction instruction = getInstructionAt(target.getEntryPoint());
        while (instruction != null && target.getBody().contains(instruction.getAddress())) {
            for (Reference reference : instruction.getReferencesFrom()) {
                if (!reference.getReferenceType().isCall()) {
                    continue;
                }
                Function callee = getFunctionAt(reference.getToAddress());
                if (callee != null) {
                    callees.put(callee.getEntryPoint(), callee);
                }
            }
            instruction = getInstructionAfter(instruction);
        }
        for (Function callee : callees.values()) {
            writer.write(describe(callee) + "\n");
        }
        writer.write("\n");
    }

    private void writeInstructionWindow(
            BufferedWriter writer, Address center, int before, int after) throws Exception {
        Instruction instruction = getInstructionContaining(center);
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
                "%s  %-28s  %s\n",
                current.getAddress(),
                bytesToHex(current.getBytes()),
                current
            ));
            current = getInstructionAfter(current);
        }
    }

    private void writeDecompilation(
            BufferedWriter writer, DecompInterface decompiler, Function function)
            throws Exception {
        if (function == null) {
            writer.write("<no function>\n\n");
            return;
        }
        writer.write("### " + describe(function) + "\n");
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
