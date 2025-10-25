
# Class: TaxonTermObject

A term object that represents a taxon term from NCBITaxon

URI: [gocam:TaxonTermObject](https://w3id.org/gocam/TaxonTermObject)


[![img](https://yuml.me/diagram/nofunky;dir:TB/class/[TermObject],[Model]-%20additional_taxa%200..*>[TaxonTermObject&#124;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[Model]-%20taxon%200..1>[TaxonTermObject],[TermObject]^-[TaxonTermObject],[Model])](https://yuml.me/diagram/nofunky;dir:TB/class/[TermObject],[Model]-%20additional_taxa%200..*>[TaxonTermObject&#124;id(i):uriorcurie;label(i):string%20%3F;type(i):uriorcurie%20%3F;obsolete(i):boolean%20%3F],[Model]-%20taxon%200..1>[TaxonTermObject],[TermObject]^-[TaxonTermObject],[Model])

## Identifier prefixes

 * NCBITaxon

## Parents

 *  is_a: [TermObject](TermObject.md) - An abstract class for all ontology term objects

## Referenced by Class

 *  **None** *[➞additional_taxa](model__additional_taxa.md)*  <sub>0..\*</sub>  **[TaxonTermObject](TaxonTermObject.md)**
 *  **None** *[➞taxon](model__taxon.md)*  <sub>0..1</sub>  **[TaxonTermObject](TaxonTermObject.md)**

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
