from app.services.redisvl.initindex import filechunkindex, filesummaryindex, webchunkindex, webchunkindex



CHUNK_INDEX_NAME = "idxpdf"
SUMMARY_INDEX_NAME = "idxsumm"
CACHE_INDEX_NAME = "idxcache"
WEBPAGE_SUMMARY_INDEX_NAME = "summidx"
WEB_CHUNK_INDEX_NAME = "idxweb"




def createindexes():
    for index in [filechunkindex, filesummaryindex, webchunkindex, webchunkindex]:
        index.create(overwrite=True)



