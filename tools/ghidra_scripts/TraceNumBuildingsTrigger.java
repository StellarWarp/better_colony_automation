// Finds the num_buildings trigger vtable from a known method and decompiles its methods.
// @category Stellaris

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashSet;
import java.util.Set;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.symbol.Reference;

public class TraceNumBuildingsTrigger extends GhidraScript {
    private static final int MAX_VTABLE_METHODS = 48;
    private static final int MAX_VTABLE_SEARCH_SLOTS = 256;
    private static final byte[] ERROR_TEXT = (
        "num_buildings doesn't support both 'any' building and in_construction 'yes' or 'any'.")
        .getBytes(StandardCharsets.US_ASCII);
    private final Set<Function> nearbyFunctions = new LinkedHashSet<>();

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            throw new IllegalArgumentException("Expected one output report path");
        }

        Address errorText = findBytes(ERROR_TEXT);
        if (errorText == null) {
            throw new IllegalArgumentException("num_buildings validation error text not found");
        }
        Function validator = findReferencingFunction(errorText);
        if (validator == null) {
            throw new IllegalArgumentException(
                "No function references validation error text at " + errorText);
        }

        try (BufferedWriter writer = new BufferedWriter(new FileWriter(new File(args[0])))) {
            writer.write("program: " + currentProgram.getName() + "\n");
            writer.write("MD5: " + currentProgram.getExecutableMD5() + "\n");
            writer.write("error text: " + errorText + "\n");
            writer.write("validator: " + describe(validator) + "\n\n");

            Set<Address> vtables = findContainingVtables(validator.getEntryPoint(), writer);
            DecompInterface decompiler = new DecompInterface();
            try {
                decompiler.openProgram(currentProgram);
                writeFunction(writer, decompiler, validator);
                for (Address vtable : vtables) {
                    writeVtable(writer, decompiler, vtable);
                }
                writer.write("=== nearby callback candidates ===\n\n");
                for (Function function : nearbyFunctions) {
                    if (!function.equals(validator)) {
                        writeFunction(writer, decompiler, function);
                    }
                }
                writer.write("=== local helper callees ===\n\n");
                Set<Function> localHelpers = new LinkedHashSet<>();
                long validatorOffset = validator.getEntryPoint().getOffset();
                for (Function function : nearbyFunctions) {
                    for (Function called : function.getCalledFunctions(monitor)) {
                        long distance = Math.abs(
                            called.getEntryPoint().getOffset() - validatorOffset);
                        if (distance <= 0x10000) localHelpers.add(called);
                    }
                }
                for (Function function : localHelpers) {
                    if (!nearbyFunctions.contains(function) && !function.equals(validator)) {
                        writeFunction(writer, decompiler, function);
                    }
                }
                writer.write("=== counting helper callees ===\n\n");
                Set<Function> countingHelpers = new LinkedHashSet<>();
                for (Function function : localHelpers) {
                    countingHelpers.addAll(function.getCalledFunctions(monitor));
                }
                for (Function function : countingHelpers) {
                    if (!nearbyFunctions.contains(function) &&
                            !localHelpers.contains(function) &&
                            !function.equals(validator)) {
                        writeFunction(writer, decompiler, function);
                    }
                }
            }
            finally {
                decompiler.dispose();
            }
        }
    }

    private Address findBytes(byte[] needle) throws Exception {
        Memory memory = currentProgram.getMemory();
        for (ghidra.program.model.mem.MemoryBlock block : memory.getBlocks()) {
            if (block.isExecute() || block.getSize() > Integer.MAX_VALUE) continue;
            byte[] bytes = new byte[(int)block.getSize()];
            memory.getBytes(block.getStart(), bytes);
            outer:
            for (int index = 0; index <= bytes.length - needle.length; index++) {
                for (int offset = 0; offset < needle.length; offset++) {
                    if (bytes[index + offset] != needle[offset]) continue outer;
                }
                return block.getStart().add(index);
            }
        }
        return null;
    }

    private Function findReferencingFunction(Address target) throws Exception {
        for (Reference reference : getReferencesTo(target)) {
            Function function = getFunctionContaining(reference.getFromAddress());
            if (function != null) return function;
        }

        Memory memory = currentProgram.getMemory();
        for (ghidra.program.model.mem.MemoryBlock block : memory.getBlocks()) {
            if (!block.isExecute() || block.getSize() > Integer.MAX_VALUE) continue;
            byte[] bytes = new byte[(int)block.getSize()];
            memory.getBytes(block.getStart(), bytes);
            for (int index = 0; index <= bytes.length - 7; index++) {
                int rex = bytes[index] & 0xff;
                int opcode = bytes[index + 1] & 0xff;
                int modrm = bytes[index + 2] & 0xff;
                if (rex < 0x40 || rex > 0x4f || opcode != 0x8d || (modrm & 0xc7) != 0x05) {
                    continue;
                }
                int displacement = (bytes[index + 3] & 0xff) |
                    ((bytes[index + 4] & 0xff) << 8) |
                    ((bytes[index + 5] & 0xff) << 16) |
                    (bytes[index + 6] << 24);
                Address source = block.getStart().add(index);
                if (source.add(7L + displacement).equals(target)) {
                    Function function = getFunctionContaining(source);
                    if (function != null) return function;
                }
            }
        }
        return null;
    }

    private Set<Address> findContainingVtables(Address method, BufferedWriter writer)
            throws Exception {
        Set<Address> result = new LinkedHashSet<>();
        writer.write("references to validator:\n");
        for (Reference reference : getReferencesTo(method)) {
            Address source = reference.getFromAddress();
            writer.write("  " + source + " in " + blockName(source) + "\n");
            if (currentProgram.getMemory().getBlock(source).isExecute()) continue;
            if (blockName(source).equals(".rdata")) {
                writePointerNeighborhood(writer, source);
            }
            for (int methodIndex = 0; methodIndex < MAX_VTABLE_SEARCH_SLOTS; methodIndex++) {
                Address candidate = source.subtract(methodIndex * 8L);
                if (isMsvcVtable(candidate)) result.add(candidate);
            }
        }
        writer.write("\n");
        return result;
    }

    private void writePointerNeighborhood(BufferedWriter writer, Address center)
            throws Exception {
        Memory memory = currentProgram.getMemory();
        writer.write("  pointer neighborhood:\n");
        for (int index = -24; index <= 24; index++) {
            Address slot = center.add(index * 8L);
            if (!memory.contains(slot)) continue;
            Address target = toAddr(memory.getLong(slot));
            String description = target.toString();
            if (memory.contains(target)) {
                Function function = getFunctionAt(target);
                description += " in " + blockName(target);
                if (function != null) {
                    description += " (" + describe(function) + ")";
                    nearbyFunctions.add(function);
                }
            }
            writer.write(String.format("    %s%03x %s -> %s\n",
                index < 0 ? "-" : "+", Math.abs(index * 8), slot, description));
        }
    }

    private boolean isMsvcVtable(Address candidate) throws Exception {
        Memory memory = currentProgram.getMemory();
        Address locatorPointerAddress = candidate.subtract(8);
        if (!memory.contains(locatorPointerAddress)) return false;
        Address locator = toAddr(memory.getLong(locatorPointerAddress));
        if (!memory.contains(locator) || memory.getBlock(locator).isExecute()) return false;
        if (memory.getInt(locator) != 1) return false;

        long imageBase = currentProgram.getImageBase().getOffset();
        long selfRva = Integer.toUnsignedLong(memory.getInt(locator.add(0x14)));
        return imageBase + selfRva == locator.getOffset();
    }

    private void writeVtable(BufferedWriter writer, DecompInterface decompiler,
            Address vtable) throws Exception {
        Memory memory = currentProgram.getMemory();
        Address locator = toAddr(memory.getLong(vtable.subtract(8)));
        long imageBase = currentProgram.getImageBase().getOffset();
        Address typeDescriptor = toAddr(
            imageBase + Integer.toUnsignedLong(memory.getInt(locator.add(0xc))));

        writer.write("=== vtable " + vtable + " ===\n");
        writer.write("type: " + readCString(typeDescriptor.add(0x10), 512) + "\n\n");

        for (int index = 0; index < MAX_VTABLE_METHODS; index++) {
            Address slot = vtable.add(index * 8L);
            Address target = toAddr(memory.getLong(slot));
            if (!memory.contains(target) || !memory.getBlock(target).isExecute()) break;
            Function function = getFunctionAt(target);
            writer.write(String.format("slot +0x%02x -> %s\n", index * 8,
                function == null ? target.toString() : describe(function)));
            if (function != null) writeFunction(writer, decompiler, function);
        }
    }

    private void writeFunction(BufferedWriter writer, DecompInterface decompiler,
            Function function) throws Exception {
        writer.write("--- " + describe(function) + " ---\n");
        writer.write("callers:\n");
        for (Reference reference : getReferencesTo(function.getEntryPoint())) {
            Function caller = getFunctionContaining(reference.getFromAddress());
            if (caller != null) {
                writer.write("  " + reference.getFromAddress() + " in " +
                    describe(caller) + "\n");
            }
        }
        DecompileResults result = decompiler.decompileFunction(function, 180, monitor);
        if (!result.decompileCompleted() || result.getDecompiledFunction() == null) {
            writer.write("Unavailable: " + result.getErrorMessage() + "\n\n");
        }
        else {
            writer.write(result.getDecompiledFunction().getC());
            writer.write("\n\n");
        }
    }

    private String blockName(Address address) {
        return currentProgram.getMemory().getBlock(address).getName();
    }

    private String readCString(Address start, int limit) throws Exception {
        byte[] bytes = new byte[limit];
        int length = 0;
        while (length < limit) {
            byte value = getByte(start.add(length));
            if (value == 0) break;
            bytes[length++] = value;
        }
        return new String(bytes, 0, length, StandardCharsets.US_ASCII);
    }

    private String describe(Function function) {
        return function.getName() + " @ " + function.getEntryPoint();
    }
}
