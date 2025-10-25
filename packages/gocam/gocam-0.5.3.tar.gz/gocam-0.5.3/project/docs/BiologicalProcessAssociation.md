
# Class: BiologicalProcessAssociation

An association between an activity and a biological process term

URI: [gocam:BiologicalProcessAssociation](https://w3id.org/gocam/BiologicalProcessAssociation)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[TermAssociation],[ProvenanceInfo],[PhaseTermObject],[EvidenceItem],[BiologicalProcessTermObject],[BiologicalProcessTermObject]<term%200..1-%20[BiologicalProcessAssociation&#124;type(i):string%20%3F],[BiologicalProcessAssociation]<part_of%200..1-++[BiologicalProcessAssociation],[PhaseTermObject]<happens_during%200..1-%20[BiologicalProcessAssociation],[Activity]++-%20part_of%200..1>[BiologicalProcessAssociation],[TermAssociation]^-[BiologicalProcessAssociation],[Activity])](https://yuml.me/diagram/nofunky;dir:TB/class/[TermAssociation],[ProvenanceInfo],[PhaseTermObject],[EvidenceItem],[BiologicalProcessTermObject],[BiologicalProcessTermObject]<term%200..1-%20[BiologicalProcessAssociation&#124;type(i):string%20%3F],[BiologicalProcessAssociation]<part_of%200..1-++[BiologicalProcessAssociation],[PhaseTermObject]<happens_during%200..1-%20[BiologicalProcessAssociation],[Activity]++-%20part_of%200..1>[BiologicalProcessAssociation],[TermAssociation]^-[BiologicalProcessAssociation],[Activity])

## Parents

 *  is_a: [TermAssociation](TermAssociation.md) - An association between an activity and a term, potentially with extensions. This is an abstract class for grouping purposes, it should not be directly instantiated, instead a subclass should be instantiated.

## Referenced by Class

 *  **None** *[➞part_of](activity__part_of.md)*  <sub>0..1</sub>  **[BiologicalProcessAssociation](BiologicalProcessAssociation.md)**
 *  **None** *[➞part_of](biologicalProcessAssociation__part_of.md)*  <sub>0..1</sub>  **[BiologicalProcessAssociation](BiologicalProcessAssociation.md)**

## Attributes


### Own

 * [➞happens_during](biologicalProcessAssociation__happens_during.md)  <sub>0..1</sub>
     * Description: Optional extension describing where the BP takes place
     * Range: [PhaseTermObject](PhaseTermObject.md)
 * [➞part_of](biologicalProcessAssociation__part_of.md)  <sub>0..1</sub>
     * Description: Optional extension allowing hierarchical nesting of BPs
     * Range: [BiologicalProcessAssociation](BiologicalProcessAssociation.md)
 * [BiologicalProcessAssociation➞term](BiologicalProcessAssociation_term.md)  <sub>0..1</sub>
     * Description: A generic slot for ontology terms
     * Range: [BiologicalProcessTermObject](BiologicalProcessTermObject.md)

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
