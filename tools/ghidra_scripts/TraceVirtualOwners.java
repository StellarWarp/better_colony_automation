// Finds raw function-pointer references to queue-command callers, usually virtual tables.
// @category Stellaris

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;

public class TraceVirtualOwners extends GhidraScript {

    private static final String[] TARGETS = { "14070ad10", "140ad2ba0", "141e91430", "140ee6d80" };

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
            Memory memory = currentProgram.getMemory();
            for (String targetText : TARGETS) {
                Address target = toAddr(targetText);
                Function function = getFunctionContaining(target);
                writer.write("=== " + describe(function) + " ===\n");
                int hits = 0;
                for (MemoryBlock block : memory.getBlocks()) {
                    if (block.isExecute() || block.getSize() > Integer.MAX_VALUE) {
                        continue;
                    }
                    byte[] bytes = new byte[(int)block.getSize()];
                    memory.getBytes(block.getStart(), bytes);
                    long needle = target.getOffset();
                    for (int index = 0; index <= bytes.length - 8; index++) {
                        long value = 0;
                        for (int byteIndex = 7; byteIndex >= 0; byteIndex--) {
                            value = (value << 8) | (bytes[index + byteIndex] & 0xffL);
                        }
                        if (value != needle) {
                            continue;
                        }
                        Address pointer = block.getStart().add(index);
                        writer.write("Pointer at " + pointer + " in block " + block.getName() + "\n");
                        writeContext(writer, memory, pointer);
                        hits++;
                    }
                }
                writer.write("Matches: " + hits + "\n\n");
            }
        }
    }

    private void writeContext(BufferedWriter writer, Memory memory, Address pointer) throws Exception {
        long startOffset = Math.max(pointer.getOffset() - 0x40, currentProgram.getMinAddress().getOffset());
        Address start = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(startOffset);
        for (int index = 0; index < 17; index++) {
            Address slot = start.add(index * 8L);
            long value = memory.getLong(slot);
            Function destination = getFunctionContaining(currentProgram.getAddressFactory()
                .getDefaultAddressSpace().getAddress(value));
            writer.write(String.format("  %s: %016x  %s%n", slot, value, describe(destination)));
        }
    }

    private String describe(Function function) {
        return function == null ? "<no function>" : function.getName() + " @ " + function.getEntryPoint();
    }
}
