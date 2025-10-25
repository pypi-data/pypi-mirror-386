
# Class: MoleculeAssociation

An association between an activity and a molecule term

URI: [gocam:MoleculeAssociation](https://w3id.org/gocam/MoleculeAssociation)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[TermAssociation],[ProvenanceInfo],[MoleculeTermObject],[MoleculeTermObject]<term%200..1-%20[MoleculeAssociation&#124;type(i):string%20%3F],[Activity]++-%20has_input%200..*>[MoleculeAssociation],[Activity]++-%20has_output%200..*>[MoleculeAssociation],[Activity]++-%20has_primary_input%200..1>[MoleculeAssociation],[Activity]++-%20has_primary_output%200..1>[MoleculeAssociation],[TermAssociation]^-[MoleculeAssociation],[EvidenceItem],[Activity])](https://yuml.me/diagram/nofunky;dir:TB/class/[TermAssociation],[ProvenanceInfo],[MoleculeTermObject],[MoleculeTermObject]<term%200..1-%20[MoleculeAssociation&#124;type(i):string%20%3F],[Activity]++-%20has_input%200..*>[MoleculeAssociation],[Activity]++-%20has_output%200..*>[MoleculeAssociation],[Activity]++-%20has_primary_input%200..1>[MoleculeAssociation],[Activity]++-%20has_primary_output%200..1>[MoleculeAssociation],[TermAssociation]^-[MoleculeAssociation],[EvidenceItem],[Activity])

## Parents

 *  is_a: [TermAssociation](TermAssociation.md) - An association between an activity and a term, potentially with extensions. This is an abstract class for grouping purposes, it should not be directly instantiated, instead a subclass should be instantiated.

## Referenced by Class

 *  **None** *[➞has_input](activity__has_input.md)*  <sub>0..\*</sub>  **[MoleculeAssociation](MoleculeAssociation.md)**
 *  **None** *[➞has_output](activity__has_output.md)*  <sub>0..\*</sub>  **[MoleculeAssociation](MoleculeAssociation.md)**
 *  **None** *[➞has_primary_input](activity__has_primary_input.md)*  <sub>0..1</sub>  **[MoleculeAssociation](MoleculeAssociation.md)**
 *  **None** *[➞has_primary_output](activity__has_primary_output.md)*  <sub>0..1</sub>  **[MoleculeAssociation](MoleculeAssociation.md)**

## Attributes


### Own

 * [MoleculeAssociation➞term](MoleculeAssociation_term.md)  <sub>0..1</sub>
     * Description: A generic slot for ontology terms
     * Range: [MoleculeTermObject](MoleculeTermObject.md)

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
