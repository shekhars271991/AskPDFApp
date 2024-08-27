from app.services.redisvl.initindex import filechunkindex, filesummaryindex, webchunkindex, websummaryindex



CHUNK_INDEX_NAME = "idxpdfchunk"
SUMMARY_INDEX_NAME = "idxpdfsumm"
CACHE_INDEX_NAME = "idxcache"
WEBPAGE_SUMMARY_INDEX_NAME = "idxwebsumm"
WEB_CHUNK_INDEX_NAME = "idxwebchunk"




def createindexes():
    for index in [filechunkindex, filesummaryindex, webchunkindex, websummaryindex]:
        try:
            index.create(overwrite=True)
        except Exception as e:
            print(f"Failed to create index {index}: {e}")




