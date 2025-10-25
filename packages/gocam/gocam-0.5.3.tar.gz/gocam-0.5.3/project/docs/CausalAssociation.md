
# Class: CausalAssociation

A causal association between two activities

URI: [gocam:CausalAssociation](https://w3id.org/gocam/CausalAssociation)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[ProvenanceInfo],[PredicateTermObject],[EvidenceItem],[Activity]<downstream_activity%200..1-%20[CausalAssociation&#124;type(i):string%20%3F],[PredicateTermObject]<predicate%200..1-%20[CausalAssociation],[Activity]++-%20causal_associations%200..*>[CausalAssociation],[Association]^-[CausalAssociation],[Association],[Activity])](https://yuml.me/diagram/nofunky;dir:TB/class/[ProvenanceInfo],[PredicateTermObject],[EvidenceItem],[Activity]<downstream_activity%200..1-%20[CausalAssociation&#124;type(i):string%20%3F],[PredicateTermObject]<predicate%200..1-%20[CausalAssociation],[Activity]++-%20causal_associations%200..*>[CausalAssociation],[Association]^-[CausalAssociation],[Association],[Activity])

## Parents

 *  is_a: [Association](Association.md) - An abstract grouping for different kinds of evidence-associated provenance

## Referenced by Class

 *  **None** *[➞causal_associations](activity__causal_associations.md)*  <sub>0..\*</sub>  **[CausalAssociation](CausalAssociation.md)**

## Attributes


### Own

 * [➞predicate](causalAssociation__predicate.md)  <sub>0..1</sub>
     * Description: The RO relation that represents the type of relationship
     * Range: [PredicateTermObject](PredicateTermObject.md)
 * [➞downstream_activity](causalAssociation__downstream_activity.md)  <sub>0..1</sub>
     * Description: The activity unit that is downstream of this one
     * Range: [Activity](Activity.md)

### Inherited from Association:

 * [➞type](association__type.md)  <sub>0..1</sub>
     * Description: The type of association.
     * Range: [String](types/String.md)
 * [➞evidence](association__evidence.md)  <sub>0..\*</sub>
     * Description: The set of evidence items that support the association.
     * Range: [EvidenceItem](EvidenceItem.md)
 * [➞provenances](association__provenances.md)  <sub>0..\*</sub>
     * Description: The set of provenance objects that provide metadata about who made the association.
     * Range: [ProvenanceInfo](ProvenanceInfo.md)
