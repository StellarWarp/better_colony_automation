"""
PDXLang Scope 规则

此文件由 tools/generate_python_rules.py 自动生成
"""

SCOPES = {
    'alliance': {
        "description": 'Scopes from a country to the federation it is a member of.',
        "input_scopes": ['country'],
        "output_scope": 'unknown',
    },
    'archaeological_site': {
        "description": 'Scopes from an object (e.g. planet) in star system view to the arc site in the same location.',
        "input_scopes": ['megastructure', 'planet', 'ship', 'fleet', 'galactic_object', 'ambient_object', 'starbase', 'archaeological_site', 'debris'],
        "output_scope": 'unknown',
    },
    'army_leader': {
        "description": 'Scopes from an object to its army leader, e.g. planet->general',
        "input_scopes": ['planet'],
        "output_scope": 'unknown',
    },
    'assembling_species': {
        "description": 'Scopes from a planet to the species currently being assembled on it.',
        "input_scopes": ['planet'],
        "output_scope": 'unknown',
    },
    'associated_federation': {
        "description": 'Scopes from a country to the federation it is an associate of.',
        "input_scopes": ['country'],
        "output_scope": 'unknown',
    },
    'astral_rift': {
        "description": 'Scopes to the astral rift in the same system.',
        "input_scopes": ['galactic_object', 'leader'],
        "output_scope": 'unknown',
    },
    'attacker': {
        "description": 'Scopes from a war to its main attacker.',
        "input_scopes": ['war'],
        "output_scope": 'unknown',
    },
    'aura_owner': {
        "description": 'If scoped system contains a Psionic Aura, scopes to the country who generated the aura (can be different from the system owner).',
        "input_scopes": ['galactic_object'],
        "output_scope": 'unknown',
    },
    'background_planet': {
        "description": 'Scopes from a leader to their background planet',
        "input_scopes": ['leader'],
        "output_scope": 'unknown',
    },
    'branch_office_owner': {
        "description": 'Scopes from a planet to the owner of a branch office.',
        "input_scopes": ['planet'],
        "output_scope": 'unknown',
    },
    'built_species': {
        "description": 'Scopes from a country to its built species.',
        "input_scopes": ['country'],
        "output_scope": 'unknown',
    },
    'capital_scope': {
        "description": 'Scopes from an empire to its capital planet.',
        "input_scopes": ['country'],
        "output_scope": 'unknown',
    },
    'capital_star': {
        "description": "Scopes from an empire to the primary star (planet scope) of its capital's system.",
        "input_scopes": ['country'],
        "output_scope": 'unknown',
    },
    'contact_country': {
        "description": 'Scopes from a first contact site to the country that the owner of the site is seeking to establish communications with.',
        "input_scopes": ['first_contact'],
        "output_scope": 'unknown',
    },
    'controller': {
        "description": 'Scopes from a planet (or starbase) to the empire controlling it (not necessarily the owner: a country occupying a planet is its controller).',
        "input_scopes": ['planet', 'ship', 'fleet', 'starbase', 'debris'],
        "output_scope": 'unknown',
    },
    'creator': {
        "description": "Scopes to the leader's country of origin",
        "input_scopes": ['leader'],
        "output_scope": 'unknown',
    },
    'declining_species': {
        "description": 'Scopes from a planet to the species currently declining on it.',
        "input_scopes": ['planet'],
        "output_scope": 'unknown',
    },
    'defender': {
        "description": 'Scopes from a war to its main defender.',
        "input_scopes": ['war'],
        "output_scope": 'unknown',
    },
    'design': {
        "description": "Scopes to the ship's design",
        "input_scopes": ['ship'],
        "output_scope": 'unknown',
    },
    'envoy_location_country': {
        "description": 'Scopes from an envoy to the empire it is appointed to.',
        "input_scopes": ['leader'],
        "output_scope": 'unknown',
    },
    'excavator_fleet': {
        "description": 'Scopes from an arc site to the fleet whose leader is currently investigating it.',
        "input_scopes": ['archaeological_site'],
        "output_scope": 'unknown',
    },
    'explorer': {
        "description": 'Scopes from an astral rift to the country whose leader is exploring, or has explored it.',
        "input_scopes": ['astral_rift'],
        "output_scope": 'unknown',
    },
    'federation': {
        "description": 'Scopes from a country to the federation it is a member of.',
        "input_scopes": ['country'],
        "output_scope": 'unknown',
    },
    'federation_leader': {
        "description": 'Scopes from a federation to the empire leading it.',
        "input_scopes": ['federation'],
        "output_scope": 'unknown',
    },
    'fleet': {
        "description": 'Scopes from a ship, starbase, astral rift or leader to its fleet, or from an army to the fleet its army transport is part of.',
        "input_scopes": ['ship', 'fleet', 'leader', 'army', 'starbase', 'astral_rift'],
        "output_scope": 'unknown',
    },
    'founder_species': {
        "description": 'Scopes from a country to its founding species.',
        "input_scopes": ['country'],
        "output_scope": 'unknown',
    },
    'from': {
        "description": 'Scopes to the ROOT of the previous event, or the preset hardcoded FROM scope.',
        "input_scopes": ['all'],
        "output_scope": 'unknown',
    },
    'fromfrom': {
        "description": 'Scopes to the FROM of the FROM scope (ROOT of two events ago, or the preset hardcoded FROMFROM scope).',
        "input_scopes": ['all'],
        "output_scope": 'unknown',
    },
    'fromfromfrom': {
        "description": 'Scopes to the FROM of the FROMFROM scope (ROOT of three events ago, or the preset hardcoded FROMFROMFROM scope)',
        "input_scopes": ['all'],
        "output_scope": 'unknown',
    },
    'fromfromfromfrom': {
        "description": 'Scopes to the FROM of the FROMFROMFROM scope (ROOT of four events ago, or the preset hardcoded FROMFROMFROMFROM scope)',
        "input_scopes": ['all'],
        "output_scope": 'unknown',
    },
    'galactic_custodian': {
        "description": 'Scopes to the Custodian empire of the Galactic Community.',
        "input_scopes": ['all'],
        "output_scope": 'unknown',
    },
    'galactic_emperor': {
        "description": 'Scopes to the ruling empire of the Galactic Imperium.',
        "input_scopes": ['all'],
        "output_scope": 'unknown',
    },
    'growing_species': {
        "description": 'Scopes from a planet to the species currently growing (not assembling) on it.',
        "input_scopes": ['planet'],
        "output_scope": 'unknown',
    },
    'heir': {
        "description": "Scopes to the heir of a country (or the heir of the object's owner).",
        "input_scopes": ['megastructure', 'planet', 'country', 'ship', 'pop', 'pop_group', 'fleet', 'galactic_object', 'leader', 'army', 'bypass', 'pop_faction', 'starbase', 'deposit', 'sector', 'archaeological_site', 'first_contact', 'spy_network', 'espionage_operation', 'agreement', 'situation', 'debris', 'astral_rift'],
        "output_scope": 'unknown',
    },
    'home_planet': {
        "description": "Scopes to a species' home planet (also works from country, pop and leader; scopes to that object's species's home planet).",
        "input_scopes": ['country', 'pop', 'pop_group', 'leader', 'species'],
        "output_scope": 'unknown',
    },
    'instigator': {
        "description": 'If scoped war was generated from a proxy war, scopes to the country who started the proxy war.',
        "input_scopes": ['war'],
        "output_scope": 'unknown',
    },
    'last_added_deposit': {
        "description": 'Scopes to the last deposit added to the current planet',
        "input_scopes": ['planet'],
        "output_scope": 'unknown',
    },
    'last_created_ambient_object': {
        "description": 'Scopes to the last ambient object that was created anywhere in the game.',
        "input_scopes": ['all'],
        "output_scope": 'unknown',
    },
    'last_created_army': {
        "description": 'Scopes to the last army that was created anywhere in the game.',
        "input_scopes": ['all'],
        "output_scope": 'unknown',
    },
    'last_created_cosmic_storm': {
        "description": 'Scopes to the last storm that was created anywhere in the game.',
        "input_scopes": ['all'],
        "output_scope": 'unknown',
    },
    'last_created_cosmic_storm_influence_field': {
        "description": 'Scopes to the last storm influence field that was created anywhere in the game.',
        "input_scopes": ['all'],
        "output_scope": 'unknown',
    },
    'last_created_country': {
        "description": 'Scopes to the last country that was created anywhere in the game.',
        "input_scopes": ['all'],
        "output_scope": 'unknown',
    },
    'last_created_design': {
        "description": 'Scopes to the last created ship design',
        "input_scopes": ['all'],
        "output_scope": 'unknown',
    },
    'last_created_fleet': {
        "description": 'Scopes to the last fleet that was created anywhere in the game.',
        "input_scopes": ['all'],
        "output_scope": 'unknown',
    },
    'last_created_leader': {
        "description": 'Scopes to the last leader that was created anywhere in the game.',
        "input_scopes": ['all'],
        "output_scope": 'unknown',
    },
    'last_created_pop_faction': {
        "description": 'Scopes to the last pop faction that was created anywhere in the game.',
        "input_scopes": ['all'],
        "output_scope": 'unknown',
    },
    'last_created_ship': {
        "description": 'Scopes to the last ship that was created anywhere in the game.',
        "input_scopes": ['all'],
        "output_scope": 'unknown',
    },
    'last_created_species': {
        "description": 'Scopes to the last species that was created anywhere in the game.',
        "input_scopes": ['all'],
        "output_scope": 'unknown',
    },
    'last_created_system': {
        "description": 'Scopes to the last fleet that was created anywhere in the game.',
        "input_scopes": ['all'],
        "output_scope": 'unknown',
    },
    'leader': {
        "description": 'Scopes from an object to its leader, e.g. country->ruler, fleet->admiral/scientist, sector->governor, army->general, arc site->scientist...',
        "input_scopes": ['planet', 'country', 'ship', 'fleet', 'leader', 'army', 'pop_faction', 'federation', 'archaeological_site', 'first_contact', 'spy_network', 'espionage_operation', 'astral_rift'],
        "output_scope": 'unknown',
    },
    'lock_country': {
        "description": 'Scopes from a bypass to the country who locked it.',
        "input_scopes": ['bypass'],
        "output_scope": 'unknown',
    },
    'mining_station': {
        "description": 'Scopes from a planet to the mining station in orbit of it.',
        "input_scopes": ['planet'],
        "output_scope": 'unknown',
    },
    'no_scope': {
        "description": 'Sets the scope to no scope (empty scope used for certain generalized behavior).',
        "input_scopes": ['all'],
        "output_scope": 'unknown',
    },
    'observation_outpost': {
        "description": 'Scopes from a planet to the observation outpost in orbit of it.',
        "input_scopes": ['planet'],
        "output_scope": 'unknown',
    },
    'observation_outpost_owner': {
        "description": 'Scopes from a planet to the owner of the observation outpost in orbit of it.',
        "input_scopes": ['planet'],
        "output_scope": 'unknown',
    },
    'orbit': {
        "description": 'Scopes to the planet the current object is in orbit of. Works on ships, fleets, starbases, armies (when in military transports) and moons (scopes to the planet that a moon orbits).',
        "input_scopes": ['planet', 'ship', 'fleet', 'army', 'starbase'],
        "output_scope": 'unknown',
    },
    'orbital_defence': {
        "description": 'Scopes from a planet to the orbital defence station (orbital ring, starbase) orbiting the planet',
        "input_scopes": ['planet'],
        "output_scope": 'unknown',
    },
    'orbital_station': {
        "description": 'Scopes from a planet to the station (mining station, research station, observation outpost) orbiting it.',
        "input_scopes": ['planet'],
        "output_scope": 'unknown',
    },
    'overlord': {
        "description": 'Scopes from a country to its overlord.',
        "input_scopes": ['country'],
        "output_scope": 'unknown',
    },
    'owner': {
        "description": 'Scopes to the owner of the current object. Works on any object that could be construed as being owned by a country (incl. planets, ships, fleets, leaders, pops, solar systems, pop factions, megastructures, first contacts, spy networks, espionage operations, armies, starbases, deposits, sectors, arc sites)',
        "input_scopes": ['megastructure', 'planet', 'country', 'ship', 'pop', 'pop_group', 'fleet', 'galactic_object', 'leader', 'army', 'bypass', 'pop_faction', 'starbase', 'deposit', 'sector', 'archaeological_site', 'first_contact', 'spy_network', 'espionage_operation', 'agreement', 'situation', 'debris', 'astral_rift'],
        "output_scope": 'unknown',
    },
    'owner_main_species': {
        "description": "Scopes to the main species of the owner of the current object. Works in every scope that 'owner' would work in.",
        "input_scopes": ['megastructure', 'planet', 'country', 'ship', 'pop', 'pop_group', 'fleet', 'galactic_object', 'leader', 'army', 'species', 'bypass', 'pop_faction', 'starbase', 'deposit', 'sector', 'archaeological_site', 'first_contact', 'spy_network', 'espionage_operation', 'agreement', 'situation', 'debris', 'astral_rift'],
        "output_scope": 'unknown',
    },
    'owner_or_space_owner': {
        "description": 'Scopes from an object to its owner if it exists, or to the owner of the space it is in otherwise. Works on all objects visible in star system view that can have an owner',
        "input_scopes": ['megastructure', 'planet', 'country', 'ship', 'fleet', 'galactic_object', 'army', 'starbase', 'archaeological_site', 'spy_network', 'debris'],
        "output_scope": 'unknown',
    },
    'owner_species': {
        "description": "Scopes to the main species of the owner of the current object. Works in every scope that 'owner' would work in.",
        "input_scopes": ['megastructure', 'planet', 'country', 'ship', 'pop', 'pop_group', 'fleet', 'galactic_object', 'leader', 'army', 'species', 'bypass', 'pop_faction', 'starbase', 'deposit', 'sector', 'archaeological_site', 'first_contact', 'spy_network', 'espionage_operation', 'agreement', 'situation', 'debris', 'astral_rift'],
        "output_scope": 'unknown',
    },
    'planet': {
        "description": 'Scopes from an object to the planet it is on. Works from army, megastructure, deposit and arc site scopes.',
        "input_scopes": ['megastructure', 'planet', 'pop', 'pop_group', 'leader', 'army', 'starbase', 'deposit', 'archaeological_site'],
        "output_scope": 'unknown',
    },
    'planet_owner': {
        "description": 'Scopes from an object to the owner of the planet it is on. Works from army, megastructure, deposit and arc site scopes.',
        "input_scopes": ['megastructure', 'planet', 'pop', 'pop_group', 'leader', 'army', 'starbase', 'deposit', 'archaeological_site'],
        "output_scope": 'unknown',
    },
    'pop_faction': {
        "description": 'Scopes from a pop or leader to its pop faction.',
        "input_scopes": ['pop', 'pop_group', 'leader', 'pop_faction'],
        "output_scope": 'unknown',
    },
    'prev': {
        "description": 'Scopes to the previous scope, e.g. owner = { capital_scope = { is_owned_by = prev } } would refer to the owner of the capital here (and always be true).',
        "input_scopes": ['all'],
        "output_scope": 'unknown',
    },
    'prevprev': {
        "description": 'Scopes back to two scope changes ago, e.g. planet = { owner = { any_owned_planet = { is_same_value = prevprev } } } would be checking if the owner of the planet owns any planet that is the same as the planet you are starting in (which would always be true).',
        "input_scopes": ['all'],
        "output_scope": 'unknown',
    },
    'prevprevprev': {
        "description": 'Scopes back to three scope changes ago (the PREV of PREVPREV).',
        "input_scopes": ['all'],
        "output_scope": 'unknown',
    },
    'prevprevprevprev': {
        "description": 'Scopes back to four scope changes ago (the PREV of PREVPREVPREV).',
        "input_scopes": ['all'],
        "output_scope": 'unknown',
    },
    'research_station': {
        "description": 'Scopes from a planet to the research station in orbit of it.',
        "input_scopes": ['planet'],
        "output_scope": 'unknown',
    },
    'reverse_first_contact': {
        "description": "Scopes from a first contact site to the equivalent one that the contact_country has on the site's owner.",
        "input_scopes": ['first_contact'],
        "output_scope": 'unknown',
    },
    'root': {
        "description": 'Scopes to the original scope of this context, e.g. the country of a country_event.',
        "input_scopes": ['all'],
        "output_scope": 'unknown',
    },
    'ruler': {
        "description": "Scopes to the ruler of a country (or the ruler of the object's owner).",
        "input_scopes": ['megastructure', 'planet', 'country', 'ship', 'pop', 'pop_group', 'fleet', 'galactic_object', 'leader', 'army', 'bypass', 'pop_faction', 'starbase', 'deposit', 'sector', 'archaeological_site', 'first_contact', 'spy_network', 'espionage_operation', 'agreement', 'situation', 'debris', 'astral_rift'],
        "output_scope": 'unknown',
    },
    'sector': {
        "description": 'Scopes from an object to the sector it is in. Works on all objects visible objects visible in star system view, plus star systems themselves and leaders (scopes to the sector the leader is currently located in, not necessarily the one they are assigned to as a governor).',
        "input_scopes": ['megastructure', 'planet', 'ship', 'pop', 'pop_group', 'fleet', 'galactic_object', 'leader', 'army', 'ambient_object', 'bypass', 'starbase', 'deposit', 'sector', 'archaeological_site', 'first_contact', 'debris'],
        "output_scope": 'unknown',
    },
    'sector_capital': {
        "description": 'Scopes from a sector to its capital planet.',
        "input_scopes": ['sector'],
        "output_scope": 'unknown',
    },
    'ship_growth_stage': {
        "description": "Scopes to the ship's current growth stage inside the ship's design",
        "input_scopes": ['ship'],
        "output_scope": 'unknown',
    },
    'solar_system': {
        "description": 'Scopes from an object to the solar system it is in. Works on all objects visible in star system view.',
        "input_scopes": ['megastructure', 'planet', 'country', 'ship', 'pop', 'pop_group', 'fleet', 'galactic_object', 'leader', 'army', 'ambient_object', 'bypass', 'starbase', 'deposit', 'archaeological_site', 'first_contact', 'debris', 'astral_rift'],
        "output_scope": 'unknown',
    },
    'space_owner': {
        "description": 'Scopes from an object to the owner of the space it is in. Works on all objects visible in star system view.',
        "input_scopes": ['megastructure', 'planet', 'country', 'ship', 'fleet', 'galactic_object', 'army', 'ambient_object', 'starbase', 'archaeological_site', 'spy_network', 'debris'],
        "output_scope": 'unknown',
    },
    'spawner_planet': {
        "description": 'Scopes from an army to the planet that spawned it.',
        "input_scopes": ['army'],
        "output_scope": 'unknown',
    },
    'species': {
        "description": 'Scopes from a country, leader, pop, army or (colonist) ship to its species.',
        "input_scopes": ['country', 'ship', 'pop', 'pop_group', 'leader', 'army', 'species'],
        "output_scope": 'unknown',
    },
    'spynetwork': {
        "description": 'Scopes from an espionage operation or spymaster envoy to its spy network.',
        "input_scopes": ['leader', 'espionage_operation'],
        "output_scope": 'unknown',
    },
    'star': {
        "description": 'Scopes from an object to the primary star (planet scope) of the system it is in. Works on all objects visible in star system view.',
        "input_scopes": ['megastructure', 'planet', 'ship', 'fleet', 'galactic_object', 'ambient_object', 'bypass', 'starbase', 'archaeological_site', 'first_contact', 'debris', 'astral_rift'],
        "output_scope": 'unknown',
    },
    'starbase': {
        "description": "Scopes from a solar system or planet to that system's starbase. Alternatively, scopes from a fleet or ship that is a starbase to its matching starbase scope.",
        "input_scopes": ['planet', 'ship', 'fleet', 'galactic_object', 'starbase'],
        "output_scope": 'unknown',
    },
    'storm_influence_field': {
        "description": 'Scopes from a galactic object to an inluence field with the galactic object as center',
        "input_scopes": ['galactic_object'],
        "output_scope": 'unknown',
    },
    'system_star': {
        "description": 'Scopes from an object to the primary star (planet scope) of the system it is in. Works on all objects visible in star system view.',
        "input_scopes": ['megastructure', 'planet', 'country', 'ship', 'pop', 'pop_group', 'fleet', 'galactic_object', 'leader', 'army', 'ambient_object', 'bypass', 'starbase', 'deposit', 'archaeological_site', 'first_contact', 'debris', 'astral_rift'],
        "output_scope": 'unknown',
    },
    'target': {
        "description": 'Scopes from a spy network to its target country, or from an espionage operation to its target (can be various objects, as set in common/espionage_operation_types).',
        "input_scopes": ['spy_network', 'espionage_operation', 'agreement', 'situation'],
        "output_scope": 'unknown',
    },
    'target_system': {
        "description": 'Scopes from a cosmic storm to the galactic object that it is heading torwards.',
        "input_scopes": ['cosmic_storm'],
        "output_scope": 'unknown',
    },
    'this': {
        "description": 'Scopes to the current scope.',
        "input_scopes": ['all'],
        "output_scope": 'unknown',
    },
    'unhappiest_pop': {
        "description": 'Scopes from a country or planet to its unhappiest pop group.',
        "input_scopes": ['planet', 'country'],
        "output_scope": 'unknown',
    },
}
