
# gocam


**metamodel version:** 1.7.0

**version:** None


Gene Ontology Causal Activity Model (GO-CAM) Schema.

This schema provides a way of representing causal pathway [Models](Model.md). A model consists of a set of
[Activity](Activity.md) objects, where each activity object represents the function of either an [individual
gene product](EnabledByGeneProductAssociation), a [protein complex of gene products](EnabledByGeneProductAssociation),
or a set of possible gene products.

Each [Models](Model.md) has associated metadata slots. Some slots such as [id](id.md), [title](title.md),
and [status](status.md) are *required*.


### Classes

 * [Activity](Activity.md) - An individual activity in a causal model, representing the individual molecular activity of a single gene product or complex in the context of a particular model
 * [Association](Association.md) - An abstract grouping for different kinds of evidence-associated provenance
     * [CausalAssociation](CausalAssociation.md) - A causal association between two activities
     * [EnabledByAssociation](EnabledByAssociation.md) - An association between an activity and the gene product or complex or set of potential gene products
         * [EnabledByGeneProductAssociation](EnabledByGeneProductAssociation.md) - An association between an activity and an individual gene product
         * [EnabledByProteinComplexAssociation](EnabledByProteinComplexAssociation.md) - An association between an activity and a protein complex, where the complex carries out the activity. This should only be used when the activity cannot be attributed to an individual member of the complex, but instead the function is an emergent property of the complex.
     * [TermAssociation](TermAssociation.md) - An association between an activity and a term, potentially with extensions. This is an abstract class for grouping purposes, it should not be directly instantiated, instead a subclass should be instantiated.
         * [BiologicalProcessAssociation](BiologicalProcessAssociation.md) - An association between an activity and a biological process term
         * [CellTypeAssociation](CellTypeAssociation.md) - An association between an activity and a cell type term
         * [CellularAnatomicalEntityAssociation](CellularAnatomicalEntityAssociation.md) - An association between an activity and a cellular anatomical entity term
         * [GrossAnatomyAssociation](GrossAnatomyAssociation.md) - An association between an activity and a gross anatomical structure term
         * [MolecularFunctionAssociation](MolecularFunctionAssociation.md) - An association between an activity and a molecular function term
         * [MoleculeAssociation](MoleculeAssociation.md) - An association between an activity and a molecule term
 * [EvidenceItem](EvidenceItem.md) - An individual piece of evidence that is associated with an assertion in a model
 * [Model](Model.md) - A model of a biological program consisting of a set of causally connected activities.
 * [Object](Object.md) - An abstract class for all identified objects in a model
     * [PublicationObject](PublicationObject.md) - An object that represents a publication or other kind of reference
     * [TermObject](TermObject.md) - An abstract class for all ontology term objects
         * [BiologicalProcessTermObject](BiologicalProcessTermObject.md) - A term object that represents a biological process term from GO
         * [CellTypeTermObject](CellTypeTermObject.md) - A term object that represents a cell type term from CL
         * [CellularAnatomicalEntityTermObject](CellularAnatomicalEntityTermObject.md) - A term object that represents a cellular anatomical entity term from GO
         * [EvidenceTermObject](EvidenceTermObject.md) - A term object that represents an evidence term from ECO. Only ECO terms that map up to a GO GAF evidence code should be used.
         * [GrossAnatomicalStructureTermObject](GrossAnatomicalStructureTermObject.md) - A term object that represents a gross anatomical structure term from UBERON
         * [InformationBiomacromoleculeTermObject](InformationBiomacromoleculeTermObject.md) - An abstract class for all information biomacromolecule term objects
             * [GeneProductTermObject](GeneProductTermObject.md) - A term object that represents a gene product term from GO or UniProtKB
             * [ProteinComplexTermObject](ProteinComplexTermObject.md) - A term object that represents a protein complex term from GO
         * [MolecularFunctionTermObject](MolecularFunctionTermObject.md) - A term object that represents a molecular function term from GO
         * [MoleculeTermObject](MoleculeTermObject.md) - A term object that represents a molecule term from CHEBI or UniProtKB
         * [PhaseTermObject](PhaseTermObject.md) - A term object that represents a phase term from GO or UBERON
         * [PredicateTermObject](PredicateTermObject.md) - A term object that represents a taxon term from NCBITaxon
         * [TaxonTermObject](TaxonTermObject.md) - A term object that represents a taxon term from NCBITaxon
 * [ProvenanceInfo](ProvenanceInfo.md) - Provenance information for an object
 * [QueryIndex](QueryIndex.md) - An index that is optionally placed on a model in order to support common query or index operations. Note that this index is not typically populated in the working transactional store for a model, it is derived via computation from core primary model information.

### Mixins


