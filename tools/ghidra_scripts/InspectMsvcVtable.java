// Resolves MSVC RTTI names and function pointers for selected vtables.
// @category Stellaris

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.nio.charset.StandardCharsets;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.mem.Memory;

public class InspectMsvcVtable extends GhidraScript {
    private static final String[] VTABLES = {
        "14255dab8",
        "1424dba80",
        "1424dba48",
        "14249d690",
        "1424d5208"
    };

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            throw new IllegalArgumentException("Expected one output report path");
        }
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(new File(args[0])))) {
            for (String value : VTABLES) {
                inspect(writer, toAddr(value));
            }
        }
    }

    private void inspect(BufferedWriter writer, Address vtable) throws Exception {
        Memory memory = currentProgram.getMemory();
        long imageBase = currentProgram.getImageBase().getOffset();
        long locatorPointer = memory.getLong(vtable.subtract(8));
        Address locator = toAddr(locatorPointer);

        writer.write("=== vtable " + vtable + " ===\n");
        writer.write("complete object locator: " + locator + "\n");
        if (memory.contains(locator) && !memory.getBlock(locator).isExecute()) {
            int typeDescriptorRva = memory.getInt(locator.add(0xc));
            Address typeDescriptor = toAddr(imageBase + Integer.toUnsignedLong(typeDescriptorRva));
            writer.write("type descriptor: " + typeDescriptor + "\n");
            if (memory.contains(typeDescriptor.add(0x10))) {
                writer.write("type name: " + readCString(typeDescriptor.add(0x10), 512) + "\n");
            }
        }
        else {
            writer.write("No standard MSVC complete-object locator before this table.\n");
        }
        writer.write("nearby pointers:\n");
        for (int index = -8; index < 0; index++) {
            writeSlot(writer, vtable, index);
        }
        writer.write("methods:\n");

        for (int index = 0; index < 32; index++) {
            Address target = writeSlot(writer, vtable, index);
            if (!memory.contains(target) || !memory.getBlock(target).isExecute()) {
                break;
            }
        }
        writer.write("raw ASCII from first non-code slot onward:\n");
        writer.write(readPrintable(vtable, 0x200) + "\n");
        writer.write("\n");
    }

    private Address writeSlot(BufferedWriter writer, Address vtable, int index) throws Exception {
        Memory memory = currentProgram.getMemory();
        Address slot = vtable.add(index * 8L);
        Address target = toAddr(memory.getLong(slot));
        Function function = getFunctionAt(target);
        writer.write(String.format(
            "  %s0x%02x %s -> %s\n",
            index < 0 ? "-" : "+",
            Math.abs(index * 8),
            target,
            function == null ? "<no function>" : function.getName()
        ));
        return target;
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

    private String readPrintable(Address start, int limit) throws Exception {
        StringBuilder result = new StringBuilder();
        for (int index = 0; index < limit; index++) {
            int value = getByte(start.add(index)) & 0xff;
            result.append(value >= 0x20 && value < 0x7f ? (char)value : '.');
        }
        return result.toString();
    }
}
