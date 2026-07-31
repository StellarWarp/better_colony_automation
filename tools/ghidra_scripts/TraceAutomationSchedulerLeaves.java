// Decompiles the construction-selection leaves reached from the colony automation scheduler.
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

public class TraceAutomationSchedulerLeaves extends GhidraScript {
    private static final String[] TARGETS = {
        "140ee8ab0", "140ee8e70", "140ee9be0", "140ee9e80", "140ee64b0", "140ee6580",
        "140e29300", "140eea070", "140eea300", "140eea580", "140eea810", "140eeaa90", "140eead20",
        "140eeafb0", "140803810", "140eeb150", "140ee6d80", "14073b350", "14015a4a0"
    };

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) throw new IllegalArgumentException("Expected one output report path");
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(new File(args[0])))) {
            DecompInterface decompiler = new DecompInterface();
            try {
                decompiler.openProgram(currentProgram);
                for (String text : TARGETS) trace(writer, decompiler, toAddr(text));
            } finally { decompiler.dispose(); }
        }
    }

    private void trace(BufferedWriter writer, DecompInterface decompiler, Address address) throws Exception {
        Function target = getFunctionContaining(address);
        writer.write("=== " + describe(target) + " ===\n");
        if (target == null) { writer.write("Not found.\n\n"); return; }
        writeCode(writer, decompiler, target, "Target");
        Set<Function> callers = new LinkedHashSet<>();
        for (Reference reference : getReferencesTo(target.getEntryPoint())) {
            Function caller = getFunctionContaining(reference.getFromAddress());
            if (caller != null) callers.add(caller);
        }
        writer.write("\nDirect callers (" + callers.size() + "):\n");
        for (Function caller : callers) writer.write("- " + describe(caller) + "\n");
        writer.write("\n\n");
    }

    private void writeCode(BufferedWriter writer, DecompInterface decompiler, Function function, String label) throws Exception {
        writer.write("\n--- " + label + ": " + describe(function) + " ---\n");
        DecompileResults result = decompiler.decompileFunction(function, 180, monitor);
        if (!result.decompileCompleted() || result.getDecompiledFunction() == null) writer.write("Unavailable: " + result.getErrorMessage() + "\n");
        else writer.write(result.getDecompiledFunction().getC() + "\n");
    }

    private String describe(Function function) { return function == null ? "<no function>" : function.getName() + " @ " + function.getEntryPoint(); }
}
