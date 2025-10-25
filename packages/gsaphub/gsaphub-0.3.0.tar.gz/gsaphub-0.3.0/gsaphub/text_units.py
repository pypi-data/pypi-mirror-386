def text_unit_as_string(text_unit):
    ents = text_unit["annotations"]
    rels = text_unit["relations"]
    text = text_unit["text"]
    text += "/t"
    text += relations_as_string(rels, ents, include_url=False)
    if "url_inception" in text_unit:
        text += f"\n\n{text_unit['url_inception']}"
    return text


def relations_as_string(relations, entities, include_url=True):
    string = []
    ents_dict = {e["id"]: e for e in entities}
    for rel in relations:
        subj = ents_dict.get(rel["subject_id"], {})
        obj = ents_dict.get(rel["object_id"], {})
        string.append(_relation_as_string(rel, subj, obj, include_url))
    return "\n\t".join(string)


def _relation_as_string(rel, subj, obj, include_url=True):
    ent = subj if subj else obj
    subs = f"[{subj.get('label', 'NIL')}: '{subj.get('text', '<no text>')}']"
    rel = f"({rel.get('relation_label', 'NIL')})"
    objs = f"[{obj.get('label', 'NIL')}: '{obj.get('text', '<no text>')}']"
    rel = f"{subs} - {rel} - {objs}"
    if ent and include_url:
        rel += f"\n\t{ent.get('url_inception')}"
    return rel
