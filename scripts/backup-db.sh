docker exec -it mongo mongodump -d suchka-ai  -o /data/backup
docker cp mongo:/data/backup/suchka-ai /backup/suchka-ai/db
docker exec -it mongo rm -rf /data/backup/suchka-ai
(cd /backup/suchka-ai/db; tar cvf suchka-ai.tar  ./suchka-ai; rm -rf ./suchka-ai;  du -h ./suchka-ai.tar)
(cd /backup/suchka-ai/db; rm ./suchka-ai.tar.gz; gzip -9 ./suchka-ai.tar;  du -h ./suchka-ai.tar.gz)
