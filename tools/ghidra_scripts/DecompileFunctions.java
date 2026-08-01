// Decompiles functions supplied by address on the command line.
// @category Stellaris

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;

public class DecompileFunctions extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 2) {
            throw new IllegalArgumentException(
                "Expected output report path followed by one or more function addresses");
        }

        try (BufferedWriter writer = new BufferedWriter(new FileWriter(new File(args[0])))) {
            DecompInterface decompiler = new DecompInterface();
            try {
                decompiler.openProgram(currentProgram);
                writer.write("program: " + currentProgram.getName() + "\n");
                writer.write("MD5: " + currentProgram.getExecutableMD5() + "\n\n");
                for (int index = 1; index < args.length; index++) {
                    Address address = toAddr(args[index]);
                    Function function = getFunctionAt(address);
                    if (function == null) {
                        writer.write("=== no function at " + address + " ===\n\n");
                        continue;
                    }
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
