
# Class: GrossAnatomyAssociation

An association between an activity and a gross anatomical structure term

URI: [gocam:GrossAnatomyAssociation](https://w3id.org/gocam/GrossAnatomyAssociation)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[TermAssociation],[ProvenanceInfo],[GrossAnatomicalStructureTermObject]<term%200..1-%20[GrossAnatomyAssociation&#124;type(i):string%20%3F],[GrossAnatomyAssociation]<part_of%200..1-++[GrossAnatomyAssociation],[CellTypeAssociation]++-%20part_of%200..1>[GrossAnatomyAssociation],[TermAssociation]^-[GrossAnatomyAssociation],[GrossAnatomicalStructureTermObject],[EvidenceItem],[CellTypeAssociation])](https://yuml.me/diagram/nofunky;dir:TB/class/[TermAssociation],[ProvenanceInfo],[GrossAnatomicalStructureTermObject]<term%200..1-%20[GrossAnatomyAssociation&#124;type(i):string%20%3F],[GrossAnatomyAssociation]<part_of%200..1-++[GrossAnatomyAssociation],[CellTypeAssociation]++-%20part_of%200..1>[GrossAnatomyAssociation],[TermAssociation]^-[GrossAnatomyAssociation],[GrossAnatomicalStructureTermObject],[EvidenceItem],[CellTypeAssociation])

## Parents

 *  is_a: [TermAssociation](TermAssociation.md) - An association between an activity and a term, potentially with extensions. This is an abstract class for grouping purposes, it should not be directly instantiated, instead a subclass should be instantiated.

## Referenced by Class

 *  **None** *[➞part_of](cellTypeAssociation__part_of.md)*  <sub>0..1</sub>  **[GrossAnatomyAssociation](GrossAnatomyAssociation.md)**
 *  **None** *[➞part_of](grossAnatomyAssociation__part_of.md)*  <sub>0..1</sub>  **[GrossAnatomyAssociation](GrossAnatomyAssociation.md)**

## Attributes


### Own

 * [➞part_of](grossAnatomyAssociation__part_of.md)  <sub>0..1</sub>
     * Range: [GrossAnatomyAssociation](GrossAnatomyAssociation.md)
 * [GrossAnatomyAssociation➞term](GrossAnatomyAssociation_term.md)  <sub>0..1</sub>
     * Description: A generic slot for ontology terms
     * Range: [GrossAnatomicalStructureTermObject](GrossAnatomicalStructureTermObject.md)

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
