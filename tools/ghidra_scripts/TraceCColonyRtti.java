// Recovers CColony RTTI complete-object locators and virtual tables.
// @category Stellaris

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;

public class TraceCColonyRtti extends GhidraScript {
    private static final byte[] NAME = ".?AVCColony@@".getBytes(StandardCharsets.US_ASCII);

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) throw new IllegalArgumentException("Expected one output report path");
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(new File(args[0])))) {
            Memory memory = currentProgram.getMemory();
            List<Address> descriptors = findBytes(memory, NAME);
            writer.write("CColony type-descriptor names: " + descriptors.size() + "\n");
            for (Address descriptorName : descriptors) {
                Address typeDescriptor = descriptorName.subtract(0x10);
                long rva = typeDescriptor.getOffset() - currentProgram.getImageBase().getOffset();
                writer.write("\nType descriptor " + typeDescriptor + ", name " + descriptorName + ", RVA " + Long.toHexString(rva) + "\n");
                List<Address> cols = findDword(memory, (int)rva);
                for (Address col : cols) {
                    if (!isLikelyCompleteObjectLocator(memory, col, (int)rva)) continue;
                    writer.write("  Complete object locator: " + col + "\n");
                    for (Address vtablePointer : findQword(memory, col.getOffset())) {
                        Address vtable = vtablePointer.add(8);
                        writer.write("  Vtable starts " + vtable + " (locator pointer " + vtablePointer + ")\n");
                        writeVtable(writer, memory, vtable);
                    }
                }
            }
        }
    }

    private boolean isLikelyCompleteObjectLocator(Memory memory, Address address, int typeRva) throws Exception {
        return memory.contains(address) && memory.getInt(address.add(0xc)) == typeRva;
    }

    private List<Address> findBytes(Memory memory, byte[] needle) throws Exception {
        List<Address> matches = new ArrayList<>();
        for (MemoryBlock block : memory.getBlocks()) {
            if (block.getSize() > Integer.MAX_VALUE) continue;
            byte[] bytes = new byte[(int)block.getSize()];
            memory.getBytes(block.getStart(), bytes);
            for (int i = 0; i <= bytes.length - needle.length; i++) {
                int j = 0; while (j < needle.length && bytes[i + j] == needle[j]) j++;
                if (j == needle.length) matches.add(block.getStart().add(i));
            }
        }
        return matches;
    }

    private List<Address> findDword(Memory memory, int needle) throws Exception {
        List<Address> matches = new ArrayList<>();
        for (MemoryBlock block : memory.getBlocks()) {
            if (block.isExecute() || block.getSize() > Integer.MAX_VALUE) continue;
            byte[] bytes = new byte[(int)block.getSize()]; memory.getBytes(block.getStart(), bytes);
            for (int i = 0; i <= bytes.length - 4; i++) {
                int value = (bytes[i] & 0xff) | ((bytes[i + 1] & 0xff) << 8) | ((bytes[i + 2] & 0xff) << 16) | (bytes[i + 3] << 24);
                if (value == needle) matches.add(block.getStart().add(i));
            }
        }
        return matches;
    }

    private List<Address> findQword(Memory memory, long needle) throws Exception {
        List<Address> matches = new ArrayList<>();
        for (MemoryBlock block : memory.getBlocks()) {
            if (block.isExecute() || block.getSize() > Integer.MAX_VALUE) continue;
            byte[] bytes = new byte[(int)block.getSize()]; memory.getBytes(block.getStart(), bytes);
            for (int i = 0; i <= bytes.length - 8; i++) {
                long value = 0; for (int j = 7; j >= 0; j--) value = (value << 8) | (bytes[i + j] & 0xffL);
                if (value == needle) matches.add(block.getStart().add(i));
            }
        }
        return matches;
    }

    private void writeVtable(BufferedWriter writer, Memory memory, Address start) throws Exception {
        for (int i = 0; i < 96 && memory.contains(start.add(i * 8L)); i++) {
            Address slot = start.add(i * 8L);
            long value = memory.getLong(slot);
            Address destination = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(value);
            Function function = getFunctionContaining(destination);
            if (function == null) break;
            writer.write(String.format("    [%02d] %s  %s @ %s%n", i, slot, function.getName(), function.getEntryPoint()));
        }
    }
}
