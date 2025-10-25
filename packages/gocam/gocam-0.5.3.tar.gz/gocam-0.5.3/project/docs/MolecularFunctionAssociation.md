
# Class: MolecularFunctionAssociation

An association between an activity and a molecular function term

URI: [gocam:MolecularFunctionAssociation](https://w3id.org/gocam/MolecularFunctionAssociation)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[TermAssociation],[ProvenanceInfo],[MolecularFunctionTermObject],[MolecularFunctionTermObject]<term%200..1-%20[MolecularFunctionAssociation&#124;type(i):string%20%3F],[Activity]++-%20molecular_function%200..1>[MolecularFunctionAssociation],[TermAssociation]^-[MolecularFunctionAssociation],[EvidenceItem],[Activity])](https://yuml.me/diagram/nofunky;dir:TB/class/[TermAssociation],[ProvenanceInfo],[MolecularFunctionTermObject],[MolecularFunctionTermObject]<term%200..1-%20[MolecularFunctionAssociation&#124;type(i):string%20%3F],[Activity]++-%20molecular_function%200..1>[MolecularFunctionAssociation],[TermAssociation]^-[MolecularFunctionAssociation],[EvidenceItem],[Activity])

## Parents

 *  is_a: [TermAssociation](TermAssociation.md) - An association between an activity and a term, potentially with extensions. This is an abstract class for grouping purposes, it should not be directly instantiated, instead a subclass should be instantiated.

## Referenced by Class

 *  **None** *[➞molecular_function](activity__molecular_function.md)*  <sub>0..1</sub>  **[MolecularFunctionAssociation](MolecularFunctionAssociation.md)**

## Attributes


### Own

 * [MolecularFunctionAssociation➞term](MolecularFunctionAssociation_term.md)  <sub>0..1</sub>
     * Description: A generic slot for ontology terms
     * Range: [MolecularFunctionTermObject](MolecularFunctionTermObject.md)

### Inherited from TermAssociation:

 * [➞type](association__type.md)  <sub>0..1</sub>
     * Description: The type of association.
     * Range: [String](types/String.md)
 * [➞evidence](association__evidence.md)  <sub>0..\*</sub>
     * Description: The set of evidence items that support the association.
     * Range: [EvidenceItem](EvidenceItem.md)
 * [➞provenances](association__provenances.md)  <sub>0..\*</sub>
     * Description: The set of provenance objects that provide metadata about who made the association.
     * Range: [ProvenanceInfo](ProvenanceInfo.md)
