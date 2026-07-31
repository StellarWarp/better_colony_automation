// Decompiles queue count/capacity candidates and records their callers.
// @category Stellaris

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.util.LinkedHashSet;
import java.util.Set;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;

public class DecompileQueueCapacityCandidates extends GhidraScript {
    private static final String[] CANDIDATES = {
        "14082fcd0",
        "140830010",
        "14095a700",
        "14095ab10",
        "14095aba0",
        "14095ff50",
        "1409603a0",
        "140d1c480"
    };

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            throw new IllegalArgumentException("Expected one output report path");
        }

        Set<Function> functions = new LinkedHashSet<>();
        for (String address : CANDIDATES) {
            Function candidate = getFunctionAt(toAddr(address));
            if (candidate == null) continue;
            functions.add(candidate);
            for (Reference reference : getReferencesTo(candidate.getEntryPoint())) {
                Function caller = getFunctionContaining(reference.getFromAddress());
                if (caller != null) functions.add(caller);
            }
        }

        try (BufferedWriter writer = new BufferedWriter(new FileWriter(new File(args[0])))) {
            DecompInterface decompiler = new DecompInterface();
            try {
                decompiler.openProgram(currentProgram);
                for (Function function : functions) {
                    writer.write("=== " + function.getName() + " @ " +
                        function.getEntryPoint() + " ===\n");
                    writer.write("callers:\n");
                    for (Reference reference : getReferencesTo(function.getEntryPoint())) {
                        Function caller = getFunctionContaining(reference.getFromAddress());
                        if (caller != null) {
                            writer.write("  " + reference.getFromAddress() + " in " +
                                caller.getName() + " @ " + caller.getEntryPoint() + "\n");
                        }
                    }
                    DecompileResults result =
                        decompiler.decompileFunction(function, 180, monitor);
                    if (result.decompileCompleted() &&
                            result.getDecompiledFunction() != null) {
                        writer.write(result.getDecompiledFunction().getC());
                    }
                    else {
                        writer.write("Unavailable: " + result.getErrorMessage() + "\n");
                    }
                    writer.write("\n\n");
                }
            }
            finally {
                decompiler.dispose();
            }
        }
    }
}