### Slots

 * [➞causal_associations](activity__causal_associations.md) - The causal associations that flow out of this activity
 * [➞enabled_by](activity__enabled_by.md) - The gene product or complex that carries out the activity
 * [➞has_input](activity__has_input.md) - The input molecules that are directly consumed by the activity
 * [➞has_output](activity__has_output.md) - The output molecules that are directly produced by the activity
 * [➞has_primary_input](activity__has_primary_input.md) - The primary input molecule that is directly consumed by the activity
 * [➞has_primary_output](activity__has_primary_output.md) - The primary output molecule that is directly produced by the activity
 * [➞id](activity__id.md) - Identifier of the activity unit. Should be in gocam namespace.
 * [➞molecular_function](activity__molecular_function.md) - The molecular function that is carried out by the gene product or complex
 * [➞occurs_in](activity__occurs_in.md) - The cellular location in which the activity occurs
 * [➞part_of](activity__part_of.md) - The larger biological process in which the activity is a part
 * [➞provenances](activity__provenances.md) - Provenance information for the activity
 * [➞evidence](association__evidence.md) - The set of evidence items that support the association.
 * [➞provenances](association__provenances.md) - The set of provenance objects that provide metadata about who made the association.
 * [➞type](association__type.md) - The type of association.
 * [➞happens_during](biologicalProcessAssociation__happens_during.md) - Optional extension describing where the BP takes place
 * [➞part_of](biologicalProcessAssociation__part_of.md) - Optional extension allowing hierarchical nesting of BPs
 * [➞downstream_activity](causalAssociation__downstream_activity.md) - The activity unit that is downstream of this one
 * [➞predicate](causalAssociation__predicate.md) - The RO relation that represents the type of relationship
 * [➞part_of](cellTypeAssociation__part_of.md)
 * [➞part_of](cellularAnatomicalEntityAssociation__part_of.md) - Optional extension allowing hierarchical nesting of CCs
 * [➞term](enabledByAssociation__term.md) - The gene product or complex that carries out the activity
     * [EnabledByGeneProductAssociation➞term](EnabledByGeneProductAssociation_term.md) - A "term" that is an entity database object representing an individual gene product.
     * [EnabledByProteinComplexAssociation➞term](EnabledByProteinComplexAssociation_term.md) - A generic slot for ontology terms
 * [➞members](enabledByProteinComplexAssociation__members.md) - The gene products that are part of the complex
 * [➞provenances](evidenceItem__provenances.md) - Provenance about the assertion, e.g. who made it
 * [➞reference](evidenceItem__reference.md) - The publication of reference that describes the evidence
 * [➞term](evidenceItem__term.md) - The ECO term representing the type of evidence
 * [➞with_objects](evidenceItem__with_objects.md) - Supporting database entities or terms
 * [➞part_of](grossAnatomyAssociation__part_of.md)
 * [➞activities](model__activities.md) - All of the activities that are part of the model
 * [➞additional_taxa](model__additional_taxa.md) - Additional taxa that the model is about
 * [➞comments](model__comments.md) - Curator-provided comments about the model
 * [➞date_modified](model__date_modified.md) - The date that the model was last modified
 * [➞id](model__id.md) - The identifier of the model. Should be in gocam namespace.
 * [➞objects](model__objects.md) - All of the objects that are part of the model. This includes terms as well as publications and database objects like gene. This is not strictly part of the data managed by the model, it is for convenience, and should be refreshed from outside.
 * [➞provenances](model__provenances.md) - Model-level provenance information
 * [➞query_index](model__query_index.md) - An optional object that contains the results of indexing a model with various summary statistics and retrieval indices.
 * [➞status](model__status.md) - The status of the model in terms of its progression along the developmental lifecycle
 * [➞taxon](model__taxon.md) - The primary taxon that the model is about
 * [➞title](model__title.md) - The human-readable descriptive title of the model
 * [➞id](object__id.md)
 * [➞label](object__label.md)
 * [➞obsolete](object__obsolete.md)
 * [➞type](object__type.md)
 * [part_of](part_of.md) - A generic slot for part-of relationships
 * [➞contributor](provenanceInfo__contributor.md)
 * [➞created](provenanceInfo__created.md)
 * [➞date](provenanceInfo__date.md)
 * [➞provided_by](provenanceInfo__provided_by.md)
 * [provenances](provenances.md) - A generic slot for provenance information
 * [➞abstract_text](publicationObject__abstract_text.md)
 * [➞full_text](publicationObject__full_text.md)
 * [➞annoton_terms](queryIndex__annoton_terms.md)
 * [➞end_activities](queryIndex__end_activities.md) - The set of activities that are the end points of the model, i.e. those that have no outgoing causal associations.
 * [➞flattened_references](queryIndex__flattened_references.md) - All publication objects from the model across different levels combined in one place
 * [➞intermediate_activities](queryIndex__intermediate_activities.md) - The set of activities that are neither start nor end activities, i.e. those that have both incoming and outgoing causal associations.
 * [➞length_of_longest_causal_association_path](queryIndex__length_of_longest_causal_association_path.md) - The maximum number of hops along activities along the direction of causal flow in a model.
 * [➞model_activity_enabled_by_closure](queryIndex__model_activity_enabled_by_closure.md) - The reflexive transitive closure of `model_activity_enabled_by_terms`, over the is_a and has_part relationship type (e.g. complex to parts)
 * [➞model_activity_enabled_by_rollup](queryIndex__model_activity_enabled_by_rollup.md) - The rollup of `model_activity_enabled_by_closure` to a GO subset or slim.
 * [➞model_activity_enabled_by_terms](queryIndex__model_activity_enabled_by_terms.md) - All direct enabler terms for all activities
 * [➞model_activity_has_input_closure](queryIndex__model_activity_has_input_closure.md) - The reflexive transitive closure of `model_activity_has_input_terms`, over the is_a relationship type
 * [➞model_activity_has_input_rollup](queryIndex__model_activity_has_input_rollup.md) - The rollup of `model_activity_has_input_closure` to a GO subset or slim.
 * [➞model_activity_has_input_terms](queryIndex__model_activity_has_input_terms.md) - All direct input terms for all activities
 * [➞model_activity_molecular_function_closure](queryIndex__model_activity_molecular_function_closure.md) - The reflexive transitive closure of `model_activity_molecular_function_terms`, over the is_a relationship
 * [➞model_activity_molecular_function_rollup](queryIndex__model_activity_molecular_function_rollup.md) - The rollup of `model_activity_molecular_function_closure` to a GO subset or slim.
 * [➞model_activity_molecular_function_terms](queryIndex__model_activity_molecular_function_terms.md) - All MF terms for all activities
 * [➞model_activity_occurs_in_closure](queryIndex__model_activity_occurs_in_closure.md) - The reflexive transitive closure of `model_activity_occurs_in_terms`, over the is_a and part_of relationship type
 * [➞model_activity_occurs_in_rollup](queryIndex__model_activity_occurs_in_rollup.md) - The rollup of `model_activity_occurs_in_closure` to a GO subset or slim.
 * [➞model_activity_occurs_in_terms](queryIndex__model_activity_occurs_in_terms.md) - All direct cellular component localization terms for all activities
 * [➞model_activity_part_of_closure](queryIndex__model_activity_part_of_closure.md) - The reflexive transitive closure of `model_activity_part_of_terms`, over the is_a and part_of relationship type
 * [➞model_activity_part_of_rollup](queryIndex__model_activity_part_of_rollup.md) - The rollup of `model_activity_part_of_closure` to a GO subset or slim.
 * [➞model_activity_part_of_terms](queryIndex__model_activity_part_of_terms.md) - All direct biological process terms for all activities
 * [➞model_taxon](queryIndex__model_taxon.md) - The primary taxon term for the model, over the NCBITaxon:subClassOf relationship type. This is used to determine the primary taxon that the model is relevant to.
 * [➞model_taxon_closure](queryIndex__model_taxon_closure.md) - The reflexive transitive closure of the taxon term for the model, over the NCBITaxon:subClassOf relationship type. This is used to determine the set of taxa that are relevant to the model.
 * [➞model_taxon_rollup](queryIndex__model_taxon_rollup.md) - The rollup of the taxon closure to a NCBITaxon subset or slim.
 * [➞number_of_activities](queryIndex__number_of_activities.md) - The number of activities in a model.
 * [➞number_of_causal_associations](queryIndex__number_of_causal_associations.md) - Total number of causal association edges connecting activities in a model.
 * [➞number_of_enabled_by_terms](queryIndex__number_of_enabled_by_terms.md) - The number of molecular entities or sets of entities in a model.
 * [➞number_of_end_activities](queryIndex__number_of_end_activities.md) - The number of end activities in a model
 * [➞number_of_intermediate_activities](queryIndex__number_of_intermediate_activities.md) - The number of intermediate activities in a model
 * [➞number_of_singleton_activities](queryIndex__number_of_singleton_activities.md) - The number of singleton activities in a model
 * [➞number_of_start_activities](queryIndex__number_of_start_activities.md) - The number of start activities in a model
 * [➞number_of_strongly_connected_components](queryIndex__number_of_strongly_connected_components.md) - The number of distinct components that consist of activities that are connected (directly or indirectly) via causal connections. Most models will consist of a single SCC. Some models may consist of two or more "islands" where there is no connection from one island to another.
 * [➞singleton_activities](queryIndex__singleton_activities.md) - The set of activities that have no causal associations, i.e. those that are not connected to any other activity in the model.
 * [➞start_activities](queryIndex__start_activities.md) - The set of activities that are the starting points of the model, i.e. those that have no incoming causal associations.
 * [➞taxon_label](queryIndex__taxon_label.md) - The label of the primary taxon for the model
 * [term](term.md) - A generic slot for ontology terms
 * [➞term](termAssociation__term.md) - The ontology term that describes the nature of the association
     * [BiologicalProcessAssociation➞term](BiologicalProcessAssociation_term.md) - A generic slot for ontology terms
     * [CellTypeAssociation➞term](CellTypeAssociation_term.md) - A generic slot for ontology terms
     * [CellularAnatomicalEntityAssociation➞term](CellularAnatomicalEntityAssociation_term.md) - A generic slot for ontology terms
     * [GrossAnatomyAssociation➞term](GrossAnatomyAssociation_term.md) - A generic slot for ontology terms
     * [MolecularFunctionAssociation➞term](MolecularFunctionAssociation_term.md) - A generic slot for ontology terms
     * [MoleculeAssociation➞term](MoleculeAssociation_term.md) - A generic slot for ontology terms

