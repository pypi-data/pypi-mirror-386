
# Class: PublicationObject

An object that represents a publication or other kind of reference

URI: [gocam:PublicationObject](https://w3id.org/gocam/PublicationObject)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[EvidenceItem]-%20reference%200..1>[PublicationObject&#124;abstract_text:string%20%3F;full_text:string%20%3F;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[QueryIndex]++-%20flattened_references%200..*>[PublicationObject],[Object]^-[PublicationObject],[QueryIndex],[Object],[EvidenceItem])](https://yuml.me/diagram/nofunky;dir:TB/class/[EvidenceItem]-%20reference%200..1>[PublicationObject&#124;abstract_text:string%20%3F;full_text:string%20%3F;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[QueryIndex]++-%20flattened_references%200..*>[PublicationObject],[Object]^-[PublicationObject],[QueryIndex],[Object],[EvidenceItem])

## Identifier prefixes

 * PMID
 * GOREF
 * DOI

## Parents

 *  is_a: [Object](Object.md) - An abstract class for all identified objects in a model

## Referenced by Class

 *  **None** *[➞reference](evidenceItem__reference.md)*  <sub>0..1</sub>  **[PublicationObject](PublicationObject.md)**
 *  **None** *[➞flattened_references](queryIndex__flattened_references.md)*  <sub>0..\*</sub>  **[PublicationObject](PublicationObject.md)**

## Attributes


### Own

 * [➞abstract_text](publicationObject__abstract_text.md)  <sub>0..1</sub>
     * Range: [String](types/String.md)
 * [➞full_text](publicationObject__full_text.md)  <sub>0..1</sub>
     * Range: [String](types/String.md)

### Inherited from Object:

 * [➞id](object__id.md)  <sub>1..1</sub>
     * Range: [Uriorcurie](types/Uriorcurie.md)
 * [➞label](object__label.md)  <sub>0..1</sub>
     * Range: [String](types/String.md)
 * [➞type](object__type.md)  <sub>0..1</sub>
     * Range: [Uriorcurie](types/Uriorcurie.md)
 * [➞obsolete](object__obsolete.md)  <sub>0..1</sub>
     * Range: [Boolean](types/Boolean.md)
