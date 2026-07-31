// Finds functions that reference both building and district RTTI descriptors.
// @category Stellaris

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;

public class TracePlanetConstructionRtti extends GhidraScript {
    private static final String BUILDING_RTTI = "CBuildingType::RTTI_Type_Descriptor";
    private static final String DISTRICT_RTTI = "CDistrictType::RTTI_Type_Descriptor";

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 1) {
            throw new IllegalArgumentException("Expected one output report path");
        }

        Address building = findGlobalSymbol(BUILDING_RTTI);
        Address district = findGlobalSymbol(DISTRICT_RTTI);
        Map<Address, Function> buildingFunctions = functionsReferencing(building);
        Map<Address, Function> districtFunctions = functionsReferencing(district);
        Set<Address> intersection = new LinkedHashSet<>(buildingFunctions.keySet());
        intersection.retainAll(districtFunctions.keySet());

        try (BufferedWriter writer = new BufferedWriter(new FileWriter(new File(args[0])))) {
            writer.write(BUILDING_RTTI + ": " + building + "\n");
            writer.write(DISTRICT_RTTI + ": " + district + "\n");
            writer.write("building functions: " + buildingFunctions.size() + "\n");
            writer.write("district functions: " + districtFunctions.size() + "\n");
            writer.write("intersection: " + intersection.size() + "\n\n");

            DecompInterface decompiler = new DecompInterface();
            try {
                decompiler.openProgram(currentProgram);
                for (Address entry : intersection) {
                    Function function = buildingFunctions.get(entry);
                    writer.write("=== " + describe(function) + " ===\n");
                    writeDecompilation(writer, decompiler, function);
                    writer.write("\n");
                }
            }
            finally {
                decompiler.dispose();
            }
        }
    }

    private Address findGlobalSymbol(String name) {
        SymbolIterator symbols = currentProgram.getSymbolTable().getAllSymbols(true);
        while (symbols.hasNext()) {
            Symbol symbol = symbols.next();
            if (symbol.getName(true).equals(name)) return symbol.getAddress();
        }
        throw new IllegalArgumentException("Symbol not found: " + name);
    }

    private Map<Address, Function> functionsReferencing(Address target) {
        Map<Address, Function> result = new LinkedHashMap<>();
        for (Reference reference : getReferencesTo(target)) {
            Function function = getFunctionContaining(reference.getFromAddress());
            if (function != null) result.put(function.getEntryPoint(), function);
        }
        return result;
    }

    private void writeDecompilation(
            BufferedWriter writer, DecompInterface decompiler, Function function) throws Exception {
        DecompileResults result = decompiler.decompileFunction(function, 180, monitor);
        if (!result.decompileCompleted() || result.getDecompiledFunction() == null) {
            writer.write("Unavailable: " + result.getErrorMessage() + "\n");
        }
        else {
            writer.write(result.getDecompiledFunction().getC());
            writer.write("\n");
        }
    }

    private String describe(Function function) {
        return function.getName() + " @ " + function.getEntryPoint();
    }
}
