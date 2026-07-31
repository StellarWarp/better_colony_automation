// Resolves MSVC RTTI names for virtual tables containing known queue-command paths.
// @category Stellaris

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.nio.charset.StandardCharsets;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.mem.Memory;

public class IdentifyQueueCommandTypes extends GhidraScript {
    private static final String[] TARGETS = { "14070ad10", "140ad2ba0", "141e91430" };

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) throw new IllegalArgumentException("Expected one output report path");
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(new File(args[0])))) {
            Memory memory = currentProgram.getMemory();
            for (String targetText : TARGETS) {
                Address target = toAddr(targetText);
                writer.write("=== " + target + " ===\n");
                Address pointer = findPointer(memory, target.getOffset());
                if (pointer == null) { writer.write("No function pointer found.\n\n"); continue; }
                Address locatorPointer = findPrecedingLocator(memory, pointer);
                writer.write("Function pointer: " + pointer + "\n");
                if (locatorPointer == null) { writer.write("No preceding MSVC complete-object locator found.\n\n"); continue; }
                Address vtableStart = locatorPointer.add(8);
                long locatorValue = memory.getLong(locatorPointer);
                Address locator = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(locatorValue);
                writer.write("Vtable start: " + vtableStart + "\nCOL pointer: " + locatorPointer + " -> " + locator + "\n");
                if (memory.contains(locator) && memory.contains(locator.add(0x17))) {
                    long typeRva = Integer.toUnsignedLong(memory.getInt(locator.add(0xc)));
                    Address type = currentProgram.getImageBase().add(typeRva);
                    writer.write("Type descriptor: " + type + "\nName: " + readAscii(memory, type.add(0x10), 300) + "\n");
                }
                writer.write("\n");
            }
        }
    }

    private Address findPointer(Memory memory, long target) throws Exception {
        for (ghidra.program.model.mem.MemoryBlock block : memory.getBlocks()) {
            if (block.isExecute() || block.getSize() > Integer.MAX_VALUE) continue;
            byte[] data = new byte[(int)block.getSize()]; memory.getBytes(block.getStart(), data);
            for (int i = 0; i <= data.length - 8; i++) {
                long value = 0; for (int j = 7; j >= 0; j--) value = (value << 8) | (data[i + j] & 0xffL);
                if (value == target) return block.getStart().add(i);
            }
        }
        return null;
    }

    private Address findPrecedingLocator(Memory memory, Address pointer) throws Exception {
        for (int slots = 1; slots <= 384; slots++) {
            Address candidate = pointer.subtract(slots * 8L);
            if (!memory.contains(candidate)) continue;
            long value = memory.getLong(candidate);
            Address locator = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(value);
            if (!memory.contains(locator) || !memory.contains(locator.add(0x17))) continue;
            int signature = memory.getInt(locator);
            long typeRva = Integer.toUnsignedLong(memory.getInt(locator.add(0xc)));
            Address type = currentProgram.getImageBase().add(typeRva);
            if ((signature == 0 || signature == 1) && memory.contains(type.add(0x10))) return candidate;
        }
        return null;
    }

    private String readAscii(Memory memory, Address address, int maximum) throws Exception {
        StringBuilder value = new StringBuilder();
        for (int i = 0; i < maximum && memory.contains(address.add(i)); i++) {
            int c = memory.getByte(address.add(i)) & 0xff;
            if (c == 0) break;
            value.append(c >= 0x20 && c <= 0x7e ? (char)c : '.');
        }
        return value.toString();
    }
}
