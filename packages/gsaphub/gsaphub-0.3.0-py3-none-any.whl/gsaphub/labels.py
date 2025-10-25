from collections import defaultdict

ALLOWED_ENTITY_TYPES = {
    "Method",
    "DatasetGeneric",
    "MLModelGeneric",
    "ReferenceLink",
    "ModelArchitecture",
    "Task",
    "Dataset",
    "MLModel",
    "DataSource",
    "URL",
}

GSAP_INTENTION_MAPPING = {
    "IntentionCreation": "creation",
    "IntentionComparison": "comparison",
    "IntentionUsage": "usage",
}


GSAP_SUBTYPE_MAPPING = {
    "Method > misc": ["Method", "Misc"],
    "Method > ML techniques": ["Method", "MLTechnique"],
    "Method > libraries and tools": ["Method", "Tool"],
    "Method > ML paradigm": ["Method", "MLParadigm"],
    "Method > evaluation techniques": ["Method", "EvaluationTechnique"],
    "Method > data processing": ["Method", "DataPreprocessing"],
    "Method > data collection": ["Method", "DataCollection"],
    "ModelArchitecture>TraditionalMLTechnique": [
        "ModelArchitecture",
        "MLTraditionalTechnique",
    ],
    "ModelArchitecture>NNType": ["ModelArchitecture", "NeuralNetType"],
    "ModelArchitecture>Component": ["ModelArchitecture", "MLModelComponent"],
    "ModelArchitecture>MLModel": ["ModelArchitecture", "MLModel"],
}

GSAP_TYPES_WITH_SUBTYPES = defaultdict(set)
for label, label_sub in GSAP_SUBTYPE_MAPPING.values():
    GSAP_TYPES_WITH_SUBTYPES[label].add(label_sub)

RELATION_MAPPING = {
    ("Dataset", "isBasedOn", "Datasource"): "sourcedFrom",
    ("DatasetGeneric", "isBasedOn", "Datasource"): "sourcedFrom",
    # Data+ isBasedOn Method/MLModel+ : generatedWith
    ("Dataset", "isBasedOn", "Method"): "generatedBy",
    ("DatasetGeneric", "isBasedOn", "Method"): "generatedBy",
    ("Dataset", "isBasedOn", "MLModel"): "generatedBy",
    ("DatasetGeneric", "isBasedOn", "MLModel"): "generatedBy",
    ("Dataset", "isBasedOn", "MLModelGeneric"): "generatedBy",
    ("DatasetGeneric", "isBasedOn", "MLModelGeneric"): "generatedBy",
    # Data+ isBasedOn Data+
    ("Dataset", "isBasedOn", "Dataset"): "transformedFrom",
    ("Dataset", "isBasedOn", "DatasetGeneric"): "transformedFrom",
    ("DatasetGeneric", "isBasedOn", "Dataset"): "transformedFrom",
    ("DatasetGeneric", "isBasedOn", "DatasetGeneric"): "transformedFrom",
    # X hasArchitecture ModelArchitecture
    ("ModelArchitecture", "isBasedOn", "ModelArchitecture"): "architecture",
    ("MLModel", "isBasedOn", "ModelArchitecture"): "architecture",
    ("MLModelGeneric", "isBasedOn", "ModelArchitecture"): "architecture",
    ("Method", "isBasedOn", "ModelArchitecture"): "architecture",
    # Method/MLModel+ isBasedOn Method => usedFor
    ("Method", "isBasedOn", "Method"): "usedFor",
    ("MLModel", "isBasedOn", "Method"): "usedFor",
    ("MLModelGeneric", "isBasedOn", "Method"): "usedFor",
    ("ModelArchitecture", "isBasedOn", "Method"): "usedFor",  # ??? exist?
    # appliedOn
    # benchmarkFor
    ("Dataset", "appliedOn", "Task"): "benchmarkFor",
    ("DatasetGeneric", "appliedOn", "Task"): "benchmarkFor",
    # appliedTo
    ("MLModel", "appliedOn", "Task"): "appliedTo",
    ("MLModelGeneric", "appliedOn", "Task"): "appliedTo",
    ("Method", "appliedOn", "Task"): "appliedTo",
    ("ModelArchitecture", "appliedOn", "Task"): "appliedTo",  # ???
    # hasProcessed
    ("MLModel", "appliedOn", "Dataset"): "processed",
    ("MLModel", "appliedOn", "DatasetGeneric"): "processed",
    ("MLModelGeneric", "appliedOn", "Dataset"): "processed",
    ("MLModelGeneric", "appliedOn", "DatasetGeneric"): "processed",
    ("Method", "appliedOn", "Dataset"): "processed",
    ("Method", "appliedOn", "DatasetGeneric"): "processed",
    # Repair 2025-01 annotations
    ("Dataset", "derivedFrom", "Dataset"): "transformedFrom",  # 11,
}
"""
    ('MLModel', 'derivedFrom', 'MLModel'): 7,
         ('MLModel', 'usedFor', 'Method'): 854,
         ('ModelArchitecture', 'usedFor', 'Method'): 19}}

         ('ModelArchitecture', 'appliedOn', 'DatasetGeneric'): 6,

('Dataset', 'Unknown', 'DatasetGeneric'): 1,
         ('Dataset', 'isBasedOn', 'ReferenceLink'): 1,
		## Footnotes
         ('DatasetGeneric', 'hasFootnote', 'FootnoteLink'): 2,
         ('MLModelGeneric', 'hasFootnote', 'FootnoteLink'): 6,
         ('MLModel', 'hasFootnote', 'FootnoteLink'): 4,
         ('Method', 'hasFootnote', 'FootnoteLink'): 3,

         ('MLModelGeneric', 'Unknown', 'Task'): 2,

         ('MLModel', 'coreference', 'ModelArchitecture'): 1,
         ('MLModel', 'isComparedTo', 'ModelArchitecture'): 1,
         ('MLModelGeneric', 'isComparedTo', 'ModelArchitecture'): 1,
         ('MLModelGeneric', 'isBasedOn', 'Dataset'): 1,
         ('MLModelGeneric', 'isHyponymOf', 'MLModel'): 1,
         ('MLModelGeneric', 'usedFor', 'Method'): 4114,
         ('MLModelGeneric', 'versionOf', 'MLModel'): 1,
         ('Method', 'isBasedOn', 'Dataset'): 3,
         ('Method', 'isBasedOn', 'DatasetGeneric'): 3,
         ('Method', 'isBasedOn', 'MLModelGeneric'): 1,
         ('ModelArchitecture', 'coreference', 'MLModelGeneric'): 1,
         ('ModelArchitecture', 'evaluatedOn', 'DatasetGeneric'): 1,
"""

