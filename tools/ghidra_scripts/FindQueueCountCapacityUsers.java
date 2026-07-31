// Finds functions that access both construction queue count and capacity offsets.
// @category Stellaris

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.AddressSetView;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;

public class FindQueueCountCapacityUsers extends GhidraScript {
    private static final Pattern FIELD_ACCESS = Pattern.compile(
        "\\[(r(?:ax|bx|cx|dx|si|di|8|9|10|11|12|13|14|15)) \\+ 0x(2c|48)\\]"
    );

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            throw new IllegalArgumentException("Expected one output report path");
        }

        try (BufferedWriter writer = new BufferedWriter(new FileWriter(new File(args[0])))) {
            FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
            while (functions.hasNext() && !monitor.isCancelled()) {
                Function function = functions.next();
                AddressSetView body = function.getBody();
                InstructionIterator instructions =
                    currentProgram.getListing().getInstructions(body, true);
                Map<String, List<String>> countAccesses = new HashMap<>();
                Map<String, List<String>> capacityAccesses = new HashMap<>();

                while (instructions.hasNext()) {
                    Instruction instruction = instructions.next();
                    String text = instruction.toString().toLowerCase(Locale.ROOT);
                    if (isStackAccess(text)) continue;
                    Matcher matcher = FIELD_ACCESS.matcher(text);
                    while (matcher.find()) {
                        Map<String, List<String>> accesses =
                            matcher.group(2).equals("2c") ? countAccesses : capacityAccesses;
                        accesses.computeIfAbsent(matcher.group(1), ignored -> new ArrayList<>())
                            .add(instruction.getAddress() + "  " + instruction);
                    }
                }

                Set<String> sharedBases = new HashSet<>(countAccesses.keySet());
                sharedBases.retainAll(capacityAccesses.keySet());
                if (!sharedBases.isEmpty()) {
                    writer.write("=== " + function.getName() + " @ " +
                        function.getEntryPoint() + " ===\n");
                    for (String base : sharedBases) {
                        writer.write("base " + base + " count accesses:\n");
                        for (String access : countAccesses.get(base)) {
                            writer.write("  " + access + "\n");
                        }
                        writer.write("base " + base + " capacity accesses:\n");
                        for (String access : capacityAccesses.get(base)) {
                            writer.write("  " + access + "\n");
                        }
                    }
                    writer.write("\n");
                }
            }
        }
    }

    private boolean isStackAccess(String text) {
        return text.contains("[rsp") || text.contains("[rbp");
    }
}
