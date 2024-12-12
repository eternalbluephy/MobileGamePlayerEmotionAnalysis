### 现在有三个方案
1. 直接使用python列表存储dict，然后mongodb直接insertMany
2. 每个信息使用json.dumps存入redis的list，然后使用redis.lrange分块，对于每一块中的每一个信息再使用json.loads加入python列表，使用mongodb的insertMany存储
3. 每个信息使用redis和哈希存储，然后使用for循环每次取出batch_size个加入python列表，然后使用mongodb的insertMany存入

此处使用 `方案2` 更好，因为其实每个信息的JSON格式并不复杂，小于lrange和for循环哈希取值的开销差距。