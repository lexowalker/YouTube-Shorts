import json,sys,urllib.request,os
out=sys.argv[1]; acc=sys.argv[2]; ver=sys.argv[3] if len(sys.argv)>3 else "print"
H={"User-Agent":"tao-short-research/1.0"}
d=json.load(urllib.request.urlopen(urllib.request.Request("https://openaccess-api.clevelandart.org/api/artworks/"+acc,headers=H),timeout=60))["data"]
im=d["images"][ver]
fn=os.path.join(out,acc+"_"+ver+".jpg")
if not os.path.exists(fn):
    open(fn,"wb").write(urllib.request.urlopen(urllib.request.Request(im["url"],headers=H),timeout=600).read())
meta={"accession":acc,"title":d["title"],"creators":[c.get("description") for c in d.get("creators",[])],"date":d.get("creation_date"),
 "license":d.get("share_license_status"),"page":d.get("url"),"image_url":im["url"],"w":im["width"],"h":im["height"],"file":fn}
json.dump(meta,open(fn+".json","w"),indent=1); print(acc,ver,im["width"],im["height"],d["title"])
