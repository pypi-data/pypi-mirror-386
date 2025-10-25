
# Class: PredicateTermObject

A term object that represents a taxon term from NCBITaxon

URI: [gocam:PredicateTermObject](https://w3id.org/gocam/PredicateTermObject)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[TermObject],[CausalAssociation]-%20predicate%200..1>[PredicateTermObject&#124;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[TermObject]^-[PredicateTermObject],[CausalAssociation])](https://yuml.me/diagram/nofunky;dir:TB/class/[TermObject],[CausalAssociation]-%20predicate%200..1>[PredicateTermObject&#124;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[TermObject]^-[PredicateTermObject],[CausalAssociation])

## Identifier prefixes

 * RO

## Parents

 *  is_a: [TermObject](TermObject.md) - An abstract class for all ontology term objects

## Referenced by Class

 *  **None** *[➞predicate](causalAssociation__predicate.md)*  <sub>0..1</sub>  **[PredicateTermObject](PredicateTermObject.md)**

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
