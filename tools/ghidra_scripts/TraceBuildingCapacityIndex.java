// Finds executable instructions that use the runtime planet modifier index for build capacity.
// @category Stellaris

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.util.LinkedHashMap;
import java.util.Map;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.mem.MemoryBlock;

public class TraceBuildingCapacityIndex extends GhidraScript {
    private static final long MODIFIER_INDEX = 0xa2;

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            throw new IllegalArgumentException("Expected one output report path");
        }

        Map<Address, Function> matches = new LinkedHashMap<>();
        byte[] needle = {(byte) 0xa2, 0x00, 0x00, 0x00};
        for (MemoryBlock block : currentProgram.getMemory().getBlocks()) {
            if (!block.isExecute()) continue;
            Address cursor = block.getStart();
            while (cursor != null && cursor.compareTo(block.getEnd()) <= 0) {
                Address match = currentProgram.getMemory().findBytes(
                    cursor, block.getEnd(), needle, null, true, monitor);
                if (match == null) break;
                Instruction instruction = getInstructionContaining(match);
                if (instruction != null && containsExactHexValue(instruction.toString(), "0xa2")) {
                    matches.put(
                        instruction.getAddress(),
                        getFunctionContaining(instruction.getAddress())
                    );
                }
                cursor = match.add(1);
            }
        }

        try (BufferedWriter writer = new BufferedWriter(new FileWriter(new File(args[0])))) {
            writer.write(String.format("modifier index: 0x%X\n", MODIFIER_INDEX));
            writer.write("instruction matches: " + matches.size() + "\n\n");
            for (Map.Entry<Address, Function> entry : matches.entrySet()) {
                Address address = entry.getKey();
                Function function = entry.getValue();
                writer.write("=== " + address + " in " + describe(function) + " ===\n");
                writeInstructionWindow(writer, address, 8, 10);
                writer.write("\n");
            }
        }
    }

    private void writeInstructionWindow(
            BufferedWriter writer, Address center, int before, int after) throws Exception {
        Instruction instruction = getInstructionAt(center);
        Instruction start = instruction;
        for (int index = 0; index < before; index++) {
            Instruction previous = getInstructionBefore(start);
            if (previous == null) break;
            start = previous;
        }
        Instruction current = start;
        for (int index = 0; current != null && index <= before + after; index++) {
            writer.write(String.format(
                "%s  %-30s  %s\n",
                current.getAddress(),
                bytesToHex(current.getBytes()),
                current.toString()
            ));
            current = getInstructionAfter(current);
        }
    }

    private String bytesToHex(byte[] bytes) {
        StringBuilder result = new StringBuilder();
        for (byte value : bytes) result.append(String.format("%02X", value & 0xff));
        return result.toString();
    }

    private boolean containsExactHexValue(String instruction, String value) {
        String text = instruction.toLowerCase();
        int index = text.indexOf(value);
        while (index >= 0) {
            int end = index + value.length();
            if (end == text.length() || Character.digit(text.charAt(end), 16) < 0) {
                return true;
            }
            index = text.indexOf(value, index + 1);
        }
        return false;
    }

    private String describe(Function function) {
        return function == null
            ? "<no function>"
            : function.getName() + " @ " + function.getEntryPoint();
    }
}
