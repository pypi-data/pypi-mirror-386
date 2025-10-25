
# Class: Object

An abstract class for all identified objects in a model

URI: [gocam:Object](https://w3id.org/gocam/Object)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[TermObject],[PublicationObject],[EvidenceItem]-%20with_objects%200..*>[Object&#124;id:uriorcurie;label:string%20%3F;type:uriorcurie%20%3F;obsolete:boolean%20%3F],[Model]++-%20objects%200..*>[Object],[Object]^-[TermObject],[Object]^-[PublicationObject],[Model],[EvidenceItem])](https://yuml.me/diagram/nofunky;dir:TB/class/[TermObject],[PublicationObject],[EvidenceItem]-%20with_objects%200..*>[Object&#124;id:uriorcurie;label:string%20%3F;type:uriorcurie%20%3F;obsolete:boolean%20%3F],[Model]++-%20objects%200..*>[Object],[Object]^-[TermObject],[Object]^-[PublicationObject],[Model],[EvidenceItem])

## Children

 * [PublicationObject](PublicationObject.md) - An object that represents a publication or other kind of reference
 * [TermObject](TermObject.md) - An abstract class for all ontology term objects

## Referenced by Class

 *  **None** *[➞with_objects](evidenceItem__with_objects.md)*  <sub>0..\*</sub>  **[Object](Object.md)**
 *  **None** *[➞objects](model__objects.md)*  <sub>0..\*</sub>  **[Object](Object.md)**

## Attributes


### Own

 * [➞id](object__id.md)  <sub>1..1</sub>
     * Range: [Uriorcurie](types/Uriorcurie.md)
 * [➞label](object__label.md)  <sub>0..1</sub>
     * Range: [String](types/String.md)
 * [➞type](object__type.md)  <sub>0..1</sub>
     * Range: [Uriorcurie](types/Uriorcurie.md)
 * [➞obsolete](object__obsolete.md)  <sub>0..1</sub>
     * Range: [Boolean](types/Boolean.md)
