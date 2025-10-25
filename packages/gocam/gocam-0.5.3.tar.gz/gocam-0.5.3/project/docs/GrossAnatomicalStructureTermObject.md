
# Class: GrossAnatomicalStructureTermObject

A term object that represents a gross anatomical structure term from UBERON

URI: [gocam:GrossAnatomicalStructureTermObject](https://w3id.org/gocam/GrossAnatomicalStructureTermObject)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[TermObject],[GrossAnatomyAssociation],[GrossAnatomyAssociation]-%20term%200..1>[GrossAnatomicalStructureTermObject&#124;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[TermObject]^-[GrossAnatomicalStructureTermObject])](https://yuml.me/diagram/nofunky;dir:TB/class/[TermObject],[GrossAnatomyAssociation],[GrossAnatomyAssociation]-%20term%200..1>[GrossAnatomicalStructureTermObject&#124;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[TermObject]^-[GrossAnatomicalStructureTermObject])

## Identifier prefixes

 * UBERON
 * PO
 * FAO
 * DDANAT

## Parents

 *  is_a: [TermObject](TermObject.md) - An abstract class for all ontology term objects

## Referenced by Class

 *  **[GrossAnatomyAssociation](GrossAnatomyAssociation.md)** *[GrossAnatomyAssociation➞term](GrossAnatomyAssociation_term.md)*  <sub>0..1</sub>  **[GrossAnatomicalStructureTermObject](GrossAnatomicalStructureTermObject.md)**

## Attributes


### Inherited from TermObject:

 * [➞id](object__id.md)  <sub>1..1</sub>
     * Range: [Uriorcurie](types/Uriorcurie.md)
 * [➞label](object__label.md)  <sub>0..1</sub>
     * Range: [String](types/String.md)
 * [➞type](object__type.md)  <sub>0..1</sub>
     * Range: [Uriorcurie](types/Uriorcurie.md)
 * [➞obsolete](object__obsolete.md)  <sub>0..1</sub>
     * Range: [Boolean](types/Boolean.md)