RELATION_INVERSE = ["usedFor"]

RELATION_LEFT_TO_RIGHT = ["coreference"]
RELATIONS_FREE_TEXT = {
    "usedFor": "is used for",
    "citation": "has reference",
    "evaluatedOn": "is evaluated on",
    "coreference": "is identical to",
    "architecture": "has architecture",
    "trainedOn": "is trained on",
    "isPartOf": "is part of",
    "isHyponymOf": "is a",
    "appliedTo": "is applied to",
    "transformedTo": "is transformed to",
    "isComparedTo": "is compared to",
    "generatedBy": "is generated by",
    "benchmarkFor": "is benchmarking",
    "isBasedOn": "is based on",
    "hasInstanceType": "has instances of type",
    "sourcedFrom": "is sourced From",
    "size": "has size",
    "url": "can be found at",
    "processed": "has processed",
    "versionOf": "isVersionOf",
}

ENTITY_MAPPING = {
    "Datasource": "DataSource",
}

SYMMETRIC_RELATIONS = ["coreference"]

ALLOWED_SIGNATURES = [
    # Attributive Relations
    # citation
    ["MLModel", "citation", "ReferenceLink"],
    ["ModelArchitecture", "citation", "ReferenceLink"],
    ["Task", "citation", "ReferenceLink"],
    ["MLModelGeneric", "citation", "ReferenceLink"],
    ["Method", "citation", "ReferenceLink"],
    ["Dataset", "citation", "ReferenceLink"],
    ["DatasetGeneric", "citation", "ReferenceLink"],
    ["DataSource", "citation", "ReferenceLink"],
    # url
    ["MLModelGeneric", "url", "URL"],
    ["Method", "url", "URL"],
    ["DatasetGeneric", "url", "URL"],
    ["MLModel", "url", "URL"],
    ["Dataset", "url", "URL"],
    ["DataSource", "url", "URL"],
    ["ModelArchitecture", "url", "URL"],
    #
    # Inner Entity Group Relations
    #
    # isHyponymOf
    # Model Like
    ["MLModelGeneric", "isHyponymOf", "MLModelGeneric"],
    ["MLModel", "isHyponymOf", "MLModelGeneric"],
    ["Method", "isHyponymOf", "Method"],
    ["ModelArchitecture", "isHyponymOf", "ModelArchitecture"],
    ["MLModelGeneric", "isHyponymOf", "ModelArchitecture"],
    ["MLModel", "isHyponymOf", "ModelArchitecture"],
    ["ModelArchitecture", "isHyponymOf", "MLModelGeneric"],
    ["Method", "isHyponymOf", "MLModelGeneric"],
    # Task
    ["Task", "isHyponymOf", "Task"],
    # Data Like
    ["DatasetGeneric", "isHyponymOf", "DatasetGeneric"],
    ["Dataset", "isHyponymOf", "DatasetGeneric"],
    ["DatasetGeneric", "isHyponymOf", "Dataset"],
    #
    # isPartOf
    # Model|Method Like
    ["MLModel", "isPartOf", "MLModelGeneric"],
    ["ModelArchitecture", "isPartOf", "MLModelGeneric"],
    ["MLModelGeneric", "isPartOf", "MLModelGeneric"],
    ["ModelArchitecture", "isPartOf", "ModelArchitecture"],
    ["MLModelGeneric", "isPartOf", "Method"],
    ["Method", "isPartOf", "Method"],
    # Task
    ["Task", "isPartOf", "Task"],
    # Data Like
    ["Dataset", "isPartOf", "DatasetGeneric"],
    ["DatasetGeneric", "isPartOf", "Dataset"],
    ["DatasetGeneric", "isPartOf", "DatasetGeneric"],
    ["Dataset", "isPartOf", "Dataset"],
    #
    # coreference
    # Model Like
    ["MLModelGeneric", "coreference", "MLModelGeneric"],
    ["MLModelGeneric", "coreference", "MLModel"],
    ["MLModel", "coreference", "MLModel"],
    ["MLModel", "coreference", "MLModelGeneric"],
    # Method Like
    ["Method", "coreference", "Method"],
    ["ModelArchitecture", "coreference", "ModelArchitecture"],
    # Task
    ["Task", "coreference", "Task"],
    # Data Like
    ["Dataset", "coreference", "Dataset"],
    ["Dataset", "coreference", "DatasetGeneric"],
    ["DatasetGeneric", "coreference", "Dataset"],
    ["DatasetGeneric", "coreference", "DatasetGeneric"],
    ["DataSource", "coreference", "DataSource"],
    #
    # isComparedTo
    # Model|Method Like
    ["MLModel", "isComparedTo", "MLModel"],
    ["MLModel", "isComparedTo", "MLModelGeneric"],
    ["MLModelGeneric", "isComparedTo", "MLModelGeneric"],
    ["MLModelGeneric", "isComparedTo", "MLModel"],
    ["Method", "isComparedTo", "Method"],
    ["Method", "isComparedTo", "MLModelGeneric"],
    ["Method", "isComparedTo", "MLModel"],
    ["MLModel", "isComparedTo", "Method"],
    ["MLModelGeneric", "isComparedTo", "Method"],
    ["ModelArchitecture", "isComparedTo", "ModelArchitecture"],
    ["ModelArchitecture", "isComparedTo", "MLModel"],
    # Task
    ["Task", "isComparedTo", "Task"],
    # Data Like
    ["DatasetGeneric", "isComparedTo", "DatasetGeneric"],
    ["Dataset", "isComparedTo", "Dataset"],
    ["DatasetGeneric", "isComparedTo", "Dataset"],
    ["Dataset", "isComparedTo", "DatasetGeneric"],
    #
    # versionOf
    # MLModel
    #["MLModel", "versionOf", "MLModel"],
    # Dataset
    #["Dataset", "versionOf", "Dataset"],
    #
    # isBasedOn
    # Model Like
    ["MLModel", "isBasedOn", "MLModel"],
    ["MLModel", "isBasedOn", "MLModelGeneric"],
    ["MLModelGeneric", "isBasedOn", "MLModelGeneric"],
    ["MLModelGeneric", "isBasedOn", "MLModel"],
    #
    # transformedFrom
    # Data Like
    ["DatasetGeneric", "transformedFrom", "DatasetGeneric"],
    ["DatasetGeneric", "transformedFrom", "Dataset"],
    ["Dataset", "transformedFrom", "DatasetGeneric"],
    ["Dataset", "transformedFrom", "Dataset"],
    #
    # size
    ["DatasetGeneric", "size", "DatasetGeneric"],
    ["Dataset", "size", "DatasetGeneric"],
    #
    # hasInstanceType
    # Data Like
    ["Dataset", "hasInstanceType", "DatasetGeneric"],
    ["DatasetGeneric", "hasInstanceType", "DatasetGeneric"],
    #
    # Inter Entity Group Relations
    # ============================
    #
    # --------------+
    # ==> Data Like |
    # --------------+
    #
    # Method|Model Like ==> Data Like
    # trainedOn
    #   ---------
    ["MLModelGeneric", "trainedOn", "DatasetGeneric"],
    ["MLModel", "trainedOn", "DatasetGeneric"],
    ["Method", "trainedOn", "DatasetGeneric"],
    ["MLModelGeneric", "trainedOn", "Dataset"],
    ["MLModel", "trainedOn", "Dataset"],
    ["Method", "trainedOn", "Dataset"],
    # evaluatedOn
    #   -----------
    ["MLModelGeneric", "evaluatedOn", "DatasetGeneric"],
    ["MLModel", "evaluatedOn", "DatasetGeneric"],
    ["MLModel", "evaluatedOn", "Dataset"],
    ["MLModelGeneric", "evaluatedOn", "Dataset"],
    ["Method", "evaluatedOn", "DatasetGeneric"],
    ["Method", "evaluatedOn", "Dataset"],
    # processed (former appliedOn)
    #   ---------
    #["Method", "processed", "DatasetGeneric"],
    #["Method", "processed", "Dataset"],
    #["MLModelGeneric", "processed", "DatasetGeneric"],
    #["MLModel", "processed", "DatasetGeneric"],
    #["MLModel", "processed", "Dataset"],
    #
    # ---------+
    # ==> Task |
    # ---------+
    #
    # Method|Model Like ==> Task
    # appliedTo
    #   ---------
    ["ModelArchitecture", "appliedTo", "Task"],
    ["MLModelGeneric", "appliedTo", "Task"],
    ["MLModel", "appliedTo", "Task"],
    ["Method", "appliedTo", "Task"],
    #
    # Data Like ==> Task
    # benchmarkFor
    #   ------------
    ["DatasetGeneric", "benchmarkFor", "Task"],
    ["Dataset", "benchmarkFor", "Task"],
    #
    # ----------------------+
    # ==> Model|Method Like |
    # ----------------------+
    #
    # Data Like ==> Method|Model Like
    # generatedBy (former basedOn)
    #   -----------
    ["DatasetGeneric", "generatedBy", "Method"],
    ["DatasetGeneric", "generatedBy", "MLModelGeneric"],
    ["DatasetGeneric", "generatedBy", "MLModel"],
    ["Dataset", "generatedBy", "Method"],
    ["Dataset", "generatedBy", "MLModelGeneric"],
    ["Dataset", "generatedBy", "MLModel"],
    #
    # Method ==> Model|Method Like
    # usedFor (former invers basedOn)
    #   -------
    ["Method", "usedFor", "MLModelGeneric"],
    ["Method", "usedFor", "MLModel"],
    ["Method", "usedFor", "Method"],
    ["Method", "usedFor", "ModelArchitecture"],
    #
    # Model|Method Like ==> ModelArchitecture
    # architecture
    #   ------------
    ["MLModelGeneric", "architecture", "ModelArchitecture"],
    ["MLModel", "architecture", "ModelArchitecture"],
    ["ModelArchitecture", "architecture", "ModelArchitecture"],
    ["Method", "architecture", "ModelArchitecture"],
    #
    # ---------------+
    # ==> DataSource +
    # ---------------+
    #
    # Data Like ==> DataSource
    # sourcedFrom
    #   -----------
    ["DatasetGeneric", "sourcedFrom", "DataSource"],
    ["Dataset", "sourcedFrom", "DataSource"],
]
ALLOWED_RELATION_TYPES = { relation_label for subject_type, relation_label, object_type in 
                          ALLOWED_SIGNATURES }

RELATION_GROUPS = {
        "Model Design":{"architecture", "usedFor", "isBasedOn"},
        "Task Binding":{"benchmarkFor", "appliedTo"},
        "Data Usage":{"evaluatedOn", "trainedOn"},  #, "processed"},
        "Data Provenance":{"generatedBy", "transformedFrom", "sourcedFrom"},
        "Data Properties":{"size", "hasInstanceType"},
        "Peer Relating":{
            "coreference",
            "isHyponymOf",
            "isPartOf",
            "isComparedTo",
            # "versionOf",
        },
        "Referencing":{"url", "citation"},
        "_average":{"weighted", "macro", "micro"},
        }

RELATION_LABEL_TO_GROUP = {
    l: g_label for g_label, g in RELATION_GROUPS.items() for l in g
}