### Enums

 * [CausalPredicateEnum](CausalPredicateEnum.md) - A term describing the causal relationship between two activities. All terms are drawn from the "causally upstream or within" (RO:0002418) branch of the Relation Ontology (RO).
 * [CellularAnatomicalEntityEnum](CellularAnatomicalEntityEnum.md) - A term from the subset of the cellular anatomical entity branch of GO CC
 * [EvidenceCodeEnum](EvidenceCodeEnum.md) - A term from the subset of ECO that maps up to a GAF evidence code
 * [InformationBiomacromoleculeCategory](InformationBiomacromoleculeCategory.md) - A term describing the type of the enabler of an activity.
 * [ModelStateEnum](ModelStateEnum.md) - A term describing where the model is in the development life cycle.
 * [PhaseEnum](PhaseEnum.md) - A term from either the phase branch of GO or the phase branch of an anatomy ontology

### Subsets


### Types


#### Built in

 * **Bool**
 * **Curie**
 * **Decimal**
 * **ElementIdentifier**
 * **NCName**
 * **NodeIdentifier**
 * **URI**
 * **URIorCURIE**
 * **XSDDate**
 * **XSDDateTime**
 * **XSDTime**
 * **float**
 * **int**
 * **str**

#### Defined

 * [Boolean](types/Boolean.md)  (**Bool**)  - A binary (true or false) value
 * [Curie](types/Curie.md)  (**Curie**)  - a compact URI
 * [Date](types/Date.md)  (**XSDDate**)  - a date (year, month and day) in an idealized calendar
 * [DateOrDatetime](types/DateOrDatetime.md)  (**str**)  - Either a date or a datetime
 * [Datetime](types/Datetime.md)  (**XSDDateTime**)  - The combination of a date and time
 * [Decimal](types/Decimal.md)  (**Decimal**)  - A real number with arbitrary precision that conforms to the xsd:decimal specification
 * [Double](types/Double.md)  (**float**)  - A real number that conforms to the xsd:double specification
 * [Float](types/Float.md)  (**float**)  - A real number that conforms to the xsd:float specification
 * [Integer](types/Integer.md)  (**int**)  - An integer
 * [Jsonpath](types/Jsonpath.md)  (**str**)  - A string encoding a JSON Path. The value of the string MUST conform to JSON Point syntax and SHOULD dereference to zero or more valid objects within the current instance document when encoded in tree form.
 * [Jsonpointer](types/Jsonpointer.md)  (**str**)  - A string encoding a JSON Pointer. The value of the string MUST conform to JSON Point syntax and SHOULD dereference to a valid object within the current instance document when encoded in tree form.
 * [Ncname](types/Ncname.md)  (**NCName**)  - Prefix part of CURIE
 * [Nodeidentifier](types/Nodeidentifier.md)  (**NodeIdentifier**)  - A URI, CURIE or BNODE that represents a node in a model.
 * [Objectidentifier](types/Objectidentifier.md)  (**ElementIdentifier**)  - A URI or CURIE that represents an object in the model.
 * [Sparqlpath](types/Sparqlpath.md)  (**str**)  - A string encoding a SPARQL Property Path. The value of the string MUST conform to SPARQL syntax and SHOULD dereference to zero or more valid objects within the current instance document when encoded as RDF.
 * [String](types/String.md)  (**str**)  - A character string
 * [Time](types/Time.md)  (**XSDTime**)  - A time object represents a (local) time of day, independent of any particular day
 * [Uri](types/Uri.md)  (**URI**)  - a complete URI
 * [Uriorcurie](types/Uriorcurie.md)  (**URIorCURIE**)  - a URI or a CURIE
