// Extracts queue-execution functions and their direct callers into a report.
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

public class TraceQueueExecution extends GhidraScript {

    private static final String[] TARGETS = {
        "140b392f0", // CAddBuildableToQueueCommand execution path
        "140803a30"  // Called by the command to perform queue work
    };

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            throw new IllegalArgumentException("Expected one output report path");
        }

        File report = new File(args[0]);
        File parent = report.getParentFile();
        if (parent != null && !parent.exists() && !parent.mkdirs()) {
            throw new IllegalStateException("Could not create report directory: " + parent);
        }

        try (BufferedWriter writer = new BufferedWriter(new FileWriter(report))) {
            DecompInterface decompiler = new DecompInterface();
            try {
                decompiler.openProgram(currentProgram);
                for (String target : TARGETS) {
                    writeTargetReport(writer, decompiler, toAddr(target));
                }
            }
            finally {
                decompiler.dispose();
            }
        }
        println("Wrote report: " + report.getAbsolutePath());
    }

    private void writeTargetReport(BufferedWriter writer, DecompInterface decompiler, Address address) throws Exception {
        Function target = getFunctionContaining(address);
        writer.write("=== Target " + address + " ===\n");
        if (target == null) {
            writer.write("No containing function found.\n\n");
            return;
        }

        writer.write("Function: " + target.getName() + " @ " + target.getEntryPoint() + "\n");
        writer.write("Direct callers:\n");

        Set<Function> callers = new LinkedHashSet<>();
        for (Reference reference : getReferencesTo(target.getEntryPoint())) {
            Function caller = getFunctionContaining(reference.getFromAddress());
            writer.write("- " + reference.getFromAddress() + " in " + functionDescription(caller) + "\n");
            if (caller != null) {
                callers.add(caller);
            }
        }

        writeDecompilation(writer, decompiler, target, "Target pseudocode");
        int callerCount = 0;
        for (Function caller : callers) {
            if (callerCount++ == 12) {
                writer.write("\nAdditional callers omitted.\n");
                break;
            }
            writeDecompilation(writer, decompiler, caller, "Caller pseudocode");
        }
        writer.write("\n");
    }

    private void writeDecompilation(BufferedWriter writer, DecompInterface decompiler, Function function, String heading)
            throws Exception {
        writer.write("\n--- " + heading + ": " + functionDescription(function) + " ---\n");
        DecompileResults result = decompiler.decompileFunction(function, 120, monitor);
        if (!result.decompileCompleted() || result.getDecompiledFunction() == null) {
            writer.write("Decompilation unavailable: " + result.getErrorMessage() + "\n");
            return;
        }
        writer.write(result.getDecompiledFunction().getC());
        writer.write("\n");
    }

    private String functionDescription(Function function) {
        return function == null ? "<no containing function>" : function.getName() + " @ " + function.getEntryPoint();
    }
}
