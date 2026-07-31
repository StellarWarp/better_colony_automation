// Traces parser and validation functions for common/colony_automation.
// @category Stellaris

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.util.LinkedHashSet;
import java.util.Set;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;

public class TraceColonyAutomationDatabase extends GhidraScript {
    private static final String[] TARGETS = {
        "140466490", // CColonyAutomationDatabase loader
        "140467020", // parses individual colony-automation definitions
        "140467850", // automation key serialization / lookup helper
        "140468290"  // automation key serialization / lookup helper
    };

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) throw new IllegalArgumentException("Expected one output report path");
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(new File(args[0])))) {
            DecompInterface decompiler = new DecompInterface();
            try {
                decompiler.openProgram(currentProgram);
                for (String targetText : TARGETS) trace(writer, decompiler, toAddr(targetText));
            }
            finally { decompiler.dispose(); }
        }
    }

    private void trace(BufferedWriter writer, DecompInterface decompiler, Address address) throws Exception {
        Function target = getFunctionContaining(address);
        writer.write("=== " + describe(target) + " ===\n");
        if (target == null) {
            writer.write("No containing function found.\n\n");
            return;
        }
        writeDecompilation(writer, decompiler, target, "Target");
        Set<Function> callers = callersOf(target);
        writer.write("\nDirect callers (" + callers.size() + "):\n");
        for (Function caller : callers) writer.write("- " + describe(caller) + "\n");
        int count = 0;
        for (Function caller : callers) {
            if (count++ >= 10) break;
            writeDecompilation(writer, decompiler, caller, "Direct caller");
        }
        writer.write("\n\n");
    }

    private Set<Function> callersOf(Function target) {
        Set<Function> result = new LinkedHashSet<>();
        for (Reference reference : getReferencesTo(target.getEntryPoint())) {
            Function caller = getFunctionContaining(reference.getFromAddress());
            if (caller != null) result.add(caller);
        }
        return result;
    }

    private void writeDecompilation(BufferedWriter writer, DecompInterface decompiler, Function function, String heading) throws Exception {
        writer.write("\n--- " + heading + ": " + describe(function) + " ---\n");
        DecompileResults result = decompiler.decompileFunction(function, 180, monitor);
        if (!result.decompileCompleted() || result.getDecompiledFunction() == null) {
            writer.write("Unavailable: " + result.getErrorMessage() + "\n");
            return;
        }
        writer.write(result.getDecompiledFunction().getC());
        writer.write("\n");
    }

    private String describe(Function function) {
        return function == null ? "<no function>" : function.getName() + " @ " + function.getEntryPoint();
    }
}
