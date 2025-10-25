def ent_to_url(ent):
    info = ent["inception_meta"]
    if info.get("line_idx") is None:
        return
    info["annotator"] = ent["annotator"]
    return info_to_url(info)


def info_to_url(info):
    url_base = "https://multiweb.gesis.org/berd-nfdi/p/"
    url = (
        f"{url_base}{info['project_id']}/annotate"
        f"?3#!d={info['document_id']}&f={info['line_idx']}&u={info['annotator']}"
    )
    return url
