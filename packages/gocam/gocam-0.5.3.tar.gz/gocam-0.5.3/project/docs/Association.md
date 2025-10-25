
# Class: Association

An abstract grouping for different kinds of evidence-associated provenance

URI: [gocam:Association](https://w3id.org/gocam/Association)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[TermAssociation],[ProvenanceInfo],[EvidenceItem],[EnabledByAssociation],[CausalAssociation],[ProvenanceInfo]<provenances%200..*-++[Association&#124;type:string%20%3F],[EvidenceItem]<evidence%200..*-++[Association],[Association]^-[TermAssociation],[Association]^-[EnabledByAssociation],[Association]^-[CausalAssociation])](https://yuml.me/diagram/nofunky;dir:TB/class/[TermAssociation],[ProvenanceInfo],[EvidenceItem],[EnabledByAssociation],[CausalAssociation],[ProvenanceInfo]<provenances%200..*-++[Association&#124;type:string%20%3F],[EvidenceItem]<evidence%200..*-++[Association],[Association]^-[TermAssociation],[Association]^-[EnabledByAssociation],[Association]^-[CausalAssociation])

## Children

 * [CausalAssociation](CausalAssociation.md) - A causal association between two activities
 * [EnabledByAssociation](EnabledByAssociation.md) - An association between an activity and the gene product or complex or set of potential gene products
 * [TermAssociation](TermAssociation.md) - An association between an activity and a term, potentially with extensions. This is an abstract class for grouping purposes, it should not be directly instantiated, instead a subclass should be instantiated.

## Referenced by Class


## Attributes


### Own

 * [➞type](association__type.md)  <sub>0..1</sub>
     * Description: The type of association.
     * Range: [String](types/String.md)
 * [➞evidence](association__evidence.md)  <sub>0..\*</sub>
     * Description: The set of evidence items that support the association.
     * Range: [EvidenceItem](EvidenceItem.md)
 * [➞provenances](association__provenances.md)  <sub>0..\*</sub>
     * Description: The set of provenance objects that provide metadata about who made the association.
     * Range: [ProvenanceInfo](ProvenanceInfo.md)
