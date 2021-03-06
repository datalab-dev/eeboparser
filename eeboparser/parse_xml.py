import re
import xml.etree.ElementTree as ET

def inter_word_tags_preprocess(raw):
    """ remove tags occuring within a word using re """
    return(re.sub('<SUP>|</SUP>|<SEG>|<SEG [A-Z]*?=.*?">|</SEG>', "", raw))


def handle_gaps(root):
    for g in root.iter('GAP'):
        if g.get("EXTENT") == "1 letter" : g.text = "*"
        if g.get("EXTENT") == "2 letters" : g.text = "**"
    return(root)

def check_if_nested(node, parent_map):
    parent = parent_map[node]

    while parent.tag != "ETS":
        if parent.tag == "TEXT":
            return True
        parent = parent_map[parent]

    return False

def get_content(root):
    # get all nodes named TEXT (".//TEXT")
    textnodes = root.findall(".//TEXT")

    # construct parent map
    parent_map = {c:p for p in root.iter() for c in p}

    filtered = [n for n in textnodes if not check_if_nested(n, parent_map)]

    textslist = [" ".join(t.itertext()) for t in filtered]
    content = " ".join(textslist)

    # since they got needlessely delimited in " ".join(t.itertext()
    content = content.replace(" * ", "*")
    content = content.replace(" ** ", "**")

    # not removing non standard characters
    content = " ".join(content.split())
    content = content.replace("|", "")
    content = content.replace("∣", "") # this is a different character to the line above which is normal pipe |

    return(content)

def get_meta(root):
    """
   "File_ID", "STC_ID", "ESTC_ID", "EEBO_Citation",
   "Proquest_ID", "VID", "Title", "Location", "Publisher",
   "Author", "Keywords", "Date", "Language", 
   """

    name = None
    try: 
        name = root.find(".//IDNO[@TYPE='DLPS']").text
    except AttributeError:
        pass


    vid = None
    try: 
        vid = root.find(".//IDNO[@TYPE='vid']").text
    except AttributeError:
        pass

    eebo = None
    try: 
        eebo = root.find(".//IDNO[@TYPE='eebo citation']").text
    except AttributeError:
        pass

    proquest = None
    try: 
        proquest = root.find(".//IDNO[@TYPE='proquest']").text
    except AttributeError:
        pass

    stcs = root.findall(".//IDNO[@TYPE='stc']")
    estc = None
    stc = None
    if len(stcs) > 1: 
        stc = stcs[0].text
        estc = stcs[1].text
    elif len(stcs) == 1:
        stc = stcs[0].text

    title = (root.find("HEADER")
            .find("FILEDESC")
            .find("TITLESTMT")
            .find("TITLE").text)

    bib = (root.find("HEADER").
            find("FILEDESC").
            find("SOURCEDESC").
            find("BIBLFULL"))

    publisher = None
    try:
        location = bib.find(".//PUBLISHER").text
    except AttributeError:
        pass

    location = None
    try:
        location = bib.find(".//PUBPLACE").text
    except AttributeError:
        pass

    date = None
    try:
        date = bib.find(".//DATE").text
    except AttributeError:
        pass

    authors = []
    try:
        authorsxml = bib.find("TITLESTMT").iter("AUTHOR")
        for a in authorsxml:
            authors.append(a.text)
    except AttributeError:
        pass

    languages = []
    try:
        texts = root.find("EEBO").iter("TEXT")
        for t in texts:
            languages.append(t.get("LANG"))
    except AttributeError:
        pass

    kws = []
    try:
        terms = root.find("HEADER").find(".//KEYWORDS").iter("TERM")
        for t in terms:
            kws.append(t.text)
    except AttributeError:
        pass

    return({"File_ID": name,
            "VID": vid,
            "EEBO_Citation": eebo,
            "Proquest_ID": proquest,
            "STC_ID": stc,
            "ESTC_ID": estc,
            "Title": title,
            "Location": location,
            "Publisher": publisher,
            "Author": authors,
            "Keywords": kws,
            "Language": languages,
            "Date": date})

def parse_xml(_id, xmlstring):
    root = ET.fromstring (
                inter_word_tags_preprocess(xmlstring)
                )
    meta = get_meta(root)
    root = handle_gaps(root)
    content = get_content(root)

    meta["_id"] = _id
    text = {}
    text["_id"] = _id
    text["text"] = content
    truncated = {}
    truncated["_id"] = _id
    truncated["text"] = content[0:500]
    return(meta, text, truncated)
