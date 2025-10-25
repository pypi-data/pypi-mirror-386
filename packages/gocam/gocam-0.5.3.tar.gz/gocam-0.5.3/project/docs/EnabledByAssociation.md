
# Class: EnabledByAssociation

An association between an activity and the gene product or complex or set of potential gene products
  that carry out that activity.

URI: [gocam:EnabledByAssociation](https://w3id.org/gocam/EnabledByAssociation)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[ProvenanceInfo],[InformationBiomacromoleculeTermObject],[EvidenceItem],[EnabledByProteinComplexAssociation],[EnabledByGeneProductAssociation],[InformationBiomacromoleculeTermObject]<term%200..1-%20[EnabledByAssociation&#124;type(i):string%20%3F],[Activity]++-%20enabled_by%200..1>[EnabledByAssociation],[EnabledByAssociation]^-[EnabledByProteinComplexAssociation],[EnabledByAssociation]^-[EnabledByGeneProductAssociation],[Association]^-[EnabledByAssociation],[Association],[Activity])](https://yuml.me/diagram/nofunky;dir:TB/class/[ProvenanceInfo],[InformationBiomacromoleculeTermObject],[EvidenceItem],[EnabledByProteinComplexAssociation],[EnabledByGeneProductAssociation],[InformationBiomacromoleculeTermObject]<term%200..1-%20[EnabledByAssociation&#124;type(i):string%20%3F],[Activity]++-%20enabled_by%200..1>[EnabledByAssociation],[EnabledByAssociation]^-[EnabledByProteinComplexAssociation],[EnabledByAssociation]^-[EnabledByGeneProductAssociation],[Association]^-[EnabledByAssociation],[Association],[Activity])

## Parents

 *  is_a: [Association](Association.md) - An abstract grouping for different kinds of evidence-associated provenance

## Children

 * [EnabledByGeneProductAssociation](EnabledByGeneProductAssociation.md) - An association between an activity and an individual gene product
 * [EnabledByProteinComplexAssociation](EnabledByProteinComplexAssociation.md) - An association between an activity and a protein complex, where the complex carries out the activity. This should only be used when the activity cannot be attributed to an individual member of the complex, but instead the function is an emergent property of the complex.

## Referenced by Class

 *  **None** *[➞enabled_by](activity__enabled_by.md)*  <sub>0..1</sub>  **[EnabledByAssociation](EnabledByAssociation.md)**

## Attributes


### Own

 * [➞term](enabledByAssociation__term.md)  <sub>0..1</sub>
     * Description: The gene product or complex that carries out the activity
     * Range: [InformationBiomacromoleculeTermObject](InformationBiomacromoleculeTermObject.md)

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

## Other properties

|  |  |  |
| --- | --- | --- |
| **Comments:** | | Note that this is an abstract class, and should ot be instantiated directly, instead instantiate a subclass depending on what kind of entity enables the association |
