# Suchka-AI
目标数据结构
Movie
- faces
- poses
- objects
- image_features


# Data Source
机器学习的数据源通过自动爬去这些数据源，数据源的数据结构如下
所有图片都存放在同一个文件夹下, 所有图片都转换成 jpg 格式，分辨率以最小边长512pix缩放。
所有的描述信息存放在图片的metadata信息中
例如： md5(url).jpg

## 自定义标签：
- imageDescription: captions
- SKA_DESCRIPTION: image captions (text label)
- SKA_TAGS: csv tags
- SKA_CATEGORIES: csv category names

## Picture database
- https://www.pornpics.com/
- http://www.brutaltgp.com/fetish.html
- http://redfetishpost.com/
- https://nastypornpics.com/ (https://nastypornpics.com/search/mature/2/)
- https://bondagepictures.net/best/bdsm.html
- http://www.bondagescan.com/


## Crawler
```sh
scrapy crawler ./crawler/pornpics.py
```

# AI 学习
## 判断演员
判断视频所有关键帧，从中提取出人脸做特征提取。
然后把所有的人脸放在一个集合内做聚类，由这个逻辑判断主演的面部特征码
DeepFace 是一个比较好的统一类库

## 问题
### 男演员问题
通常男演员的面部特别特征特别稀疏，一个图集中只有很少的出境
等于要把所有图片集中的脸识别出来，按图集分类，比如图集中出现了3个独立的面孔
然后找出各个图集中的共同脸形成这个模特的最原始人脸信息

当已经形成了模特的人脸信息后，其他照片和这个信息做比对

## Visualizaion
pyvis

## 多标签分类任务
### 特征提取
特征提取用ResNet101

### 分类头
参考文章 https://zhuanlan.zhihu.com/p/107737824

### tensorflow GPU
```sh
source $CONDA_PREFIX/etc/conda/activate.d/env_vars.sh
```


### Useful checker
```js
// check if duplicate records, expect to be empty output
db.gallery.aggregate([ { $group: { _id: "$gid", count: { $sum: 1 } } }, { $match: { count: { $gt: 1 } } }]);
db.channel.aggregate([ { $group: { _id: "$name", count: { $sum: 1 } } }, { $match: { count: { $gt: 1 } } }]);
db.model.aggregate([ { $group: { _id: "$name", count: { $sum: 1 } } }, { $match: { count: { $gt: 1 } } }]);
db.tag.aggregate([ { $group: { _id: "$name", count: { $sum: 1 } } }, { $match: { count: { $gt: 1 } } }]);
db.face.aggregate([ { $group: { _id: {$concat:["$name","$source"]}, count: { $sum: 1 } } }, { $match: { count: { $gt: 1 } } }]);

// check data records for each collection
db.getCollectionNames().forEach((collectionName) => {
  const count = db.getCollection(collectionName).countDocuments();
  print(`Collection: ${collectionName}, Count: ${count}`);
});
```

```js
// find the most popular tags
db.tag.aggregate([{$project: {name: "$name" ,g_count: {$size: "$galleries"}}}, {$sort: {g_count:-1}}])
```

### backup database
```sh
docker exec -it mongo mongodump -d suchka-ai  -o /data/backup
docker cp mongo:/data/backup/suchka-ai /backup/suchka-ai/db
docker exec -it mongo rm -rf /data/backup/suchka-ai
(cd /backup/suchka-ai/db; tar czvf suchka-ai.tar.gz  ./suchka-ai; rm -rf ./suchka-ai)
```