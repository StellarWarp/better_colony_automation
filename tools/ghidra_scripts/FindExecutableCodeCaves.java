// Finds unreferenced executable padding suitable for a small local helper.
// @category Stellaris

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.Reference;

public class FindExecutableCodeCaves extends GhidraScript {
    private static final Address PATCH_SITE = null;
    private static final int MIN_LENGTH = 0x80;

    private record Cave(
        Address start,
        int length,
        long distance,
        int fill,
        String blockName,
        Address blockStart,
        Address blockEnd
    ) {}

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            throw new IllegalArgumentException("Expected one output report path");
        }

        Address patchSite = toAddr("140ee7081");
        List<Cave> caves = new ArrayList<>();
        for (MemoryBlock block : currentProgram.getMemory().getBlocks()) {
            if (!block.isExecute() || !block.isInitialized()) continue;
            Address cursor = block.getStart();
            Address end = block.getEnd();
            while (cursor.compareTo(end) <= 0 && !monitor.isCancelled()) {
                int fill = getByte(cursor) & 0xff;
                if (fill != 0 && fill != 0xcc) {
                    cursor = cursor.next();
                    continue;
                }

                Address start = cursor;
                int length = 0;
                while (cursor.compareTo(end) <= 0 &&
                        (getByte(cursor) & 0xff) == fill) {
                    length++;
                    cursor = cursor.next();
                }
                if (length >= MIN_LENGTH && isUnreferenced(start, length)) {
                    long distance = Math.abs(
                        start.getOffset() - patchSite.getOffset()
                    );
                    caves.add(new Cave(
                        start,
                        length,
                        distance,
                        fill,
                        block.getName(),
                        block.getStart(),
                        block.getEnd()
                    ));
                }
            }
        }

        caves.sort(Comparator.comparingLong(Cave::distance));
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(new File(args[0])))) {
            writer.write("patch_site: " + patchSite + "\n");
            writer.write("minimum_length: 0x" + Integer.toHexString(MIN_LENGTH) + "\n");
            writer.write("candidate_count: " + caves.size() + "\n\n");
            for (int index = 0; index < Math.min(caves.size(), 100); index++) {
                Cave cave = caves.get(index);
                writer.write(String.format(
                    "%s length=0x%x fill=0x%02x distance=0x%x " +
                    "block=%s block_range=%s-%s%n",
                    cave.start(), cave.length(), cave.fill(), cave.distance(),
                    cave.blockName(), cave.blockStart(), cave.blockEnd()
                ));
            }
        }
    }

    private boolean isUnreferenced(Address start, int length) {
        for (int offset = 0; offset < length; offset++) {
            Address address = start.add(offset);
            Reference[] references = getReferencesTo(address);
            if (references.length != 0 ||
                    currentProgram.getFunctionManager().getFunctionAt(address) != null) {
                return false;
            }
        }
        return true;
    }
}
