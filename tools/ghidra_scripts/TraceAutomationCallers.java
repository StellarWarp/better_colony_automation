// Traces callers around the queue-command path to locate colony automation scheduling.
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

public class TraceAutomationCallers extends GhidraScript {

    private static final String[] TARGETS = {
        "14070ad10",
        "140ad2ba0",
        "141e91430"
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
                    traceTarget(writer, decompiler, toAddr(target));
                }
            }
            finally {
                decompiler.dispose();
            }
        }
        println("Wrote report: " + report.getAbsolutePath());
    }

    private void traceTarget(BufferedWriter writer, DecompInterface decompiler, Address address) throws Exception {
        Function target = getFunctionContaining(address);
        writer.write("=== Target " + address + ": " + description(target) + " ===\n");
        if (target == null) {
            writer.write("No containing function found.\n\n");
            return;
        }

        writeDecompiler(writer, decompiler, target, "Target pseudocode");
        Set<Function> callers = callersOf(target);
        writer.write("\nDirect callers (" + callers.size() + "):\n");
        for (Function caller : callers) {
            writer.write("- " + description(caller) + "\n");
        }

        int written = 0;
        for (Function caller : callers) {
            if (written++ == 24) {
                writer.write("\nAdditional callers omitted.\n");
                break;
            }
            writeDecompiler(writer, decompiler, caller, "Direct caller pseudocode");
            Set<Function> grandparents = callersOf(caller);
            writer.write("\nCallers of " + description(caller) + " (" + grandparents.size() + "):\n");
            for (Function grandparent : grandparents) {
                writer.write("- " + description(grandparent) + "\n");
            }
        }
        writer.write("\n\n");
    }

    private Set<Function> callersOf(Function target) {
        Set<Function> callers = new LinkedHashSet<>();
        for (Reference reference : getReferencesTo(target.getEntryPoint())) {
            Function caller = getFunctionContaining(reference.getFromAddress());
            if (caller != null) {
                callers.add(caller);
            }
        }
        return callers;
    }

    private void writeDecompiler(BufferedWriter writer, DecompInterface decompiler, Function function, String heading)
            throws Exception {
        writer.write("\n--- " + heading + ": " + description(function) + " ---\n");
        DecompileResults result = decompiler.decompileFunction(function, 180, monitor);
        if (!result.decompileCompleted() || result.getDecompiledFunction() == null) {
            writer.write("Decompilation unavailable: " + result.getErrorMessage() + "\n");
            return;
        }
        writer.write(result.getDecompiledFunction().getC());
        writer.write("\n");
    }

    private String description(Function function) {
        return function == null ? "<no containing function>" : function.getName() + " @ " + function.getEntryPoint();
    }
}
