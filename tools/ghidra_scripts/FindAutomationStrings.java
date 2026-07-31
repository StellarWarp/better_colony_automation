// Lists ASCII strings relevant to colony automation and their code references.
// @category Stellaris

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.Reference;

public class FindAutomationStrings extends GhidraScript {
    private static final String[] TERMS = { "automation", "colony", "construction_queue", "queue" };

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) throw new IllegalArgumentException("Expected one output report path");
        File report = new File(args[0]);
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(report))) {
            Memory memory = currentProgram.getMemory();
            for (MemoryBlock block : memory.getBlocks()) {
                if (block.isExecute() || block.getSize() > Integer.MAX_VALUE) continue;
                byte[] bytes = new byte[(int)block.getSize()];
                memory.getBytes(block.getStart(), bytes);
                for (int start = 0; start < bytes.length; ) {
                    int end = start;
                    while (end < bytes.length && isPrintable(bytes[end])) end++;
                    if (end - start >= 5) {
                        String value = new String(bytes, start, end - start, StandardCharsets.US_ASCII);
                        if (matches(value)) writeMatch(writer, memory, block.getStart().add(start), value);
                    }
                    start = end + 1;
                }
            }
        }
    }

    private boolean matches(String value) {
        String lower = value.toLowerCase(Locale.ROOT);
        for (String term : TERMS) if (lower.contains(term)) return true;
        return false;
    }

    private boolean isPrintable(byte value) {
        int c = value & 0xff;
        return c >= 0x20 && c <= 0x7e;
    }

    private void writeMatch(BufferedWriter writer, Memory memory, Address address, String value) throws Exception {
        writer.write("=== " + address + " ===\n" + value + "\n");
        Set<Address> sources = new LinkedHashSet<>();
        for (Reference reference : getReferencesTo(address)) sources.add(reference.getFromAddress());
        for (Address source : findRipRelativeLeaReferences(memory, address)) sources.add(source);
        for (Address source : sources) {
            Function function = getFunctionContaining(source);
            writer.write("  xref " + source + " in " + (function == null ? "<none>" : function.getName() + " @ " + function.getEntryPoint()) + "\n");
        }
        writer.write("\n");
    }

    private List<Address> findRipRelativeLeaReferences(Memory memory, Address target) throws Exception {
        List<Address> sources = new ArrayList<>();
        for (MemoryBlock block : memory.getBlocks()) {
            if (!block.isExecute() || block.getSize() > Integer.MAX_VALUE) continue;
            byte[] bytes = new byte[(int)block.getSize()];
            memory.getBytes(block.getStart(), bytes);
            for (int index = 0; index <= bytes.length - 7; index++) {
                int rex = bytes[index] & 0xff, opcode = bytes[index + 1] & 0xff, modrm = bytes[index + 2] & 0xff;
                if (rex < 0x40 || rex > 0x4f || opcode != 0x8d || (modrm & 0xc7) != 0x05) continue;
                int displacement = (bytes[index + 3] & 0xff) | ((bytes[index + 4] & 0xff) << 8)
                    | ((bytes[index + 5] & 0xff) << 16) | (bytes[index + 6] << 24);
                Address source = block.getStart().add(index);
                if (source.add(7L + displacement).equals(target)) sources.add(source);
            }
        }
        return sources;
    }
}
