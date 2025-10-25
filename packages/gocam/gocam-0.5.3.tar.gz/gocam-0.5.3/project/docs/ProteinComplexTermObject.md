
# Class: ProteinComplexTermObject

A term object that represents a protein complex term from GO

URI: [gocam:ProteinComplexTermObject](https://w3id.org/gocam/ProteinComplexTermObject)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[EnabledByProteinComplexAssociation]-%20term%200..1>[ProteinComplexTermObject&#124;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[InformationBiomacromoleculeTermObject]^-[ProteinComplexTermObject],[InformationBiomacromoleculeTermObject],[EnabledByProteinComplexAssociation])](https://yuml.me/diagram/nofunky;dir:TB/class/[EnabledByProteinComplexAssociation]-%20term%200..1>[ProteinComplexTermObject&#124;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[InformationBiomacromoleculeTermObject]^-[ProteinComplexTermObject],[InformationBiomacromoleculeTermObject],[EnabledByProteinComplexAssociation])

## Parents

 *  is_a: [InformationBiomacromoleculeTermObject](InformationBiomacromoleculeTermObject.md) - An abstract class for all information biomacromolecule term objects

## Referenced by Class

 *  **[EnabledByProteinComplexAssociation](EnabledByProteinComplexAssociation.md)** *[EnabledByProteinComplexAssociation➞term](EnabledByProteinComplexAssociation_term.md)*  <sub>0..1</sub>  **[ProteinComplexTermObject](ProteinComplexTermObject.md)**

## Attributes


### Inherited from InformationBiomacromoleculeTermObject:

 * [➞id](object__id.md)  <sub>1..1</sub>
     * Range: [Uriorcurie](types/Uriorcurie.md)
 * [➞label](object__label.md)  <sub>0..1</sub>
     * Range: [String](types/String.md)
 * [➞type](object__type.md)  <sub>0..1</sub>
     * Range: [Uriorcurie](types/Uriorcurie.md)
 * [➞obsolete](object__obsolete.md)  <sub>0..1</sub>
     * Range: [Boolean](types/Boolean.md)
