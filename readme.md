# 运行方法
1. 在weibo下创建headers.json，写入请求头（需Cookie）
2. 在bili下创建headers.json，写入请求头（需Cookie）
3. 在run_crawler.py的bilibili_mids、bilibili_hot、weibo_uids和weibo_hot指定要爬取的内容与过滤
4. 运行preprocessing/preprocessing.ipynb完成数据预处理
5. 运行visualizer.py进行数据可视化