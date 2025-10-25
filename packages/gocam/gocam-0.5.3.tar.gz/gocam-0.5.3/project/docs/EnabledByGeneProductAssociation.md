
# Class: EnabledByGeneProductAssociation

An association between an activity and an individual gene product

URI: [gocam:EnabledByGeneProductAssociation](https://w3id.org/gocam/EnabledByGeneProductAssociation)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[ProvenanceInfo],[GeneProductTermObject],[EvidenceItem],[GeneProductTermObject]<term%200..1-%20[EnabledByGeneProductAssociation&#124;type(i):string%20%3F],[EnabledByAssociation]^-[EnabledByGeneProductAssociation],[EnabledByAssociation])](https://yuml.me/diagram/nofunky;dir:TB/class/[ProvenanceInfo],[GeneProductTermObject],[EvidenceItem],[GeneProductTermObject]<term%200..1-%20[EnabledByGeneProductAssociation&#124;type(i):string%20%3F],[EnabledByAssociation]^-[EnabledByGeneProductAssociation],[EnabledByAssociation])

## Parents

 *  is_a: [EnabledByAssociation](EnabledByAssociation.md) - An association between an activity and the gene product or complex or set of potential gene products

## Referenced by Class


## Attributes


### Own

 * [EnabledByGeneProductAssociation➞term](EnabledByGeneProductAssociation_term.md)  <sub>0..1</sub>
     * Description: A "term" that is an entity database object representing an individual gene product.
     * Range: [GeneProductTermObject](GeneProductTermObject.md)
     * Example: UniProtKB:Q96Q11 The protein product of the Homo sapiens TRNT1 gene
     * Example: RNAcentral:URS00026A1FBE_9606 An RNA product of this RNA central gene

### Inherited from EnabledByAssociation:

 * [➞type](association__type.md)  <sub>0..1</sub>
     * Description: The type of association.
     * Range: [String](types/String.md)
 * [➞evidence](association__evidence.md)  <sub>0..\*</sub>
     * Description: The set of evidence items that support the association.
     * Range: [EvidenceItem](EvidenceItem.md)
 * [➞provenances](association__provenances.md)  <sub>0..\*</sub>
     * Description: The set of provenance objects that provide metadata about who made the association.
     * Range: [ProvenanceInfo](ProvenanceInfo.md)
