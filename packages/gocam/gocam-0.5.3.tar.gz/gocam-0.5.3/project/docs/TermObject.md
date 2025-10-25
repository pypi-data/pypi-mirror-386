
# Class: TermObject

An abstract class for all ontology term objects

URI: [gocam:TermObject](https://w3id.org/gocam/TermObject)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[QueryIndex]++-%20annoton_terms%200..*>[TermObject&#124;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[QueryIndex]++-%20model_activity_enabled_by_closure%200..*>[TermObject],[QueryIndex]++-%20model_activity_enabled_by_rollup%200..*>[TermObject],[QueryIndex]++-%20model_activity_enabled_by_terms%200..*>[TermObject],[QueryIndex]++-%20model_activity_has_input_closure%200..*>[TermObject],[QueryIndex]++-%20model_activity_has_input_rollup%200..*>[TermObject],[QueryIndex]++-%20model_activity_has_input_terms%200..*>[TermObject],[QueryIndex]++-%20model_activity_molecular_function_closure%200..*>[TermObject],[QueryIndex]++-%20model_activity_molecular_function_rollup%200..*>[TermObject],[QueryIndex]++-%20model_activity_molecular_function_terms%200..*>[TermObject],[QueryIndex]++-%20model_activity_occurs_in_closure%200..*>[TermObject],[QueryIndex]++-%20model_activity_occurs_in_rollup%200..*>[TermObject],[QueryIndex]++-%20model_activity_occurs_in_terms%200..*>[TermObject],[QueryIndex]++-%20model_activity_part_of_closure%200..*>[TermObject],[QueryIndex]++-%20model_activity_part_of_rollup%200..*>[TermObject],[QueryIndex]++-%20model_activity_part_of_terms%200..*>[TermObject],[QueryIndex]++-%20model_taxon%200..*>[TermObject],[QueryIndex]++-%20model_taxon_closure%200..*>[TermObject],[QueryIndex]++-%20model_taxon_rollup%200..*>[TermObject],[TermAssociation]-%20term%200..1>[TermObject],[TermObject]^-[TaxonTermObject],[TermObject]^-[PredicateTermObject],[TermObject]^-[PhaseTermObject],[TermObject]^-[MoleculeTermObject],[TermObject]^-[MolecularFunctionTermObject],[TermObject]^-[InformationBiomacromoleculeTermObject],[TermObject]^-[GrossAnatomicalStructureTermObject],[TermObject]^-[EvidenceTermObject],[TermObject]^-[CellularAnatomicalEntityTermObject],[TermObject]^-[CellTypeTermObject],[TermObject]^-[BiologicalProcessTermObject],[Object]^-[TermObject],[TermAssociation],[TaxonTermObject],[QueryIndex],[PredicateTermObject],[PhaseTermObject],[Object],[MoleculeTermObject],[MolecularFunctionTermObject],[InformationBiomacromoleculeTermObject],[GrossAnatomicalStructureTermObject],[EvidenceTermObject],[CellularAnatomicalEntityTermObject],[CellTypeTermObject],[BiologicalProcessTermObject])](https://yuml.me/diagram/nofunky;dir:TB/class/[QueryIndex]++-%20annoton_terms%200..*>[TermObject&#124;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[QueryIndex]++-%20model_activity_enabled_by_closure%200..*>[TermObject],[QueryIndex]++-%20model_activity_enabled_by_rollup%200..*>[TermObject],[QueryIndex]++-%20model_activity_enabled_by_terms%200..*>[TermObject],[QueryIndex]++-%20model_activity_has_input_closure%200..*>[TermObject],[QueryIndex]++-%20model_activity_has_input_rollup%200..*>[TermObject],[QueryIndex]++-%20model_activity_has_input_terms%200..*>[TermObject],[QueryIndex]++-%20model_activity_molecular_function_closure%200..*>[TermObject],[QueryIndex]++-%20model_activity_molecular_function_rollup%200..*>[TermObject],[QueryIndex]++-%20model_activity_molecular_function_terms%200..*>[TermObject],[QueryIndex]++-%20model_activity_occurs_in_closure%200..*>[TermObject],[QueryIndex]++-%20model_activity_occurs_in_rollup%200..*>[TermObject],[QueryIndex]++-%20model_activity_occurs_in_terms%200..*>[TermObject],[QueryIndex]++-%20model_activity_part_of_closure%200..*>[TermObject],[QueryIndex]++-%20model_activity_part_of_rollup%200..*>[TermObject],[QueryIndex]++-%20model_activity_part_of_terms%200..*>[TermObject],[QueryIndex]++-%20model_taxon%200..*>[TermObject],[QueryIndex]++-%20model_taxon_closure%200..*>[TermObject],[QueryIndex]++-%20model_taxon_rollup%200..*>[TermObject],[TermAssociation]-%20term%200..1>[TermObject],[TermObject]^-[TaxonTermObject],[TermObject]^-[PredicateTermObject],[TermObject]^-[PhaseTermObject],[TermObject]^-[MoleculeTermObject],[TermObject]^-[MolecularFunctionTermObject],[TermObject]^-[InformationBiomacromoleculeTermObject],[TermObject]^-[GrossAnatomicalStructureTermObject],[TermObject]^-[EvidenceTermObject],[TermObject]^-[CellularAnatomicalEntityTermObject],[TermObject]^-[CellTypeTermObject],[TermObject]^-[BiologicalProcessTermObject],[Object]^-[TermObject],[TermAssociation],[TaxonTermObject],[QueryIndex],[PredicateTermObject],[PhaseTermObject],[Object],[MoleculeTermObject],[MolecularFunctionTermObject],[InformationBiomacromoleculeTermObject],[GrossAnatomicalStructureTermObject],[EvidenceTermObject],[CellularAnatomicalEntityTermObject],[CellTypeTermObject],[BiologicalProcessTermObject])

## Parents

 *  is_a: [Object](Object.md) - An abstract class for all identified objects in a model

## Children

 * [BiologicalProcessTermObject](BiologicalProcessTermObject.md) - A term object that represents a biological process term from GO
 * [CellTypeTermObject](CellTypeTermObject.md) - A term object that represents a cell type term from CL
 * [CellularAnatomicalEntityTermObject](CellularAnatomicalEntityTermObject.md) - A term object that represents a cellular anatomical entity term from GO
 * [EvidenceTermObject](EvidenceTermObject.md) - A term object that represents an evidence term from ECO. Only ECO terms that map up to a GO GAF evidence code should be used.
 * [GrossAnatomicalStructureTermObject](GrossAnatomicalStructureTermObject.md) - A term object that represents a gross anatomical structure term from UBERON
 * [InformationBiomacromoleculeTermObject](InformationBiomacromoleculeTermObject.md) - An abstract class for all information biomacromolecule term objects
 * [MolecularFunctionTermObject](MolecularFunctionTermObject.md) - A term object that represents a molecular function term from GO
 * [MoleculeTermObject](MoleculeTermObject.md) - A term object that represents a molecule term from CHEBI or UniProtKB
 * [PhaseTermObject](PhaseTermObject.md) - A term object that represents a phase term from GO or UBERON
 * [PredicateTermObject](PredicateTermObject.md) - A term object that represents a taxon term from NCBITaxon
 * [TaxonTermObject](TaxonTermObject.md) - A term object that represents a taxon term from NCBITaxon

## Referenced by Class

 *  **None** *[➞annoton_terms](queryIndex__annoton_terms.md)*  <sub>0..\*</sub>  **[TermObject](TermObject.md)**
 *  **None** *[➞model_activity_enabled_by_closure](queryIndex__model_activity_enabled_by_closure.md)*  <sub>0..\*</sub>  **[TermObject](TermObject.md)**
 *  **None** *[➞model_activity_enabled_by_rollup](queryIndex__model_activity_enabled_by_rollup.md)*  <sub>0..\*</sub>  **[TermObject](TermObject.md)**
 *  **None** *[➞model_activity_enabled_by_terms](queryIndex__model_activity_enabled_by_terms.md)*  <sub>0..\*</sub>  **[TermObject](TermObject.md)**
 *  **None** *[➞model_activity_has_input_closure](queryIndex__model_activity_has_input_closure.md)*  <sub>0..\*</sub>  **[TermObject](TermObject.md)**
 *  **None** *[➞model_activity_has_input_rollup](queryIndex__model_activity_has_input_rollup.md)*  <sub>0..\*</sub>  **[TermObject](TermObject.md)**
 *  **None** *[➞model_activity_has_input_terms](queryIndex__model_activity_has_input_terms.md)*  <sub>0..\*</sub>  **[TermObject](TermObject.md)**
 *  **None** *[➞model_activity_molecular_function_closure](queryIndex__model_activity_molecular_function_closure.md)*  <sub>0..\*</sub>  **[TermObject](TermObject.md)**
 *  **None** *[➞model_activity_molecular_function_rollup](queryIndex__model_activity_molecular_function_rollup.md)*  <sub>0..\*</sub>  **[TermObject](TermObject.md)**
 *  **None** *[➞model_activity_molecular_function_terms](queryIndex__model_activity_molecular_function_terms.md)*  <sub>0..\*</sub>  **[TermObject](TermObject.md)**
 *  **None** *[➞model_activity_occurs_in_closure](queryIndex__model_activity_occurs_in_closure.md)*  <sub>0..\*</sub>  **[TermObject](TermObject.md)**
 *  **None** *[➞model_activity_occurs_in_rollup](queryIndex__model_activity_occurs_in_rollup.md)*  <sub>0..\*</sub>  **[TermObject](TermObject.md)**
 *  **None** *[➞model_activity_occurs_in_terms](queryIndex__model_activity_occurs_in_terms.md)*  <sub>0..\*</sub>  **[TermObject](TermObject.md)**
 *  **None** *[➞model_activity_part_of_closure](queryIndex__model_activity_part_of_closure.md)*  <sub>0..\*</sub>  **[TermObject](TermObject.md)**
 *  **None** *[➞model_activity_part_of_rollup](queryIndex__model_activity_part_of_rollup.md)*  <sub>0..\*</sub>  **[TermObject](TermObject.md)**
 *  **None** *[➞model_activity_part_of_terms](queryIndex__model_activity_part_of_terms.md)*  <sub>0..\*</sub>  **[TermObject](TermObject.md)**
 *  **None** *[➞model_taxon](queryIndex__model_taxon.md)*  <sub>0..\*</sub>  **[TermObject](TermObject.md)**
 *  **None** *[➞model_taxon_closure](queryIndex__model_taxon_closure.md)*  <sub>0..\*</sub>  **[TermObject](TermObject.md)**
 *  **None** *[➞model_taxon_rollup](queryIndex__model_taxon_rollup.md)*  <sub>0..\*</sub>  **[TermObject](TermObject.md)**
 *  **None** *[term](term.md)*  <sub>0..1</sub>  **[TermObject](TermObject.md)**
 *  **None** *[➞term](termAssociation__term.md)*  <sub>0..1</sub>  **[TermObject](TermObject.md)**

## Attributes


### Inherited from Object:

 * [➞id](object__id.md)  <sub>1..1</sub>
     * Range: [Uriorcurie](types/Uriorcurie.md)
 * [➞label](object__label.md)  <sub>0..1</sub>
     * Range: [String](types/String.md)
 * [➞type](object__type.md)  <sub>0..1</sub>
     * Range: [Uriorcurie](types/Uriorcurie.md)
 * [➞obsolete](object__obsolete.md)  <sub>0..1</sub>
     * Range: [Boolean](types/Boolean.md)
