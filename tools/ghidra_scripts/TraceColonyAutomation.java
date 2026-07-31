// Locates engine strings and their code references in a loaded Ghidra program.
// @category Stellaris

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.Reference;

public class TraceColonyAutomation extends GhidraScript {

    private static final String[] NEEDLES = {
        "CColonyAutomationDatabase",
        "CColonyAutomationCategoryDatabase",
        "CAddBuildableToQueueCommand",
        "construction_queue",
        "queue_building_construction",
        "planet_building_capacity_add",
        "COLONY_AUTOMATION_COOLDOWN"
    };

    @Override
    public void run() throws Exception {
        Memory memory = currentProgram.getMemory();
        Address start = currentProgram.getMinAddress();
        Address end = currentProgram.getMaxAddress();

        DecompInterface decompiler = new DecompInterface();
        try {
            decompiler.openProgram(currentProgram);

            for (String needle : NEEDLES) {
                println("\n=== " + needle + " ===");
                List<Address> matches = findAsciiMatches(memory, start, end, needle);
                if (matches.isEmpty()) {
                    println("not found");
                    continue;
                }

                for (Address match : matches) {
                    println("string address: " + match);
                    Reference[] references = getReferencesTo(match);
                    List<Address> sources = new ArrayList<>();
                    for (Reference reference : references) {
                        sources.add(reference.getFromAddress());
                    }
                    for (Address source : findRipRelativeLeaReferences(memory, match)) {
                        if (!sources.contains(source)) {
                            sources.add(source);
                        }
                    }
                    println("references: " + sources.size());

                    for (Address source : sources) {
                        Function function = getFunctionContaining(source);
                        println("xref " + source + " in " + functionName(function));

                        if (function != null) {
                            printDecompilerExcerpt(decompiler, function);
                        }
                    }
                }
            }
        }
        finally {
            decompiler.dispose();
        }
    }

    private List<Address> findAsciiMatches(Memory memory, Address start, Address end, String value) throws Exception {
        byte[] bytes = value.getBytes(StandardCharsets.US_ASCII);
        List<Address> matches = new ArrayList<>();
        Address cursor = start;
        while (cursor != null && cursor.compareTo(end) <= 0 && matches.size() < 32) {
            Address match = memory.findBytes(cursor, end, bytes, null, true, monitor);
            if (match == null) {
                break;
            }
            matches.add(match);
            cursor = match.add(1);
        }
        return matches;
    }

    private List<Address> findRipRelativeLeaReferences(Memory memory, Address target) throws Exception {
        List<Address> sources = new ArrayList<>();
        for (MemoryBlock block : memory.getBlocks()) {
            if (!block.isExecute() || block.getSize() > Integer.MAX_VALUE) {
                continue;
            }
            byte[] bytes = new byte[(int) block.getSize()];
            memory.getBytes(block.getStart(), bytes);
            for (int index = 0; index <= bytes.length - 7; index++) {
                int rex = bytes[index] & 0xff;
                int opcode = bytes[index + 1] & 0xff;
                int modrm = bytes[index + 2] & 0xff;
                if (rex < 0x40 || rex > 0x4f || opcode != 0x8d || (modrm & 0xc7) != 0x05) {
                    continue;
                }
                int displacement = (bytes[index + 3] & 0xff)
                    | ((bytes[index + 4] & 0xff) << 8)
                    | ((bytes[index + 5] & 0xff) << 16)
                    | (bytes[index + 6] << 24);
                Address source = block.getStart().add(index);
                if (source.add(7L + displacement).equals(target)) {
                    sources.add(source);
                }
            }
        }
        return sources;
    }

    private String functionName(Function function) {
        if (function == null) {
            return "<no containing function>";
        }
        return function.getName() + " @ " + function.getEntryPoint();
    }

    private void printDecompilerExcerpt(DecompInterface decompiler, Function function) {
        DecompileResults result = decompiler.decompileFunction(function, 30, monitor);
        if (!result.decompileCompleted() || result.getDecompiledFunction() == null) {
            println("  decompilation unavailable: " + result.getErrorMessage());
            return;
        }

        String code = result.getDecompiledFunction().getC();
        String[] lines = code.split("\\R");
        int limit = Math.min(lines.length, 80);
        println("  decompiler excerpt:");
        for (int index = 0; index < limit; index++) {
            println("    " + lines[index]);
        }
        if (lines.length > limit) {
            println("    ... truncated after " + limit + " lines");
        }
    }
}
