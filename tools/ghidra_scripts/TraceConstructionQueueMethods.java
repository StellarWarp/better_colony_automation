// Decompiles the function cluster around the confirmed construction queue updater.
// @category Stellaris

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.symbol.Reference;

public class TraceConstructionQueueMethods extends GhidraScript {
    private static final String START = "140802000";
    private static final String END = "140805000";

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            throw new IllegalArgumentException("Expected one output report path");
        }

        Address start = toAddr(START);
        Address end = toAddr(END);
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(new File(args[0])))) {
            DecompInterface decompiler = new DecompInterface();
            try {
                decompiler.openProgram(currentProgram);
                FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(start, true);
                while (functions.hasNext()) {
                    Function function = functions.next();
                    if (function.getEntryPoint().compareTo(end) >= 0) break;
                    writer.write("=== " + describe(function) + " ===\n");
                    writer.write("callers:\n");
                    for (Reference reference : getReferencesTo(function.getEntryPoint())) {
                        Function caller = getFunctionContaining(reference.getFromAddress());
                        if (caller != null) {
                            writer.write("  " + reference.getFromAddress() + " in " +
                                describe(caller) + "\n");
                        }
                    }
                    DecompileResults result =
                        decompiler.decompileFunction(function, 180, monitor);
                    if (!result.decompileCompleted() ||
                            result.getDecompiledFunction() == null) {
                        writer.write("Unavailable: " + result.getErrorMessage() + "\n\n");
                    }
                    else {
                        writer.write(result.getDecompiledFunction().getC());
                        writer.write("\n\n");
                    }
                }
            }
            finally {
                decompiler.dispose();
            }
        }
    }

    private String describe(Function function) {
        return function.getName() + " @ " + function.getEntryPoint();
    }
}
