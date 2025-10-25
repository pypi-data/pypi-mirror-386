
# Class: EvidenceItem

An individual piece of evidence that is associated with an assertion in a model

URI: [gocam:EvidenceItem](https://w3id.org/gocam/EvidenceItem)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[PublicationObject],[ProvenanceInfo],[Object],[EvidenceTermObject],[ProvenanceInfo]<provenances%200..*-++[EvidenceItem],[Object]<with_objects%200..*-%20[EvidenceItem],[PublicationObject]<reference%200..1-%20[EvidenceItem],[EvidenceTermObject]<term%200..1-%20[EvidenceItem],[Association]++-%20evidence%200..*>[EvidenceItem],[Association])](https://yuml.me/diagram/nofunky;dir:TB/class/[PublicationObject],[ProvenanceInfo],[Object],[EvidenceTermObject],[ProvenanceInfo]<provenances%200..*-++[EvidenceItem],[Object]<with_objects%200..*-%20[EvidenceItem],[PublicationObject]<reference%200..1-%20[EvidenceItem],[EvidenceTermObject]<term%200..1-%20[EvidenceItem],[Association]++-%20evidence%200..*>[EvidenceItem],[Association])

## Referenced by Class

 *  **None** *[➞evidence](association__evidence.md)*  <sub>0..\*</sub>  **[EvidenceItem](EvidenceItem.md)**

## Attributes


### Own

 * [➞term](evidenceItem__term.md)  <sub>0..1</sub>
     * Description: The ECO term representing the type of evidence
     * Range: [EvidenceTermObject](EvidenceTermObject.md)
     * Example: ECO:0000314 direct assay evidence used in manual assertion (IDA)
 * [➞reference](evidenceItem__reference.md)  <sub>0..1</sub>
     * Description: The publication of reference that describes the evidence
     * Range: [PublicationObject](PublicationObject.md)
     * Example: PMID:32075755 None
 * [➞with_objects](evidenceItem__with_objects.md)  <sub>0..\*</sub>
     * Description: Supporting database entities or terms
     * Range: [Object](Object.md)
 * [➞provenances](evidenceItem__provenances.md)  <sub>0..\*</sub>
     * Description: Provenance about the assertion, e.g. who made it
     * Range: [ProvenanceInfo](ProvenanceInfo.md)
